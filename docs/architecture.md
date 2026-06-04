# Architecture

## Medallion layers

```
Cloudflare R2 (raw Parquet)
        │
        ▼
  DuckDB bronze          ← append-only, schema-on-read, lineage columns
        │
        ▼ dbt staging
  silver (views)         ← dedup, cast, clean, standardize categoricals
        │
        ▼ dbt intermediate (ephemeral)
  SCD2 surrogate keys    ← product_key, customer_key for date-range joins
        │
        ▼ dbt marts
  gold (tables)          ← star schema, surrogate FK resolution, -1 sentinel
        │
        ▼ export_snapshot.py
  JSON snapshot          ← committed to repo → dashboard/public/data/
        │
        ▼
  Next.js / Vercel       ← reads files at build time, fully static
```

## Key decisions

### Zero-cost permanence

The Snowflake trial builds the enterprise-vocabulary layer (micro-partitions, stages, COPY INTO, clustering keys). DuckDB runs the identical dbt project locally and in CI, for free, indefinitely. The dashboard reads an exported JSON snapshot so it stays live after Snowflake expires.

### Static serving

`export_snapshot.py` queries the DuckDB gold marts and writes six aggregated JSON files to `dashboard/public/data/`. Next.js reads them with `readFileSync` at build time — no runtime database dependency, no serverless cold starts, no warehouse cost.

### SCD Type 2 resolution

`dim_product` (on `retail_price`) and `dim_customer` (on `customer_segment`) are Type-2 slowly changing dimensions. Fact tables store natural keys only. Intermediate ephemeral models expose `effective_date` / `expiry_date`. Gold facts resolve surrogate keys via date-range LEFT JOIN:

```sql
left join dim_product p
    on  s.product_id   = p.product_id
    and s.sale_date   >= p.effective_date
    and (s.sale_date  <= p.expiry_date or p.expiry_date is null)
```

Unresolved keys coalesce to `-1` (the "unknown member" sentinel).

### Dual-target dbt

A single `generate_schema_name` macro overrides dbt's default prefix behavior so `+schema: staging` resolves to schema `staging` (not `main_staging`) on both DuckDB and Snowflake. The models are identical; only `profiles.yml` changes.

### Airflow vs GitLab scheduled pipelines

Airflow runs locally in Docker for demonstration — always-on hosting is not free. GitHub Actions scheduled workflows (`scheduled.yml`) serve as the lightweight production-grade orchestration proof: they run the full pipeline weekly, generate the Elementary report, and upload a 30-day artifact.

## Repository layout

```
fashion-retail-intelligence/
  data_generation/      Python generators (Faker, NumPy, pandas, pyarrow)
  ingestion/            Bronze load + R2 upload + gold snapshot export
  dbt/                  dbt project: staging → intermediate → marts
    models/
      staging/          11 stg_bronze__*.sql + _sources.yml + _schema.yml
      intermediate/     2 int_*__scd2_surrogate.sql (ephemeral)
      marts/            11 dim_*/fct_* tables + _schema.yml (contracts)
    macros/             generate_schema_name.sql override
  orchestration/        Airflow DAG (fashion_retail_pipeline.py)
  dashboard/            Next.js 14 App Router + Recharts
    app/                5 domain pages (server components)
    components/         KpiCard, SideNav, chart wrappers (client components)
    public/data/        6 committed JSON snapshots
    lib/                data.ts (readFileSync), types.ts
  docker/               Dockerfiles + docker-compose.yml
  tests/                86 unit + 13 integration smoke tests
  .github/workflows/    ci.yml, scheduled.yml, docs.yml
  docs/                 MkDocs source (this site)
  Makefile              task runner
  pyproject.toml        uv-managed deps
```
