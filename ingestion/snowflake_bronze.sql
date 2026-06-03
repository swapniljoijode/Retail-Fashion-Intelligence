-- =============================================================================
-- Phase 3: Snowflake Bronze Layer — Stage, File Format, DDL, and COPY INTO
-- =============================================================================
-- Pre-requisites:
--   1. A Cloudflare R2 bucket named fashion-retail-raw with Parquet data uploaded
--      via ingestion/upload_r2.py (prefix = 'raw').
--   2. An R2 API token with Object Read permissions (Settings → R2 → Manage API tokens).
--   3. Snowflake trial account with ACCOUNTADMIN or SYSADMIN role.
--
-- Run order:
--   Step 1  — Create storage objects (stage, file format)
--   Step 2  — Create bronze schema and tables
--   Step 3  — Run COPY INTO for each table
--   Step 4  — Validate row counts
-- =============================================================================


-- =============================================================================
-- Step 1: Storage objects
-- =============================================================================

USE ROLE SYSADMIN;
USE DATABASE FASHION_RETAIL;          -- create with: CREATE DATABASE FASHION_RETAIL;
USE WAREHOUSE FASHION_WH;             -- create with: CREATE WAREHOUSE FASHION_WH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;

-- Cloudflare R2 S3-compatible external stage.
-- Replace <ACCOUNT_ID>, <ACCESS_KEY_ID>, and <SECRET_ACCESS_KEY> with the
-- values from your Cloudflare dashboard (R2 → Manage API tokens).
-- Never commit real credentials; store them in Snowflake secrets or CI vars.
CREATE STAGE IF NOT EXISTS fashion_r2_raw_stage
    URL           = 's3compat://fashion-retail-raw/raw/'
    ENDPOINT      = '<ACCOUNT_ID>.r2.cloudflarestorage.com'
    CREDENTIALS   = (
        AWS_KEY_ID     = '<ACCESS_KEY_ID>'
        AWS_SECRET_KEY = '<SECRET_ACCESS_KEY>'
    )
    COMMENT = 'Cloudflare R2 raw landing bucket — read-only for bronze ingestion';

-- Verify the stage can list files before proceeding.
LIST @fashion_r2_raw_stage;

CREATE FILE FORMAT IF NOT EXISTS bronze_parquet_fmt
    TYPE                 = PARQUET
    SNAPPY_COMPRESSION   = TRUE
    USE_VECTORIZED_SCANNER = TRUE
    COMMENT = 'Snappy-compressed Parquet produced by pyarrow in Phase 2';


-- =============================================================================
-- Step 2: Bronze schema and tables
-- =============================================================================
-- Bronze contract:
--   • Schema mirrors the source Parquet exactly — no casting, no cleaning.
--   • Type-drifted columns (units_sold, units_on_hand) are kept as VARCHAR
--     because the writer coerced them to all-string to preserve the dirtiness.
--   • Two lineage columns are added to every table:
--       _source_file  VARCHAR        — Parquet file path from metadata$filename
--       _load_timestamp TIMESTAMP_NTZ — UTC timestamp of the COPY INTO run
--   • APPEND-ONLY: never UPDATE or DELETE from bronze tables.

CREATE SCHEMA IF NOT EXISTS bronze;

-- ── dim_date ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.dim_date (
    date_key            INTEGER,
    date                DATE,
    day_of_week         INTEGER,
    day_name            VARCHAR,
    day_of_month        INTEGER,
    day_of_year         INTEGER,
    week_of_year        INTEGER,
    month_number        INTEGER,
    month_name          VARCHAR,
    quarter_number      INTEGER,
    year                INTEGER,
    retail_season       VARCHAR,
    calendar_season     VARCHAR,
    is_weekend          BOOLEAN,
    is_public_holiday   BOOLEAN,
    holiday_name        VARCHAR,
    trading_day_of_week INTEGER,
    _source_file        VARCHAR,
    _load_timestamp     TIMESTAMP_NTZ
);

