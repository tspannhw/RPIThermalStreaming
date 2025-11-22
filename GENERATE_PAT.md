# Quick Guide: Generate Programmatic Access Token (PAT)

Based on [Snowflake's PAT Documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens).

## Simple Method (Default Settings)

```sql
-- Login to Snowflake as ACCOUNTADMIN or user with appropriate privileges
USE ROLE ACCOUNTADMIN;

-- Generate PAT with default 15-day expiration
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN;
```

**Copy the secret immediately!** It looks like: `ver:1-hint:123456789-EAAA...`

You'll see output like:
```
+-------------+-------------------------------+
| name        | value                         |
|-------------+-------------------------------|
| TOKEN_12345 | ver:1-hint:987654-EAAABBBCCC...|
+-------------+-------------------------------+
```

## Recommended Method (Named + Long Expiration)

```sql
-- Generate PAT named "thermal_pat" valid for 90 days
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN 
  NAME = 'thermal_pat'
  EXPIRES_IN = 90;
```

## Secure Method (Role Restriction)

```sql
-- Generate PAT that can ONLY use THERMAL_STREAMING_ROLE
ALTER USER THERMAL_STREAMING_USER 
  ADD PROGRAMMATIC ACCESS TOKEN 
  NAME = 'thermal_pat'
  ROLE_RESTRICTION = (THERMAL_STREAMING_ROLE)
  EXPIRES_IN = 90;
```

## Add to Configuration

Edit `snowflake_config.json`:

```json
{
  "user": "THERMAL_STREAMING_USER",
  "account": "SFSENORTHAMERICA-TSPANN-AWS1",
  "url": "https://SFSENORTHAMERICA-TSPANN-AWS1.snowflakecomputing.com:443",
  "pat": "ver:1-hint:987654-EAAABBBCCC...",
  "role": "THERMAL_STREAMING_ROLE",
  "database": "DEMO",
  "schema": "DEMO",
  "pipe": "THERMAL_SENSOR_PIPE",
  "channel_name": "thermal_channel_001"
}
```

**Important:** Remove or clear the `private_key_file` field!

## Test Connection

```bash
python test_connection.py
```

## Manage PATs

### List all PATs for a user
```sql
SHOW USER PROGRAMMATIC ACCESS TOKENS FOR USER THERMAL_STREAMING_USER;
```

### View expiration dates
```sql
DESC USER THERMAL_STREAMING_USER;
```

### Rotate PAT (generates new secret)
```sql
ALTER USER THERMAL_STREAMING_USER 
  ROTATE PROGRAMMATIC ACCESS TOKEN thermal_pat;
```

### Revoke PAT
```sql
ALTER USER THERMAL_STREAMING_USER 
  REMOVE PROGRAMMATIC ACCESS TOKEN thermal_pat;
```

## Troubleshooting

### Error: "User must be subject to a network policy"

Service users require a network policy. Either:

1. **Create a network policy:**
```sql
CREATE NETWORK POLICY my_network_policy
  ALLOWED_IP_LIST = ('0.0.0.0/0');  -- Adjust to your IP range

ALTER USER THERMAL_STREAMING_USER 
  SET NETWORK_POLICY = my_network_policy;
```

2. **Or bypass for human users (not recommended for service users):**
```sql
CREATE AUTHENTICATION POLICY bypass_network_policy
  PAT_POLICY=(NETWORK_POLICY_EVALUATION = ENFORCED_NOT_REQUIRED);

ALTER USER THERMAL_STREAMING_USER 
  SET AUTHENTICATION POLICY bypass_network_policy;
```

### Error: "Insufficient privileges"

You need the `MANAGE USER CREDENTIALS` privilege:

```sql
GRANT MANAGE USER CREDENTIALS ON USER THERMAL_STREAMING_USER TO ROLE ACCOUNTADMIN;
```

## Best Practices

1. ✅ Use role restrictions for security
2. ✅ Set appropriate expiration (30-90 days recommended)
3. ✅ Store PATs securely (never commit to git)
4. ✅ Rotate PATs regularly
5. ✅ Monitor PAT usage in `SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY`

## References

- [Snowflake PAT Documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- [ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN](https://docs.snowflake.com/en/sql-reference/sql/alter-user#programmatic-access-token-pat-operations)

