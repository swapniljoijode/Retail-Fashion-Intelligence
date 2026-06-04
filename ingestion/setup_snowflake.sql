-- =============================================================================
-- Snowflake Trial — Initial Object Setup
-- Run this ONCE as ACCOUNTADMIN before running snowflake_bronze.sql or dbt.
-- =============================================================================
-- Order matters:
--   1. Create warehouse, database
--   2. Grant SYSADMIN the objects
--   3. Register your RSA public key on your user
--   4. Verify connection (run as dbt user)
-- =============================================================================

-- ── Step 1: Create compute and storage objects ─────────────────────────────────
USE ROLE ACCOUNTADMIN;

-- XS warehouse: cheapest, enough for a single-user dev build.
-- AUTO_SUSPEND = 60 means it idles off after 60 s with no queries.
CREATE WAREHOUSE IF NOT EXISTS FASHION_WH
    WAREHOUSE_SIZE    = 'XSMALL'
    AUTO_SUSPEND      = 60
    AUTO_RESUME       = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Fashion Retail Intelligence — dev warehouse';

CREATE DATABASE IF NOT EXISTS FASHION_RETAIL
    COMMENT = 'Fashion Retail Intelligence Platform';

-- ── Step 2: Grant SYSADMIN access ──────────────────────────────────────────────
GRANT USAGE  ON WAREHOUSE FASHION_WH    TO ROLE SYSADMIN;
GRANT USAGE  ON DATABASE  FASHION_RETAIL TO ROLE SYSADMIN;
GRANT ALL    ON DATABASE  FASHION_RETAIL TO ROLE SYSADMIN;

-- Allow SYSADMIN to create schemas inside the database.
GRANT CREATE SCHEMA ON DATABASE FASHION_RETAIL TO ROLE SYSADMIN;

-- ── Step 3: Register RSA public key ────────────────────────────────────────────
-- After generating your key pair locally:
--   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt
--   openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub
--
-- Open snowflake_key.pub and copy the contents between the
-- -----BEGIN PUBLIC KEY----- and -----END PUBLIC KEY----- lines (no whitespace).
-- Paste it below and run as ACCOUNTADMIN.

ALTER USER <YOUR_USERNAME>
    SET RSA_PUBLIC_KEY = '<paste_public_key_contents_here>';

-- Verify the key was registered:
DESC USER <YOUR_USERNAME>;
-- Look for the RSA_PUBLIC_KEY_FP row — it should show a SHA256 fingerprint.

-- ── Step 4: Quick connection test ──────────────────────────────────────────────
-- Switch to SYSADMIN and verify the warehouse and database are accessible.
USE ROLE SYSADMIN;
USE WAREHOUSE FASHION_WH;
USE DATABASE FASHION_RETAIL;

SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();
-- Expected: SYSADMIN | FASHION_WH | FASHION_RETAIL

-- ── Done — proceed to snowflake_bronze.sql ────────────────────────────────────