-- ── dim_product ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.dim_product (
    product_key     INTEGER,
    product_id      VARCHAR,
    sku             VARCHAR,
    product_name    VARCHAR,
    category        VARCHAR,       -- intentional casing inconsistency injected by dirtiness module
    subcategory     VARCHAR,
    brand           VARCHAR,
    color           VARCHAR,       -- nullable: ~2 % nulled by dirtiness module
    size            VARCHAR,
    season          VARCHAR,
    cost_price      FLOAT,
    retail_price    FLOAT,
    margin_pct      FLOAT,
    is_current      BOOLEAN,
    effective_date  DATE,
    expiry_date     DATE,
    _source_file    VARCHAR,
    _load_timestamp TIMESTAMP_NTZ
);

-- ── dim_store ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.dim_store (
    store_key       INTEGER,
    store_id        VARCHAR,
    store_name      VARCHAR,
    region          VARCHAR,
    city            VARCHAR,
    country         VARCHAR,
    store_type      VARCHAR,
    square_footage  INTEGER,
    opening_date    DATE,
    _source_file    VARCHAR,
    _load_timestamp TIMESTAMP_NTZ
);

-- ── dim_customer ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.dim_customer (
    customer_key        INTEGER,
    customer_id         VARCHAR,
    customer_segment    VARCHAR,
    loyalty_tier        VARCHAR,
    region              VARCHAR,   -- nullable: ~5 % nulled by dirtiness module
    city                VARCHAR,   -- nullable: ~4 % nulled by dirtiness module
    acquisition_channel VARCHAR,
    first_purchase_date DATE,
    is_current          BOOLEAN,
    effective_date      DATE,
    expiry_date         DATE,
    _source_file        VARCHAR,
    _load_timestamp     TIMESTAMP_NTZ
);

-- ── dim_channel ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.dim_channel (
    channel_key     INTEGER,
    channel_id      VARCHAR,
    channel_name    VARCHAR,
    channel_type    VARCHAR,
    platform        VARCHAR,
    _source_file    VARCHAR,
    _load_timestamp TIMESTAMP_NTZ
);

-- ── dim_promotion ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.dim_promotion (
    promotion_key   INTEGER,
    promotion_id    VARCHAR,
    promotion_name  VARCHAR,
    promotion_type  VARCHAR,
    discount_pct    FLOAT,
    start_date      DATE,
    end_date        DATE,
    is_sitewide     BOOLEAN,
    _source_file    VARCHAR,
    _load_timestamp TIMESTAMP_NTZ
);

-- ── fact_sales ────────────────────────────────────────────────────────────────
-- units_sold is VARCHAR because the dirtiness module injected type-drift (int→str)
-- and the writer coerced the column to all-string to preserve the inconsistency.
-- The silver layer will CAST and validate this column.
CREATE TABLE IF NOT EXISTS bronze.fact_sales (
    sale_key          INTEGER,
    order_id          VARCHAR,
    order_line_id     VARCHAR,
    sale_date         DATE,
    product_id        VARCHAR,
    store_id          VARCHAR,
    customer_id       VARCHAR,
    channel_id        VARCHAR,
    promotion_id      VARCHAR,
    units_sold        VARCHAR,     -- type-drifted: ~3 % rows hold the value as a string
    unit_retail_price FLOAT,
    gross_revenue     FLOAT,
    discount_amount   FLOAT,
    net_revenue       FLOAT,
    unit_cost         FLOAT,
    cogs              FLOAT,
    gross_margin      FLOAT,
    _source_file      VARCHAR,
    _load_timestamp   TIMESTAMP_NTZ
);

-- ── fact_inventory_snapshot ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.fact_inventory_snapshot (
    inventory_key   INTEGER,
    snapshot_date   DATE,
    product_id      VARCHAR,
    store_id        VARCHAR,
    units_on_hand   VARCHAR,       -- type-drifted: ~2 % rows
    units_in_transit INTEGER,
    units_on_order  INTEGER,
    reorder_point   INTEGER,
    is_stockout     BOOLEAN,
    _source_file    VARCHAR,
    _load_timestamp TIMESTAMP_NTZ
);

