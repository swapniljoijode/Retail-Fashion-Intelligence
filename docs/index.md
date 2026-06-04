# Fashion Retail Intelligence Platform

> End-to-end medallion data engineering portfolio — DuckDB · dbt · Airflow · Next.js

[![CI](https://github.com/swapniljoijode/Retail-Fashion-Intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/swapniljoijode/Retail-Fashion-Intelligence/actions/workflows/ci.yml)

## What this project is

A complete data engineering platform for a fictional fashion retailer, built to demonstrate the full enterprise data stack from raw generation to a live public dashboard — at **zero cost, permanently**.

| Layer | Tool | Why |
|---|---|---|
| Generation | Python (Faker, NumPy, pandas) | Controlled, reproducible synthetic data |
| Raw storage | Cloudflare R2 | S3-compatible, free forever, zero egress |
| Warehouse | DuckDB (permanent) + Snowflake (trial) | Free shadow + enterprise vocabulary |
| Transform | dbt-core + dbt-duckdb + dbt-expectations | Medallion layers, tests, contracts, docs |
| Orchestration | Airflow + astronomer-cosmos | DAG with per-model tasks and retries |
| Containers | Docker + Docker Compose | One-command reproducible environments |
| CI/CD | GitHub Actions | Lint → test-unit ‖ test-integration → docker-build |
| Dashboard | Next.js 14 + Recharts | Five domain views on Vercel Hobby (free) |
| Observability | Elementary | dbt test results, freshness, anomaly reports |
| Docs | MkDocs Material | This site |

## Architecture in one sentence

Synthetic Parquet → Cloudflare R2 → DuckDB bronze → dbt silver/gold → JSON snapshot → Next.js dashboard on Vercel.

The dashboard reads a static snapshot exported from gold marts — it never depends on the warehouse being alive, so it survives the Snowflake trial expiry.

## Five domain views

| Domain | Business question |
|---|---|
| **Sales** | Where is revenue moving and which channels and categories drive it? |
| **Marketing** | Which channels and devices convert, and what drives returns? |
| **Category** | Which categories earn their floor space and where is markdown deepest? |
| **Product Planning** | What to replenish now, what to hold, where is stockout risk highest? |
| **Placement** | Which regions are under-stocked relative to their revenue contribution? |

## Documentation

| Site | URL |
|---|---|
| **This site** (MkDocs) | `https://swapniljoijode.github.io/Retail-Fashion-Intelligence/` |
| **dbt lineage graph** | `https://swapniljoijode.github.io/Retail-Fashion-Intelligence/dbt-docs/` |
| **Live dashboard** | Vercel — see repo README for link |

## Quick start

```bash
git clone https://github.com/swapniljoijode/Retail-Fashion-Intelligence.git
cd Retail-Fashion-Intelligence
make setup          # create venv, install deps
make seed           # generate synthetic Parquet
make ingest         # load DuckDB bronze
make dbt-run        # run dbt silver + gold
make test           # run unit tests (86 tests)
make test-all       # run unit + integration smoke tests (99 tests)
```
