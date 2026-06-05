# Fashion Retail Intelligence Platform

[![CI](https://github.com/swapniljoijode/Retail-Fashion-Intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/swapniljoijode/Retail-Fashion-Intelligence/actions/workflows/ci.yml)
[![Scheduled Pipeline](https://github.com/swapniljoijode/Retail-Fashion-Intelligence/actions/workflows/scheduled.yml/badge.svg)](https://github.com/swapniljoijode/Retail-Fashion-Intelligence/actions/workflows/scheduled.yml)

An end-to-end data engineering platform for a fashion retailer — built to demonstrate the full enterprise data stack from raw generation to a live public dashboard, at **zero cost, permanently**.

**[Live Dashboard →](https://retail-fashion-intelligence.vercel.app)** &nbsp;|&nbsp; **[Documentation →](https://swapniljoijode.github.io/Retail-Fashion-Intelligence/)** &nbsp;|&nbsp; **[dbt Lineage Graph →](https://swapniljoijode.github.io/Retail-Fashion-Intelligence/dbt-docs/)**

---

## Architecture

```
Synthetic Parquet (Python)
        │
        ▼
Cloudflare R2           ← raw landing, zero egress, permanent free tier
        │
        ▼
Bronze layer            ← append-only, schema-on-read, lineage metadata
  DuckDB (free)         ← permanent shadow warehouse
  Snowflake (trial)     ← enterprise vocabulary: stages, COPY INTO, micro-partitions
        │
        ▼ dbt
Silver (staging views)  ← dedup, cast, clean, standardise
        │
        ▼ dbt
Gold (mart tables)      ← star schema, SCD2 surrogate keys, 190 tests
        │
        ▼
JSON snapshot           ← exported to dashboard/public/data/, committed to repo
        │
        ▼
Next.js / Vercel        ← five domain views, fully static, always live
```

The dashboard reads a static JSON snapshot — it **never depends on the warehouse being alive**, so it survives the Snowflake trial expiry.

---

## Five Domain Views

| Domain | Business question |
|---|---|
| **Sales** | Where is revenue moving and which channels and categories drive it? |
| **Marketing** | Which channels and devices convert, and what is driving returns? |
| **Category** | Which categories earn their floor space and where is markdown deepest? |
| **Product Planning** | What to replenish, what to hold, where is stockout risk highest? |
| **Placement** | Which regions are under-stocked relative to their revenue contribution? |

---

## Tech Stack

| Layer | Tool | Free status |
|---|---|---|
| Generation | Python — Faker, NumPy, pandas, pyarrow | Open source |
| Raw storage | Cloudflare R2 | Free forever (10 GB, zero egress) |
| Warehouse | Snowflake | 30-day trial |
| Warehouse shadow | DuckDB | Free forever |
| Transform | dbt-core + dbt-duckdb + dbt-snowflake + dbt-expectations | Open source |
| Observability | Elementary | Open source |
| Orchestration | Airflow + astronomer-cosmos | Free, local Docker |
| Containers | Docker + Docker Compose | Free |
| CI/CD | GitHub Actions | Free tier |
| Dashboard | Next.js 14 + Recharts | Open source |
| Hosting | Vercel Hobby | Free |
| Docs | MkDocs Material + GitHub Pages | Free |
| Env / deps | uv | Open source |

---

## Key Numbers

| Metric | Value |
|---|---|
| dbt models | 11 staging + 2 intermediate + 11 gold = **24** |
| dbt tests | **190** (not_null, unique, relationships, accepted_values, dbt-expectations) |
| Test pass rate | **100%** on both DuckDB and Snowflake |
| Synthetic rows | ~1M (small volume) — fact_sales, inventory, web events, returns, markdown |
| CI jobs | lint → unit tests ‖ integration smoke → docker build |
| Warehouse targets | DuckDB (permanent) + Snowflake Enterprise (trial) |

---

## Quick Start

```bash
git clone https://github.com/swapniljoijode/Retail-Fashion-Intelligence.git
cd Retail-Fashion-Intelligence

make setup          # create venv, install all deps, install pre-commit hooks
make seed           # generate small-volume synthetic Parquet (seed=42)
make bronze         # load DuckDB bronze layer
make dbt-build      # dbt deps + run + test against DuckDB
make test           # run 86 unit tests
make test-all       # run 86 unit + 13 integration smoke tests (99 total)
```

To run the dashboard locally:
```bash
make export-snapshot    # export DuckDB gold marts → dashboard/public/data/*.json
make dashboard-install  # npm install inside dashboard/
make dashboard-dev      # Next.js dev server on http://localhost:3000
```

---

## Repository Layout

```
fashion-retail-intelligence/
  data_generation/      Python generators — Faker, NumPy, pandas, pyarrow
  ingestion/            Bronze load, R2 upload, Snowflake bronze SQL, snapshot export
  dbt/                  dbt project: staging → intermediate (ephemeral) → marts
  orchestration/        Airflow DAG with astronomer-cosmos dbt task group
  dashboard/            Next.js 14 App Router + Recharts
  docker/               Dockerfiles and Docker Compose
  docs/                 MkDocs source (architecture, theory companion, metric dictionary)
  tests/                pytest — unit + integration smoke
  .github/workflows/    ci.yml, scheduled.yml, docs.yml
  Makefile              task runner
  pyproject.toml        uv-managed Python deps
```

---

## Data Model

Star schema — five fact tables feeding five business domain marts.

**Dimensions:** `dim_product` (SCD2 on price), `dim_store`, `dim_customer` (SCD2 on segment), `dim_date`, `dim_channel`, `dim_promotion`

**Facts:** `fct_sales`, `fct_inventory_snapshot`, `fct_returns`, `fct_web_events`, `fct_markdown`

Surrogate key resolution uses date-range JOINs for SCD2 dimensions. Unresolved keys coalesce to `-1` (unknown member sentinel). See the [metric dictionary](docs/metric_dictionary.md) for all KPI definitions and formulas.

---

## CI / CD

Every push to `main` triggers:

```
lint (ruff + black + sqlfluff)
    ├── test-unit     (pytest, no integration)
    └── test-integration  (generate → bronze → dbt build → gold assertions)
            └── docker-build  (app image, no push)
```

A weekly scheduled pipeline runs the full medallion (generate → bronze → dbt build → export snapshot → R2 upload) and uploads a 30-day artifact.

---

## Docs

- **Architecture, theory companion, metric dictionary:** [GitHub Pages](https://swapniljoijode.github.io/Retail-Fashion-Intelligence/)
- **dbt lineage graph + column descriptions:** [dbt docs](https://swapniljoijode.github.io/Retail-Fashion-Intelligence/dbt-docs/)
- **Snowflake trial setup guide:** [docs/snowflake_setup.md](docs/snowflake_setup.md)
- **Backfill procedure:** [docs/backfill_procedure.md](docs/backfill_procedure.md)

---

*Built by [Swapnil Joijode](https://github.com/swapniljoijode)*