-- ── fact_returns ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.fact_returns (
    return_key          INTEGER,
    return_id           VARCHAR,
    return_line_id      VARCHAR,
    original_order_id   VARCHAR,
    return_date         DATE,
    original_sale_date  DATE,
    product_id          VARCHAR,
    store_id            VARCHAR,
    customer_id         VARCHAR,
    channel_id          VARCHAR,
    units_returned      INTEGER,
    refund_value        FLOAT,
    return_reason       VARCHAR,
    _source_file        VARCHAR,
    _load_timestamp     TIMESTAMP_NTZ
);

-- ── fact_web_events ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.fact_web_events (
    event_key                INTEGER,
    session_id               VARCHAR,
    event_date               DATE,
    customer_id              VARCHAR,   -- nullable: ~30 % anonymous sessions
    channel_id               VARCHAR,
    device_type              VARCHAR,
    session_duration_seconds INTEGER,
    product_id               VARCHAR,   -- nullable: only set when product was viewed
    event_type               VARCHAR,
    _source_file             VARCHAR,
    _load_timestamp          TIMESTAMP_NTZ
);

-- ── fact_markdown ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.fact_markdown (
    markdown_key            INTEGER,
    week_start_date         DATE,
    product_id              VARCHAR,
    store_id                VARCHAR,
    regular_price           FLOAT,
    markdown_price          FLOAT,
    markdown_depth_pct      FLOAT,
    units_sold_on_markdown  INTEGER,
    revenue_on_markdown     FLOAT,
    _source_file            VARCHAR,
    _load_timestamp         TIMESTAMP_NTZ
);


-- =============================================================================
-- Step 3: COPY INTO
-- =============================================================================
-- Pattern: SELECT source columns from the Parquet stage variant, append
-- metadata$filename and CURRENT_TIMESTAMP() as lineage columns.
-- ON_ERROR = SKIP_FILE skips corrupt files without aborting the entire load —
-- log any skipped files in the COPY history for investigation.
--
-- Run each block independently so a failure in one table doesn't block others.

