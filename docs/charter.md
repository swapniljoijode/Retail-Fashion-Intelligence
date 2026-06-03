# Project Charter — Fashion Retail Intelligence Platform

**Owner:** Swapnil Joijode
**Version:** 1.0
**Date:** June 2026
**Status:** Active

---

## Purpose

Build an end-to-end, medallion-architecture data engineering platform for fashion retail intelligence. The platform demonstrates the full data engineering lifecycle — from synthetic data generation through transformation, orchestration, and serving — using enterprise-grade tooling at zero cost.

This is a portfolio project, engineered to reflect the vocabulary, decisions, and trade-offs that senior data engineering roles reward.

---

## Success Criteria

1. A medallion pipeline (bronze → silver → gold) running on both Snowflake (trial) and DuckDB (permanent shadow) via a single dbt project.
2. A CI/CD pipeline that blocks merges to main unless lint, unit tests, and dbt tests are green.
3. A deployed public dashboard on Vercel serving five domain views from a static snapshot, with no runtime dependency on the warehouse.
4. A Project Tracker that records phase and task status via API, updated automatically by the CI/CD pipeline.
5. Every phase has a documented definition of done that is met before the next phase begins.

---

## Scope

**In scope**

- Synthetic data generation with configurable volume and a fixed seed
- Object storage via Cloudflare R2 (raw and served buckets)
- Snowflake bronze/silver/gold build during the trial window
- DuckDB shadow that mirrors the Snowflake build permanently
- dbt project with staging, intermediate, and mart layers for five business domains
- Airflow DAG (local Docker) covering generate → ingest → transform → export
- Docker Compose stack for reproducible local runs
- GitLab CI/CD pipeline with lint, test, build, and scheduled run stages
- Next.js dashboard with five domain views hosted on Vercel
- Elementary data observability
- Product image pipeline using openly licensed sources

**Out of scope**

- Real customer or transaction data of any kind
- Always-on cloud Airflow hosting (cost constraint)
- Power BI, Tableau, or any proprietary BI tool
- Machine learning or forecasting models
- Any scraping of live retail sites

---

## Business Domains and Internal Customers

The platform serves five internal business functions, each represented by a mart and a dashboard view.

| Domain | Primary question | Owning mart |
|---|---|---|
| Sales | Where is revenue moving and why? | mart_sales |
| Marketing | Which channels and campaigns convert? | mart_marketing |
| Category management | Which categories earn their space? | mart_category |
| Product planning | What to buy, hold, or replenish? | mart_product_planning |
| Placement | How to distribute and allocate stock? | mart_placement |

---

## Constraints

- **Zero cost**: every tool must be free or within a free tier. Snowflake is the sole exception and is confined to its 30-day trial.
- **Reproducible**: a fresh clone followed by `make setup` must produce a working environment.
- **Decoupled serving**: the dashboard must survive Snowflake trial expiry.
- **Version controlled**: every artifact is committed; main is protected; CI/CD is bound to the repository.

---

## Naming Conventions

These are locked here and apply for the life of the project.

- Python: `snake_case` for variables, functions, and file names
- SQL/dbt: `snake_case` for all identifiers
- dbt model prefixes: `stg_` staging, `int_` intermediate, `fct_` fact, `dim_` dimension
- Parquet partitioning: `year=YYYY/month=MM/day=DD`
- Git: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- Branches: `feat/`, `fix/`, `chore/` prefixes; never commit directly to main

---

## Phase Gate Summary

| Milestone | Phase | Definition of done |
|---|---|---|
| M-1 | Pre-project | Project Tracker live on Vercel |
| M0 | Foundation | Fresh clone + `make setup` passes all hooks |
| M1 | Model locked | Every KPI has a formula and grain in the metric dictionary |
| M2 | Data | Generator produces tested Parquet at two volumes |
| M3 | Bronze | Raw Parquet in R2 with matching row counts on both targets |
| M4 | Marts | `dbt build` green on both targets with docs generated |
| M5 | Orchestrated | Full DAG rerunnable without side effects |
| M6 | Containerized | `docker compose up && make test` passes on a clean machine |
| M7 | CI/CD | Merges gated on green pipeline |
| M8 | Dashboard | Five domain views live on a public URL |
| M9 | Extensions | Images, observability, and docs published |
