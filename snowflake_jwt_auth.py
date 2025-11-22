#!/usr/bin/env python3
"""
Snowflake Authentication Module

Supports two authentication methods:
1. JWT Key-Pair Authentication (more complex, requires key generation)
2. Programmatic Access Token (simpler, generate in Snowflake UI)

Based on Snowflake's authentication documentation:
- JWT: https://docs.snowflake.com/en/developer-guide/sql-api/guide#using-key-pair-authentication
- Token: https://docs.snowflake.com/en/user-guide/authentication-programmatic-tokens
"""

import jwt
import time
import logging
import requests
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SnowflakeJWTAuth:
    """Handles authentication for Snowflake (JWT or Access Token)."""
    
    def __init__(self, config: Dict):
        """
        Initialize authentication.
        
        Supports two methods:
        1. JWT (requires private_key_file in config)
        2. Access Token (requires access_token in config)
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.account = config['account'].upper()
        self.user = config['user'].upper()
        
        # Check which authentication method to use
        if 'pat' in config and config['pat']:
            # Use Programmatic Access Token (PAT) - simpler method
            self.auth_method = 'pat'
            self.pat = config['pat']
            logger.info(f"PAT authentication initialized for user: {self.user}")
        elif 'private_key_file' in config and config['private_key_file']:
            # Use JWT key-pair authentication
            self.auth_method = 'jwt'
            self.private_key = self._load_private_key()
            self.qualified_username = f"{self.account}.{self.user}"
            logger.info(f"JWT auth initialized for user: {self.qualified_username}")
        else:
            raise ValueError(
                "No authentication method configured. "
                "Provide either 'pat' (Programmatic Access Token) or 'private_key_file' in config."
            )
    
    def _load_private_key(self):
        """Load private key from PEM file."""
        private_key_file = self.config['private_key_file']
        
        try:
            with open(private_key_file, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,  # Assumes unencrypted key
                    backend=default_backend()
                )
            
            logger.info(f"Private key loaded from {private_key_file}")
            return private_key
            
        except FileNotFoundError:
            logger.error(f"Private key file not found: {private_key_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            raise
    
    def generate_jwt_token(self) -> str:
        """
        Generate a JWT token for Snowflake authentication.
        
        Returns:
            Signed JWT token string
        """
        # Get public key fingerprint (SHA256 hash)
        public_key_bytes = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Calculate SHA256 fingerprint (uppercase hex)
        from hashlib import sha256
        public_key_fp = 'SHA256:' + sha256(public_key_bytes).hexdigest().upper()
        
        # Create JWT payload
        # Use epoch timestamps (seconds since Unix epoch)
        now = datetime.now(timezone.utc)
        iat = int(now.timestamp())
        exp = int((now + timedelta(hours=1)).timestamp())
        
        payload = {
            'iss': f"{self.qualified_username}.{public_key_fp}",
            'sub': self.qualified_username,
            'iat': iat,
            'exp': exp
        }
        
        logger.debug(f"JWT payload - iss: {payload['iss'][:50]}...")
        logger.debug(f"JWT payload - sub: {payload['sub']}")
        
        # Sign the JWT
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm='RS256'
        )
        
        logger.debug("JWT token generated")
        return token
    
    def get_scoped_token(self) -> str:
        """
        Get authentication token.
        
        Returns either:
        1. The Programmatic Access Token (PAT) if using PAT auth
        2. OAuth token from JWT exchange (if using JWT auth)
        
        Returns:
            Authentication token string
        """
        if self.auth_method == 'pat':
            # Simple: just return the PAT
            logger.info("Using Programmatic Access Token (PAT)")
            return self.pat
        
        elif self.auth_method == 'jwt':
            # Complex: exchange JWT for OAuth token
            return self._get_jwt_oauth_token()
        
        else:
            raise ValueError(f"Unknown auth method: {self.auth_method}")
    
    def _get_jwt_oauth_token(self) -> str:
        """
        Exchange JWT for a scoped token using Snowflake's OAuth endpoint.
        
        Returns:
            Scoped access token string
        """
        logger.info("Exchanging JWT for OAuth token...")
        
        jwt_token = self.generate_jwt_token()
        
        # Construct OAuth token URL (account should be lowercase in URL)
        account = self.config['account'].lower()
        token_url = f"https://{account}.snowflakecomputing.com/oauth/token"
        
        logger.debug(f"Token URL: {token_url}")
        
        # Prepare request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Get role (uppercase)
        role = self.config.get('role', 'PUBLIC').upper()
        
        data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': jwt_token,
            'scope': f'session:role:{role}'
        }
        
        logger.debug(f"Requesting token with role: {role}")
        
        try:
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                raise ValueError("No access_token in response")
            
            logger.info("OAuth token obtained successfully")
            return access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get OAuth token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            
            # Add helpful troubleshooting info
            logger.error("\nTroubleshooting JWT Auth:")
            logger.error("1. Verify the public key is registered in Snowflake:")
            logger.error(f"   ALTER USER {self.user} SET RSA_PUBLIC_KEY='<your_key>';")
            logger.error("2. Ensure the private key matches the registered public key")
            logger.error(f"3. Check the user exists: {self.user}")
            logger.error(f"4. Verify account identifier: {self.account}")
            logger.error("\nOR switch to Programmatic Access Token (PAT):")
            logger.error("   Add 'pat' to your snowflake_config.json")
            
            raise


def main():
    """Test JWT authentication."""
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        with open('snowflake_config.json', 'r') as f:
            config = json.load(f)
        
        auth = SnowflakeJWTAuth(config)
        token = auth.get_scoped_token()
        
        print(f"Successfully obtained token (length: {len(token)})")
        print(f"Token prefix: {token[:50]}...")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == '__main__':
    main()