COPY INTO bronze.dim_date
FROM (
    SELECT
        $1:date_key::INTEGER,
        $1:date::DATE,
        $1:day_of_week::INTEGER,
        $1:day_name::VARCHAR,
        $1:day_of_month::INTEGER,
        $1:day_of_year::INTEGER,
        $1:week_of_year::INTEGER,
        $1:month_number::INTEGER,
        $1:month_name::VARCHAR,
        $1:quarter_number::INTEGER,
        $1:year::INTEGER,
        $1:retail_season::VARCHAR,
        $1:calendar_season::VARCHAR,
        $1:is_weekend::BOOLEAN,
        $1:is_public_holiday::BOOLEAN,
        $1:holiday_name::VARCHAR,
        $1:trading_day_of_week::INTEGER,
        metadata$filename::VARCHAR  AS _source_file,
        CURRENT_TIMESTAMP()         AS _load_timestamp
    FROM @fashion_r2_raw_stage/dim_date/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.dim_product
FROM (
    SELECT
        $1:product_key::INTEGER,
        $1:product_id::VARCHAR,
        $1:sku::VARCHAR,
        $1:product_name::VARCHAR,
        $1:category::VARCHAR,
        $1:subcategory::VARCHAR,
        $1:brand::VARCHAR,
        $1:color::VARCHAR,
        $1:size::VARCHAR,
        $1:season::VARCHAR,
        $1:cost_price::FLOAT,
        $1:retail_price::FLOAT,
        $1:margin_pct::FLOAT,
        $1:is_current::BOOLEAN,
        $1:effective_date::DATE,
        $1:expiry_date::DATE,
        metadata$filename::VARCHAR  AS _source_file,
        CURRENT_TIMESTAMP()         AS _load_timestamp
    FROM @fashion_r2_raw_stage/dim_product/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.dim_store
FROM (
    SELECT
        $1:store_key::INTEGER,
        $1:store_id::VARCHAR,
        $1:store_name::VARCHAR,
        $1:region::VARCHAR,
        $1:city::VARCHAR,
        $1:country::VARCHAR,
        $1:store_type::VARCHAR,
        $1:square_footage::INTEGER,
        $1:opening_date::DATE,
        metadata$filename::VARCHAR  AS _source_file,
        CURRENT_TIMESTAMP()         AS _load_timestamp
    FROM @fashion_r2_raw_stage/dim_store/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.dim_customer
FROM (
    SELECT
        $1:customer_key::INTEGER,
        $1:customer_id::VARCHAR,
        $1:customer_segment::VARCHAR,
        $1:loyalty_tier::VARCHAR,
        $1:region::VARCHAR,
        $1:city::VARCHAR,
        $1:acquisition_channel::VARCHAR,
        $1:first_purchase_date::DATE,
        $1:is_current::BOOLEAN,
        $1:effective_date::DATE,
        $1:expiry_date::DATE,
        metadata$filename::VARCHAR  AS _source_file,
        CURRENT_TIMESTAMP()         AS _load_timestamp
    FROM @fashion_r2_raw_stage/dim_customer/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.dim_channel
FROM (
    SELECT
        $1:channel_key::INTEGER,
        $1:channel_id::VARCHAR,
        $1:channel_name::VARCHAR,
        $1:channel_type::VARCHAR,
        $1:platform::VARCHAR,
        metadata$filename::VARCHAR  AS _source_file,
        CURRENT_TIMESTAMP()         AS _load_timestamp
    FROM @fashion_r2_raw_stage/dim_channel/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.dim_promotion
FROM (
    SELECT
        $1:promotion_key::INTEGER,
        $1:promotion_id::VARCHAR,
        $1:promotion_name::VARCHAR,
        $1:promotion_type::VARCHAR,
        $1:discount_pct::FLOAT,
        $1:start_date::DATE,
        $1:end_date::DATE,
        $1:is_sitewide::BOOLEAN,
        metadata$filename::VARCHAR  AS _source_file,
        CURRENT_TIMESTAMP()         AS _load_timestamp
    FROM @fashion_r2_raw_stage/dim_promotion/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.fact_sales
FROM (
    SELECT
        $1:sale_key::INTEGER,
        $1:order_id::VARCHAR,
        $1:order_line_id::VARCHAR,
        $1:sale_date::DATE,
        $1:product_id::VARCHAR,
        $1:store_id::VARCHAR,
        $1:customer_id::VARCHAR,
        $1:channel_id::VARCHAR,
        $1:promotion_id::VARCHAR,
        $1:units_sold::VARCHAR,         -- type-drifted; silver layer will CAST
        $1:unit_retail_price::FLOAT,
        $1:gross_revenue::FLOAT,
        $1:discount_amount::FLOAT,
        $1:net_revenue::FLOAT,
        $1:unit_cost::FLOAT,
        $1:cogs::FLOAT,
        $1:gross_margin::FLOAT,
        metadata$filename::VARCHAR      AS _source_file,
        CURRENT_TIMESTAMP()             AS _load_timestamp
    FROM @fashion_r2_raw_stage/fact_sales/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.fact_inventory_snapshot
FROM (
    SELECT
        $1:inventory_key::INTEGER,
        $1:snapshot_date::DATE,
        $1:product_id::VARCHAR,
        $1:store_id::VARCHAR,
        $1:units_on_hand::VARCHAR,      -- type-drifted; silver layer will CAST
        $1:units_in_transit::INTEGER,
        $1:units_on_order::INTEGER,
        $1:reorder_point::INTEGER,
        $1:is_stockout::BOOLEAN,
        metadata$filename::VARCHAR      AS _source_file,
        CURRENT_TIMESTAMP()             AS _load_timestamp
    FROM @fashion_r2_raw_stage/fact_inventory_snapshot/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.fact_returns
FROM (
    SELECT
        $1:return_key::INTEGER,
        $1:return_id::VARCHAR,
        $1:return_line_id::VARCHAR,
        $1:original_order_id::VARCHAR,
        $1:return_date::DATE,
        $1:original_sale_date::DATE,
        $1:product_id::VARCHAR,
        $1:store_id::VARCHAR,
        $1:customer_id::VARCHAR,
        $1:channel_id::VARCHAR,
        $1:units_returned::INTEGER,
        $1:refund_value::FLOAT,
        $1:return_reason::VARCHAR,
        metadata$filename::VARCHAR      AS _source_file,
        CURRENT_TIMESTAMP()             AS _load_timestamp
    FROM @fashion_r2_raw_stage/fact_returns/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.fact_web_events
FROM (
    SELECT
        $1:event_key::INTEGER,
        $1:session_id::VARCHAR,
        $1:event_date::DATE,
        $1:customer_id::VARCHAR,
        $1:channel_id::VARCHAR,
        $1:device_type::VARCHAR,
        $1:session_duration_seconds::INTEGER,
        $1:product_id::VARCHAR,
        $1:event_type::VARCHAR,
        metadata$filename::VARCHAR      AS _source_file,
        CURRENT_TIMESTAMP()             AS _load_timestamp
    FROM @fashion_r2_raw_stage/fact_web_events/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;

COPY INTO bronze.fact_markdown
FROM (
    SELECT
        $1:markdown_key::INTEGER,
        $1:week_start_date::DATE,
        $1:product_id::VARCHAR,
        $1:store_id::VARCHAR,
        $1:regular_price::FLOAT,
        $1:markdown_price::FLOAT,
        $1:markdown_depth_pct::FLOAT,
        $1:units_sold_on_markdown::INTEGER,
        $1:revenue_on_markdown::FLOAT,
        metadata$filename::VARCHAR      AS _source_file,
        CURRENT_TIMESTAMP()             AS _load_timestamp
    FROM @fashion_r2_raw_stage/fact_markdown/
)
FILE_FORMAT = (FORMAT_NAME = bronze_parquet_fmt)
ON_ERROR = SKIP_FILE;


-- =============================================================================
-- Step 4: Row-count validation
-- =============================================================================
-- Compare each bronze table count against the source file count via the stage.
-- Counts should match unless ON_ERROR = SKIP_FILE dropped corrupt files.

SELECT 'dim_date'               AS table_name, COUNT(*) AS bronze_rows FROM bronze.dim_date               UNION ALL
SELECT 'dim_product'            AS table_name, COUNT(*) AS bronze_rows FROM bronze.dim_product             UNION ALL
SELECT 'dim_store'              AS table_name, COUNT(*) AS bronze_rows FROM bronze.dim_store               UNION ALL
SELECT 'dim_customer'           AS table_name, COUNT(*) AS bronze_rows FROM bronze.dim_customer            UNION ALL
SELECT 'dim_channel'            AS table_name, COUNT(*) AS bronze_rows FROM bronze.dim_channel             UNION ALL
SELECT 'dim_promotion'          AS table_name, COUNT(*) AS bronze_rows FROM bronze.dim_promotion           UNION ALL
SELECT 'fact_sales'             AS table_name, COUNT(*) AS bronze_rows FROM bronze.fact_sales              UNION ALL
SELECT 'fact_inventory_snapshot'AS table_name, COUNT(*) AS bronze_rows FROM bronze.fact_inventory_snapshot UNION ALL
SELECT 'fact_returns'           AS table_name, COUNT(*) AS bronze_rows FROM bronze.fact_returns            UNION ALL
SELECT 'fact_web_events'        AS table_name, COUNT(*) AS bronze_rows FROM bronze.fact_web_events         UNION ALL
SELECT 'fact_markdown'          AS table_name, COUNT(*) AS bronze_rows FROM bronze.fact_markdown
ORDER BY table_name;

-- Inspect the COPY history for any skipped files or errors:
SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME   => 'FACT_SALES',
    START_TIME   => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
