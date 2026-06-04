# Snowflake Trial Build

This guide walks through the complete Snowflake trial build: account setup, key-pair auth, R2 external stage, bronze COPY INTO, and dbt silver + gold. All SQL and dbt code is already in the repo — this is purely the execution sequence.

## Pre-requisites

- Cloudflare R2 credentials configured (`.env` with `R2_*` vars set, Parquet uploaded via `make upload`)
- Python environment set up (`make setup`)
- Parquet data generated (`make seed`)

---

## Step 1 — Sign up for a Snowflake trial

Go to [snowflake.com](https://www.snowflake.com) → **Start for Free**.

- Choose any cloud provider (AWS us-east-1 is fine)
- Note your **account identifier** — it appears in the URL as `https://<org>-<account>.snowflakecomputing.com`
- The dbt-snowflake profile uses the format `<org>-<account>` (e.g. `myorg-myaccount`)

---

## Step 2 — Generate a key pair

Run from the project root:

```bash
# Generate RSA private key in PKCS8 format (no passphrase)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt

# Extract the public key
openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub
```

`snowflake_key.p8` is gitignored — never commit it.

---

## Step 3 — Initial Snowflake object setup

Open a Snowflake Worksheet and run [`ingestion/setup_snowflake.sql`](../ingestion/setup_snowflake.sql) step by step.

This script:
1. Creates `FASHION_WH` (XS, auto-suspends after 60 s)
2. Creates `FASHION_RETAIL` database
3. Grants SYSADMIN access to both
4. Registers your RSA public key on your user

Replace `<YOUR_USERNAME>` and `<paste_public_key_contents_here>` before running the `ALTER USER` statement.

```sql
-- Example — get the key contents with:
cat snowflake_key.pub | grep -v "BEGIN\|END" | tr -d '\n'
```

---

## Step 4 — Configure `.env`

Copy `.env.example` to `.env` and fill in the Snowflake section:

```bash
SNOWFLAKE_ACCOUNT=myorg-myaccount       # from your Snowflake URL
SNOWFLAKE_USER=your_username
SNOWFLAKE_DATABASE=FASHION_RETAIL
SNOWFLAKE_WAREHOUSE=FASHION_WH
SNOWFLAKE_ROLE=SYSADMIN
SNOWFLAKE_PRIVATE_KEY_PATH=./snowflake_key.p8
```

---

## Step 5 — Configure `dbt/profiles.yml`

Copy `dbt/profiles.yml.example` to `dbt/profiles.yml` (it's gitignored). The Snowflake target reads from env vars — no credentials in the file.

Verify dbt can connect:

```bash
cd dbt && uv run dbt debug --target snowflake --profiles-dir .
# All checks should show "OK"
```

---

## Step 6 — Upload Parquet to Cloudflare R2

If you haven't already:

```bash
make seed      # generate small-volume Parquet (seed=42, reproducible)
make upload    # upload to R2 bucket fashion-retail-raw/raw/
```

Verify in the Cloudflare dashboard that files appear under `raw/dim_date/`, `raw/fact_sales/`, etc.

---

## Step 7 — Load Snowflake bronze layer

Open a Snowflake Worksheet and run [`ingestion/snowflake_bronze.sql`](../ingestion/snowflake_bronze.sql).

The script does this in four steps:

1. **Creates an S3-compatible external stage** pointing at your R2 bucket — replace `<ACCOUNT_ID>`, `<ACCESS_KEY_ID>`, `<SECRET_ACCESS_KEY>` with your R2 token values
2. **Creates 11 bronze tables** in the `bronze` schema (schema-on-read, append-only, with `_source_file` and `_load_timestamp` lineage columns)
3. **COPY INTO** each table from the R2 stage (Parquet → Snowflake)
4. **Row-count validation** — compare bronze counts against expected values

Expected row counts at `small` volume:

| Table | ~Rows |
|---|---|
| dim_date | 366 |
| dim_product | ~500 |
| dim_store | ~100 |
| dim_customer | ~5,000 |
| dim_channel | 5 |
| dim_promotion | ~50 |
| fact_sales | ~200,000 |
| fact_inventory_snapshot | ~500,000 |
| fact_returns | ~20,000 |
| fact_web_events | ~150,000 |
| fact_markdown | ~50,000 |

If `LIST @fashion_r2_raw_stage` returns 0 files, the stage credentials or endpoint are wrong.

---

## Step 8 — Run dbt against Snowflake

```bash
# Install packages (only needed once or after packages.yml changes)
make dbt-deps

# Full build — run + test all models against Snowflake
make dbt-build-snowflake
```

This runs all 212 dbt tests against Snowflake. Expect ~3–5 minutes on an XS warehouse.

To target only the run or only the tests:

```bash
cd dbt && uv run dbt run  --target snowflake --profiles-dir .
cd dbt && uv run dbt test --target snowflake --profiles-dir .
```

---

## Step 9 — Generate and serve dbt docs

```bash
make dbt-docs-snowflake
```

This opens the dbt docs site at [http://localhost:8080](http://localhost:8080).

The lineage graph shows the full DAG: 11 source tables → 11 staging views → 2 intermediate ephemeral models → 11 gold tables. Each node shows column descriptions, tests, and data types from the Snowflake catalog.

!!! tip "Interview artifact"
    The dbt lineage graph is one of the strongest portfolio artifacts available — it proves you understand the full transformation chain, not just individual SQL files. Screenshot it and reference it in interviews.

---

## Step 10 — Verify gold layer

After `dbt build` succeeds, spot-check a few marts:

```sql
USE ROLE SYSADMIN;
USE DATABASE FASHION_RETAIL;
USE WAREHOUSE FASHION_WH;

-- Gold marts created in marts schema
SHOW TABLES IN SCHEMA marts;

-- Spot-check: SCD2 surrogate key resolution
SELECT
    resolved_pct,
    unresolved_count
FROM (
    SELECT
        ROUND(COUNT_IF(product_key != -1) * 100.0 / COUNT(*), 2) AS resolved_pct,
        COUNT_IF(product_key = -1) AS unresolved_count
    FROM marts.fct_sales
);
-- resolved_pct should be ~99%+

-- Revenue sanity check
SELECT SUM(gross_revenue), SUM(net_revenue), SUM(gross_margin)
FROM marts.fct_sales;
```

---

## Cleanup (after trial expires or when done)

The trial gives ~$400 in credits. To avoid accidental spend:

```sql
-- Suspend the warehouse when done (or let AUTO_SUSPEND handle it)
ALTER WAREHOUSE FASHION_WH SUSPEND;
```

When the trial expires, the DuckDB shadow keeps the project fully live — the dashboard, tests, and CI all run against DuckDB at zero cost.
