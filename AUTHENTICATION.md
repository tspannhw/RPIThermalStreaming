# Snowflake Authentication Options

This application supports two authentication methods. Choose the one that works best for you.

Based on [Snowflake's authentication documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens).

---

## 🎯 OPTION 1: Programmatic Access Token (PAT) - RECOMMENDED

**Pros:**
- ✅ Simpler setup (no key generation)
- ✅ Works immediately
- ✅ Easy to rotate tokens
- ✅ No public key registration needed
- ✅ Can set expiration time (1-365 days)

**Cons:**
- ⚠️ Tokens expire (must be regenerated periodically)
- ⚠️ May require network policy for service users

### Setup Steps

#### 1. Generate Programmatic Access Token (PAT)

**Method A: Using SQL (Recommended)**

```sql
USE ROLE ACCOUNTADMIN;

-- Generate a PAT with default 15-day expiration
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN;
```

The secret will be displayed in the `value` column. **Copy it immediately** - you cannot view it again!

**Method B: With Custom Name and Expiration**

```sql
-- Generate PAT named "thermal_pat" valid for 90 days
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN 
  NAME = 'thermal_pat'
  EXPIRES_IN = 90;
```

**Method C: Restrict to Specific Role**

```sql
-- Generate PAT that can only assume THERMAL_STREAMING_ROLE
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN 
  NAME = 'thermal_pat'
  ROLE_RESTRICTION = (THERMAL_STREAMING_ROLE)
  EXPIRES_IN = 90;
```

#### 2. Add PAT to Configuration

Edit `snowflake_config.json`:

```json
{
  "user": "THERMAL_STREAMING_USER",
  "account": "your_account_identifier",
  "url": "https://your_account_identifier.snowflakecomputing.com:443",
  "pat": "ver:1-hint:123456789-EAAABBBCCCdddEEEfffGGG...",
  "role": "THERMAL_STREAMING_ROLE",
  "database": "DEMO",
  "schema": "DEMO",
  "pipe": "THERMAL_SENSOR_PIPE",
  "channel_name": "thermal_channel_001"
}
```

#### 3. Test Connection

```bash
python test_connection.py
```

### Managing PATs

#### List Your PATs

```sql
SHOW USER PROGRAMMATIC ACCESS TOKENS FOR USER THERMAL_STREAMING_USER;
```

#### Rotate a PAT

```sql
-- Rotate (creates new secret, invalidates old one)
ALTER USER THERMAL_STREAMING_USER 
  ROTATE PROGRAMMATIC ACCESS TOKEN thermal_pat;
```

#### Revoke a PAT

```sql
-- Revoke permanently (cannot be recovered)
ALTER USER THERMAL_STREAMING_USER 
  REMOVE PROGRAMMATIC ACCESS TOKEN thermal_pat;
```

#### Check PAT Expiration

```sql
-- View expiration date
DESC USER THERMAL_STREAMING_USER;
```

### Best Practices for PATs

1. **Use role restrictions:** Limit PAT to specific roles for security
2. **Set appropriate expiration:** Balance security vs. operational overhead
3. **Store securely:** Use secret managers (AWS Secrets Manager, HashiCorp Vault)
4. **Rotate regularly:** Rotate PATs before expiration
5. **Monitor usage:** Check `SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY` for PAT usage

For more details, see [Snowflake PAT Documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens).

---

## 🔐 OPTION 2: JWT Key-Pair Authentication

**Pros:**
- ✅ Tokens never expire
- ✅ More secure (private key never transmitted)
- ✅ Good for long-running applications

**Cons:**
- ⚠️ More complex setup
- ⚠️ Requires key generation and management
- ⚠️ Public key must be registered in Snowflake

### Setup Steps

#### 1. Generate Key Pair

```bash
./generate_keys.sh
```

This creates:
- `rsa_key.p8` - Private key (keep secret!)
- `rsa_key.pub` - Public key

#### 2. Register Public Key in Snowflake

```bash
# Extract and format public key
python extract_public_key.py
```

Copy the SQL command and run it in Snowflake:

```sql
ALTER USER THERMAL_STREAMING_USER SET RSA_PUBLIC_KEY='<generated_key>';
```

Verify:

```sql
DESC USER THERMAL_STREAMING_USER;
-- Look for RSA_PUBLIC_KEY_FP
```

#### 3. Configure Application

Edit `snowflake_config.json`:

```json
{
  "user": "THERMAL_STREAMING_USER",
  "account": "your_account_identifier",
  "url": "https://your_account_identifier.snowflakecomputing.com:443",
  "private_key_file": "rsa_key.p8",
  "role": "THERMAL_STREAMING_ROLE",
  "database": "DEMO",
  "schema": "DEMO",
  "pipe": "THERMAL_SENSOR_PIPE",
  "channel_name": "thermal_channel_001"
}
```

#### 4. Test Connection

```bash
python test_connection.py
```

### Troubleshooting JWT Auth

If you get "JWT token is invalid":

1. **Verify fingerprint matches:**
   ```bash
   python debug_jwt.py
   ```

2. **Check public key is registered:**
   ```sql
   DESC USER THERMAL_STREAMING_USER;
   ```

3. **Ensure private/public keys match:**
   ```bash
   python verify_keypair.py
   ```

---

## 📊 Comparison

| Feature | PAT | JWT Key-Pair |
|---------|-----|--------------|
| Setup Complexity | ⭐ Simple | ⭐⭐⭐ Complex |
| Security | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Excellent |
| Expiration | Yes (1-365 days) | No |
| Rotation | Easy (SQL command) | Manual |
| Best For | Most use cases | High-security environments |

## 🎯 Recommendation

- **For most users:** Use **PAT** (Option 1) - simpler and sufficient for most scenarios
- **For high-security environments:** Use **JWT Key-Pair** (Option 2) with proper key management

---

## 🔄 Switching Between Methods

You can easily switch by modifying `snowflake_config.json`:

**To use PAT:**
```json
{
  "pat": "ver:1-hint:...",
  "private_key_file": ""
}
```

**To use JWT:**
```json
{
  "pat": "",
  "private_key_file": "rsa_key.p8"
}
```

The application automatically detects which method to use.

---

## 📚 References

- [Snowflake Programmatic Access Tokens](https://docs.snowflake.com/en/user-guide/authentication-programmatic-tokens)
- [Snowflake Key-Pair Authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Snowflake API Integrations](https://docs.snowflake.com/en/sql-reference/sql/create-api-integration-snowflake)

