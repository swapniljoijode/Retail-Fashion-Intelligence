# Fashion Retail Intelligence Platform

*End-to-End Data Engineering Project Plan*

Prepared for Swapnil Joijode | Version 1.1 | June 2026

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Architecture Decisions](#2-architecture-decisions)
- [3. Technology Stack, Free-Tier Validated](#3-technology-stack-free-tier-validated)
- [4. Tools Added Beyond the Original Scope](#4-tools-added-beyond-the-original-scope)
- [5. Target Data Model](#5-target-data-model)
- [6. Repository Structure](#6-repository-structure)
- [7. Phased Delivery Plan](#7-phased-delivery-plan)
  - [Phase 0. Charter and Foundation](#phase-0-charter-and-foundation)
  - [Phase 1. Dimensional Model and Metric Dictionary](#phase-1-dimensional-model-and-metric-dictionary)
  - [Phase 2. Synthetic Data Generation in Python](#phase-2-synthetic-data-generation-in-python)
  - [Phase 3. Raw Storage and Bronze Ingestion](#phase-3-raw-storage-and-bronze-ingestion)
  - [Phase 4. Transformations, Silver and Gold with dbt](#phase-4-transformations-silver-and-gold-with-dbt)
  - [Phase 5. Orchestration with Airflow and Cosmos](#phase-5-orchestration-with-airflow-and-cosmos)
  - [Phase 6. Containerization and Testing](#phase-6-containerization-and-testing)
  - [Phase 7. CI/CD with GitLab](#phase-7-cicd-with-gitlab)
  - [Phase 8. Serving Layer and Dashboard App](#phase-8-serving-layer-and-dashboard-app)
  - [Phase 9. Future Scope, Images, Observability, Documentation](#phase-9-future-scope-images-observability-documentation)
- [8. The Theory Companion, Learning Track](#8-the-theory-companion-learning-track)
- [9. Future Scope](#9-future-scope)
- [10. Risk Register](#10-risk-register)
- [11. Sequencing and Milestones](#11-sequencing-and-milestones)

---

## 1. Executive Summary

This document defines the end-to-end build of a Fashion Retail Intelligence Platform: a medallion-architecture data engineering project that generates synthetic fashion retail data, lands it in object storage, ingests and transforms it through bronze, silver, and gold layers, orchestrates the pipeline, ships it through continuous integration, and serves business-ready insight through a branded dashboard application.

The platform is engineered to run at zero cost permanently while still demonstrating the enterprise vocabulary that interviews reward. This is achieved through a dual-track design: the full medallion is built in Snowflake during its trial window for credibility, and an identical dbt project runs against DuckDB for a free, reproducible, always-available version. The live dashboard reads an exported snapshot, so it survives the Snowflake trial expiry rather than breaking with it.

The plan is sequenced in ten phases, each with a clear objective, a detailed step layout, deliverables, watch-outs, and a definition of done. A parallel theory companion grows with every phase, converting each tool and each concept into interview-ready knowledge.

Two disciplines run across every phase. All work is version controlled in Git, and the CI/CD pipeline is bound to that repository so that history, review, and delivery form one system. Progress is recorded in a dedicated Project Tracker application, a separate build with its own repository and its own detailed development plan. That tracker is built first, before Phase 0 of this project, and once live it records the success, failure, and ongoing status of every task defined here.

---

## 2. Architecture Decisions

**The governing constraint.** Every tool in this build must be free. Three elements of the original stack collide with that rule, and the resolutions below are load-bearing.

**Object storage: Cloudflare R2, not S3**

R2 is S3-compatible, so existing boto3 code and Snowflake stages work unchanged. Every Cloudflare account includes ten gigabytes of storage, one million write operations, ten million read operations per month, and zero egress fees, with no time limit. S3 by contrast offers only a twelve-month free tier and always charges for egress. MinIO, the former self-hosted alternative, was archived in February 2026 and is no longer maintained, so it is excluded.

**Warehouse: Snowflake trial plus a DuckDB shadow**

Snowflake has no permanent free tier; it provides a thirty-day trial with roughly four hundred dollars in credits. That is sufficient to build and demonstrate the full medallion, which carries the interview vocabulary of warehouses, micro-partitions, stages, and clustering keys. In parallel, the identical dbt project runs against DuckDB, which is free forever and runs locally in Docker. The dbt adapter abstraction makes this nearly free to maintain: same models, a different target in profiles.yml.

**Serving: decouple the dashboard from the warehouse**

The warehouse is the factory. The dashboard reads the factory output, not the factory. Gold marts are exported to a snapshot in R2 and optionally into Cloudflare D1 or Neon Postgres. The Next.js app reads that snapshot, which means the public dashboard remains live indefinitely and never depends on an always-on warehouse.

**Orchestration runtime reality**

Airflow is free and open source, but an always-on hosted instance is not free. The build runs Airflow locally in Docker for demonstration and recording, and uses GitLab scheduled pipelines as the lightweight production-grade proof of orchestration.

**Version control and progress tracking**

Git is the system of record. Every artifact is committed, main is protected, and the CI/CD pipeline is bound to the repository so version control and delivery are one system. Progress is tracked in a separate Project Tracker application that records each task as ongoing, success, or failure. The two codebases stay independent and integrate through a versioned template and an API, not through shared code. Crucially, status updates flow to the tracker as data through its API; the tracker application is never rebuilt to record a status change. The tracker has its own detailed development plan and is built first.

---

## 3. Technology Stack, Free-Tier Validated

Every component below is free to implement, in line with the project constraint. The only paid element, Snowflake, is confined to its free trial and is shadowed by a permanently free equivalent.

| Layer | Tool | Free status | Role |
| --- | --- | --- | --- |
| Generation | Python: Faker, NumPy, pandas, pyarrow | Free, open source | Generate and stage synthetic data |
| Raw storage | Cloudflare R2 | Free, 10GB, zero egress, no time limit | Raw landing and served snapshot |
| Warehouse build | Snowflake | 30-day trial, not permanent | Medallion build and interview vocabulary |
| Warehouse shadow | DuckDB | Free, open source | Permanent reproducible warehouse |
| Transformation | dbt core, snowflake, duckdb, expectations | Free, open source | Silver and gold modeling, tests, docs |
| Orchestration | Apache Airflow plus astronomer-cosmos | Free, local Docker | Scheduled pipeline DAG |
| Containers | Docker, Docker Compose | Free | Reproducible environments and testing |
| CI/CD | GitLab CI/CD | Free tier | Lint, test, build, deliver |
| Serving store | R2 plus optional D1 or Neon | Free tiers | Snapshot the dashboard reads |
| Frontend | Next.js, Recharts or Chart.js | Free, open source | Dashboard application |
| Hosting | Vercel Hobby or Cloudflare Pages | Free | Host the dashboard |
| Quality gates | ruff, black, sqlfluff, pre-commit | Free, open source | Code consistency enforcement |
| Env and deps | uv | Free, open source | Reproducible Python environment |
| Observability | Elementary | Free, open source | Data observability |
| Diagrams | dbdiagram.io or Mermaid | Free | ERD and lineage diagrams |
| Version control | Git on GitLab or GitHub | Free | System of record; CI/CD bound to the repository |
| Progress tracking | Project Tracker app, separate repo | Free, self-hosted on Vercel | Records task success, failure, and ongoing status |

---

## 4. Tools Added Beyond the Original Scope

The original brief named Python, Snowflake, dbt, a DAG, S3, Docker, and GitLab. The following additions close real gaps. Critical items are essential for a credible build; recommended items raise it to senior standard.

**Critical additions**

- Frontend framework: Next.js with Recharts or Chart.js. The dashboard is a full-stack web build, not a Power BI report, so the framework must be named explicitly.
- Data quality layer: dbt-expectations plus dbt model contracts, on top of dbt built-in tests. This enforces your standard that data accuracy is the overriding constraint.
- dbt docs: a free data catalog and lineage graph, and one of the strongest interview artifacts available.
- Code quality gates: ruff, black, sqlfluff, and pre-commit, which enforce your stated intolerance for inconsistent naming and formatting.
- Secrets handling: GitLab CI/CD variables, python-dotenv, and Snowflake key-pair authentication.
- Progress tracking application: a dedicated tracker, built first, that records the success, failure, and ongoing status of every task. It has its own repository and its own development plan.
- Git version control discipline: conventional commits, milestone tags, protected main, and CI/CD bound to the repository so version control and delivery are one system.

**Recommended additions**

- astronomer-cosmos to render dbt cleanly inside Airflow.
- Elementary for free data observability dashboards.
- uv for fast, reproducible Python dependency management.
- A Makefile as a single task runner for the whole project.
- pytest for the generators and ingestion logic.

---

## 5. Target Data Model

The model is designed before any data is generated. It is a set of conformed dimensions feeding five star-schema marts, one per business domain.

**Conformed dimensions**

| Dimension | Grain | Key attributes | History |
| --- | --- | --- | --- |
| dim_product | One row per SKU | category, subcategory, brand, color, size, season, cost, price | Type 2 on price |
| dim_store | One row per store | region, city, store type, square footage | Type 1 |
| dim_customer | One row per customer | segment, loyalty tier, location, acquisition channel | Type 2 on segment |
| dim_date | One row per day | day, week, month, quarter, season, holiday flag | Static |
| dim_channel | One row per channel | online, in-store, marketplace | Type 1 |
| dim_promotion | One row per promotion | type, discount, start, end | Type 1 |

**Fact tables**

| Fact | Grain | Core measures |
| --- | --- | --- |
| fact_sales | One row per order line | units, gross revenue, discount, net revenue, margin |
| fact_inventory_snapshot | Product, store, day | units on hand, units in transit, stockout flag |
| fact_returns | One row per return line | units returned, refund value, reason |
| fact_web_events | One row per session event | views, add-to-cart, conversions |
| fact_markdown | Product, store, week | markdown depth, units sold on markdown |

**Mart to domain mapping**

| Mart | Primary questions | Example KPIs |
| --- | --- | --- |
| Sales | Where is revenue moving and why | revenue, AOV, sell-through, units |
| Marketing | Which channels and campaigns convert | conversion rate, acquisition, attribution |
| Category management | Which categories earn their space | gross margin, top movers, space-to-sales |
| Product planning | What to buy, hold, or replenish | sell-through rate, weeks of supply, size curve |
| Placement | How to distribute and allocate stock | regional distribution, allocation, stockout rate |

---

## 6. Repository Structure

A single monorepo holds every layer so the project reads as one coherent system.

```text
fashion-retail-intelligence/
  data_generation/      Python generators and fashion taxonomy
  ingestion/            R2 upload and bronze load scripts
  dbt/                  dbt project: staging, intermediate, marts
  orchestration/        Airflow DAGs and Cosmos config
  dashboard/            Next.js application
  docker/               Dockerfiles and docker-compose.yml
  docs/                 theory companion and dbt docs
  tests/                pytest suites
  .gitlab-ci.yml        pipeline definition
  Makefile              task runner
  pyproject.toml        pinned dependencies
  .env.example          documented variables, no secrets
```

---

## 7. Phased Delivery Plan

Each phase below carries the same structure: objective, scope, detailed steps, tools, deliverables, watch-outs, a definition of done, and the theory topics it contributes to the learning track. A phase is not started until the previous definition of done is met.

### Phase 0. Charter and Foundation

**Objective.** Stand up a professional repository, a reproducible environment, and automated quality gates before any feature work begins.

**Scope.** Repository structure, Python environment, container baseline, linting and formatting hooks, task runner, secrets scaffolding, and a written project charter.

**Detailed steps**

1. Initialize a Git repository with a clear monorepo layout (see Section 6). Protect main and work through feature branches and merge requests.
2. Create the Python environment with uv. Pin dependencies in pyproject.toml and commit the lockfile so every clone is identical.
3. Add the pre-commit framework. Wire ruff and black for Python and sqlfluff for SQL so quality is enforced on every commit, not at review time.
4. Write a Makefile exposing standard commands: setup, seed, ingest, dbt-run, dbt-test, test, and lint. One verb per action.
5. Establish secrets handling. A .env file ignored by Git, python-dotenv for local loading, and a documented .env.example. Pipeline credentials live in GitLab CI/CD variables only.
6. Author the project charter: scope, success criteria, explicit out-of-scope items, and the five marts named as internal customers.
7. Author the tracker migration template: a machine-readable file listing every phase and task with stable identifiers. This file is the single source of truth that seeds the Project Tracker and mirrors the tasks in this plan, so tasks are written once and consumed by both the document and the tracker.

**Tools and libraries.** Git, GitLab, uv, ruff, black, sqlfluff, pre-commit, make, python-dotenv.

**Deliverables**

- Initialized repository with protected main
- Green pre-commit run on a clean clone
- Makefile, .env.example, and charter document
- Tracker migration template authored and seeding the Project Tracker

**Watch-outs**

- Never commit a secret. Add .env and credential files to .gitignore on day one.
- Lock naming conventions now (snake_case tables, stg_ int_ fct_ dim_ dbt prefixes) so they stay consistent for the life of the project.

**Definition of done.** A fresh clone followed by make setup produces a working environment with all hooks passing.

**Theory companion topics added.** monorepo vs polyrepo, why lockfiles matter, pre-commit hooks and shift-left quality, environment isolation, and the twelve-factor principle of config in the environment rather than in code.

---

### Phase 1. Dimensional Model and Metric Dictionary

**Objective.** Define the target star schemas and lock every metric definition before a single row of data is generated. This is the requirement kit your own hard-won lesson demands.

**Scope.** Conceptual and logical models, grain statements, a metric dictionary, and the mapping of each mart to its business domain.

**Detailed steps**

1. State the business questions each of the five marts must answer. One page per domain: marketing, sales, category management, product planning, placement.
2. Design the conformed dimensions: dim_product, dim_store, dim_customer, dim_date, dim_channel, dim_promotion. Define keys, attributes, and which dimensions are slowly changing.
3. Design the fact tables with explicit grain statements: fact_sales at order-line grain, fact_inventory_snapshot at product-store-day grain, fact_returns, fact_web_events, and fact_markdown.
4. Write the metric dictionary. For every KPI, record name, definition, formula, grain, and owning mart. Examples: sell-through rate, weeks of supply, gross margin, average order value, conversion rate, return rate.
5. Produce an entity relationship diagram using dbdiagram.io or Mermaid, both free.
6. Review the model against the business questions. Every question must be answerable from the model. If one is not, revise the model before moving on.

**Tools and libraries.** dbdiagram.io or Mermaid, a markdown metric dictionary.

**Deliverables**

- Entity relationship diagram
- Metric dictionary with formulas and grain
- Mart-to-domain mapping table

**Watch-outs**

- Lock metric definitions here. Category managers cause rework precisely because metrics are not standardized before the build. This phase is that standardization, made formal.
- Decide slowly changing dimension strategy per dimension now, not later.

**Definition of done.** Every mart KPI has a single agreed formula and grain recorded in the metric dictionary.

**Theory companion topics added.** star vs snowflake schema, fact grain, conformed dimensions, slowly changing dimensions types 1 2 and 3, additive vs semi-additive vs non-additive measures, and surrogate vs natural keys.

---

### Phase 2. Synthetic Data Generation in Python

**Objective.** Generate a realistic, controllable, and intentionally imperfect fashion retail dataset driven by the Phase 1 model.

**Scope.** Dimension generators, fact generators with seasonality and behavior, deliberate data dirtiness, and Parquet output.

**Detailed steps**

1. Build the dimension generators first. Faker supplies names, addresses, and identifiers. A hand-seeded fashion taxonomy supplies category, subcategory, brand, color, size, and season for realism.
2. Build the fact generators. Use NumPy distributions for quantities and prices. Encode seasonal curves, weekend uplift, promotional response, and price elasticity so sales read like behavior rather than uniform noise.
3. Make volume configurable: a small set for fast local DuckDB iteration and a larger set for the Snowflake build.
4. Inject controlled dirtiness: nulls in non-critical fields, duplicate rows, type drift such as numbers stored as strings, and inconsistent category casing. This gives the silver layer real work to do.
5. Write outputs as date-partitioned Parquet using pandas or pyarrow.
6. Cover the generators with pytest: schema shape, referential integrity so every fact key exists in a dimension, and value ranges.

**Tools and libraries.** Faker, NumPy, pandas, pyarrow, pytest. Avoid black-box synthesizers such as SDV; a transparent generator is more defensible in interviews and far easier to control.

**Deliverables**

- Generator package with configurable volume
- Partitioned Parquet output
- Generator test suite

**Watch-outs**

- Seed the random generators so runs are reproducible.
- Keep the dirtiness intentional and documented, never accidental, so you can speak to exactly what the silver layer cleans.

**Definition of done.** The generator produces referentially consistent Parquet at two volumes with passing tests and a fixed seed.

**Theory companion topics added.** why synthetic data, Parquet vs CSV with columnar storage and predicate pushdown, partitioning, referential integrity, reproducible randomness with seeds, and pytest fixtures.

---

### Phase 3. Raw Storage and Bronze Ingestion

**Objective.** Land raw data in object storage and ingest it untransformed into the bronze layer of the medallion.

**Scope.** R2 buckets, upload, Snowflake external stage and COPY INTO, and the DuckDB equivalent.

**Detailed steps**

1. Create R2 buckets: one for raw landing and one reserved for the served mart snapshot built in Phase 8. Configure S3-compatible credentials.
2. Upload Parquet to R2 with boto3 pointed at the R2 S3-compatible endpoint.
3. Snowflake path: create a storage integration or external stage onto R2, define file formats, and COPY INTO bronze tables. Bronze mirrors the source, schema-on-read, no cleaning, append-only, with ingestion metadata columns for load timestamp and source file.
4. DuckDB path: read the same Parquet from R2 or local disk into bronze tables. Identical logical layer at zero cost.
5. Validate land-to-bronze row counts and log every ingestion run.

**Tools and libraries.** boto3, Cloudflare R2, Snowflake external stage, DuckDB, Parquet.

**Deliverables**

- R2 buckets and upload script
- Snowflake external stage and bronze tables
- DuckDB bronze tables and an ingestion log

**Watch-outs**

- Bronze is immutable and append-only. Never clean or reshape here.
- Capture lineage metadata so every row records where it came from and when.

**Definition of done.** Raw Parquet in R2 lands in bronze on both Snowflake and DuckDB with matching row counts.

**Theory companion topics added.** object vs block vs file storage, external stages and storage integrations, COPY INTO and bulk loading, schema-on-read vs schema-on-write, why bronze is immutable, and micro-partitions in Snowflake.

---

### Phase 4. Transformations, Silver and Gold with dbt

**Objective.** Transform bronze into a clean conformed silver layer and business-ready gold marts using dbt, with tests, contracts, and generated documentation.

**Scope.** The dbt project, staging, intermediate, and mart layers, tests, contracts, docs, and dual targets for Snowflake and DuckDB.

**Detailed steps**

1. Initialize the dbt project. Configure profiles.yml with two targets, snowflake and duckdb. The models are identical; only the connection changes.
2. Build staging models with the stg_ prefix, one per source. Cast types, rename to conventions, deduplicate, and standardize categoricals. Your cleaning framework lives here as code.
3. Build intermediate models with the int_ prefix. Conform and join, centralize reusable logic, and resolve slowly changing dimensions.
4. Build gold marts with dim_ and fct_ prefixes: the five star schemas mapped to marketing, sales, category management, product planning, and placement.
5. Test with dbt built-ins (unique, not_null, relationships, accepted_values) plus dbt-expectations for distribution and range checks. Add model contracts on gold to enforce column names and types.
6. Document every model and column, then run dbt docs generate to produce the catalog and the lineage graph.

**Tools and libraries.** dbt-core, dbt-snowflake, dbt-duckdb, dbt-expectations, dbt docs.

**Deliverables**

- Full dbt project with a three-layer medallion
- Test suite and gold-layer contracts
- Generated docs site with lineage graph

**Watch-outs**

- Incremental models must be idempotent and handle late-arriving data.
- Choose materializations deliberately. Do not make everything a table or everything a view.

**Definition of done.** dbt build passes on both targets with every test green and docs generated.

**Theory companion topics added.** dbt project anatomy and profiles.yml, ref and source functions, materializations (view, table, incremental, ephemeral), incremental strategies and idempotency, materialized vs non-materialized views, indexing vs clustering keys, dbt tests and contracts, snapshots for type-2 history, and the lineage graph.

---

### Phase 5. Orchestration with Airflow and Cosmos

**Objective.** Orchestrate the end-to-end pipeline as a scheduled, observable directed acyclic graph.

**Scope.** Airflow running in Docker, and one DAG covering generate, land, ingest, transform, test, and export.

**Detailed steps**

1. Run Airflow locally with the official Docker Compose. No paid hosting.
2. Build the DAG: generate data, upload to R2, COPY into bronze, dbt run, dbt test, then export marts to the served snapshot.
3. Use astronomer-cosmos to render the dbt project as native Airflow tasks, so each model is a visible task with its own retries and logs.
4. Set dependencies, retries, and a schedule. Make every task idempotent so reruns are safe.
5. Demonstrate a backfill and document the procedure.

**Tools and libraries.** Apache Airflow, Docker Compose, astronomer-cosmos.

**Deliverables**

- Running Airflow instance
- The pipeline DAG with Cosmos-rendered dbt tasks
- A documented backfill run

**Watch-outs**

- Always-on hosting is not free. For the portfolio, run and record locally, and present GitLab scheduled pipelines as the lightweight production alternative.
- Idempotency is non-negotiable for safe reruns.

**Definition of done.** The DAG runs end to end locally, is rerunnable without side effects, and produces the served snapshot.

**Theory companion topics added.** what orchestration solves, DAGs tasks and operators, idempotency and backfills, scheduling and catchup, retries and alerting, and why Cosmos beats a single bash dbt task.

---

### Phase 6. Containerization and Testing

**Objective.** Make the whole stack reproducible in containers and prove correctness with layered tests.

**Scope.** Dockerfiles, Docker Compose, pytest, dbt tests, and environment parity between local and CI.

**Detailed steps**

1. Containerize the Python generation and ingestion service on a pinned base image.
2. Compose the stack: the ingestion service, Airflow, DuckDB, and supporting services in one Docker Compose file.
3. Layer the tests: pytest for Python logic, dbt tests for data, and a smoke test that runs a minimal end-to-end pipeline.
4. Ensure parity so the same container runs locally and in the pipeline.

**Tools and libraries.** Docker, Docker Compose, pytest, dbt.

**Deliverables**

- Dockerfiles and a Compose stack
- Unit, data, and integration test suites
- A one-command local run

**Watch-outs**

- Keep images small and pinned.
- Never bake secrets into an image.

**Definition of done.** docker compose up followed by make test runs the pipeline and passes all tests on a clean machine.

**Theory companion topics added.** containers vs virtual machines, images vs containers, Docker layers and build caching, Compose for multi-service apps, the testing pyramid for data, and environment parity.

---

### Phase 7. CI/CD with GitLab

**Objective.** Automate quality and delivery on every change.

**Scope.** GitLab pipeline stages, secrets, scheduled runs, and merge gating.

**Detailed steps**

1. Define the pipeline with stages for lint, test, build, and dbt run.
2. Lint runs ruff, black in check mode, and sqlfluff. Test runs pytest and dbt tests against DuckDB, which is free and fast. Build produces the Docker image.
3. Store credentials as masked and protected GitLab CI/CD variables.
4. Add a scheduled pipeline to demonstrate orchestration without a hosted Airflow.
5. Gate merges into main on a green pipeline.
6. Emit task status to the Project Tracker on each stage. On success or failure the pipeline calls the tracker API so progress is recorded automatically, as data, without redeploying the tracker.

**Tools and libraries.** GitLab CI/CD, the .gitlab-ci.yml file, CI/CD variables.

**Deliverables**

- A working .gitlab-ci.yml
- A passing pipeline and a scheduled job
- Protected main with merge gates

**Watch-outs**

- Run heavy steps against DuckDB in CI to stay free and fast; reserve Snowflake for the manual trial build.
- Never echo a secret into pipeline logs.
- Send progress to the tracker through its API as data. Never trigger a tracker rebuild for a status change.

**Definition of done.** Every merge request triggers lint, test, and build, and merges are blocked unless the pipeline is green.

**Theory companion topics added.** CI vs CD, pipeline stages and runners, artifacts and caching, secrets management in CI, trunk-based development and merge gates, and why you test against the cheap target.

---

### Phase 8. Serving Layer and Dashboard App

**Objective.** Deliver a branded, decision-led fashion retail dashboard on Vercel that reads a snapshot fully decoupled from the warehouse.

**Scope.** Mart export, the serving store, the Next.js app, charts, and hosting.

**Detailed steps**

1. Export gold marts to the served snapshot: Parquet or JSON in R2, and optionally loaded into Cloudflare D1 or Neon Postgres for queryable access.
2. Build the Next.js app. Serverless route handlers read the snapshot. The app never depends on an always-on Snowflake.
3. Design to your philosophy: brand colors and logo, executive KPIs at the top with positive and negative indicators, supporting charts below that answer specific questions, one consistent theme, no duplicate charts, and no needless drillthrough.
4. Build the five domain views: sales, marketing, category, product planning, placement. Each leads with the decision it drives.
5. Deploy to Vercel Hobby or Cloudflare Pages, both free.

**Tools and libraries.** Next.js, Recharts or Chart.js, Vercel or Cloudflare Pages, R2, and optionally Cloudflare D1 or Neon.

**Deliverables**

- The served snapshot in R2
- A deployed dashboard with five domain views
- A live public link

**Watch-outs**

- The live app must survive the Snowflake trial expiry. Reading the snapshot is what guarantees that.
- Keep the design simple. Resist chart clutter at every step.

**Definition of done.** A public URL renders the five domain views from the snapshot with no dependency on the warehouse being live.

**Theory companion topics added.** decoupling serving from compute, static vs dynamic serving, serverless functions, caching and revalidation, why a custom app over a hosted BI tool here, and dashboard information hierarchy.

---

### Phase 9. Future Scope, Images, Observability, Documentation

**Objective.** Extend the platform with product imagery, data observability, and a polished documentation surface.

**Scope.** An image pipeline, Elementary observability, and a published documentation site.

**Detailed steps**

1. Images: use an openly licensed source such as the Kaggle Fashion Product Images dataset or the Unsplash and Pexels free APIs. Do not scrape arbitrary retail sites; that is a copyright and terms-of-service risk on a public portfolio. Store images in R2, key by product_id, and render on dashboard thumbnails.
2. Observability: add Elementary to surface dbt test results, freshness, and anomalies as a free report.
3. Documentation: publish the theory companion alongside the dbt docs, optionally through MkDocs or a docs route in the app.

**Tools and libraries.** Kaggle dataset or Unsplash and Pexels APIs, R2, Elementary, MkDocs, dbt docs.

**Deliverables**

- Image pipeline with thumbnails keyed by product_id
- A live observability report
- Published documentation

**Watch-outs**

- Respect image licensing and record provenance.
- Keep image volume within the R2 free tier; thumbnails sit comfortably inside 10GB.

**Definition of done.** Thumbnails render from R2 by product_id, the observability report is live, and the docs are published.

**Theory companion topics added.** data observability vs testing, freshness and anomaly detection, licensing and provenance for assets, and CDN delivery and egress economics.

---

## 8. The Theory Companion, Learning Track

A second document grows alongside this plan. Its purpose is to ensure you learn the theory behind every tool, action, file, and line of code, not only the practical steps. It is structured with an index, then one entry per concept, each closing with interview-favorite questions and answers.

Every phase contributes its theory topics, listed in this plan under the heading Theory companion topics added. By the end of Phase 9 the companion covers the full arc from indexing and micro-partitions to materialization strategy, idempotency, and serving economics. Each entry pairs what a thing does with why it exists and when it fails, which is the framing interviewers probe.

**Sample entry shape.** Concept: materialized vs non-materialized views. What it is. Why it exists. The cost and freshness trade-off. When it breaks. Two interview questions with model answers.

---

## 9. Future Scope

Three extensions take the platform from complete to distinctive.

- Product imagery: source images from openly licensed datasets or free APIs, store in R2, key by product_id, and render on dashboard thumbnails. Never scrape arbitrary retail sites; that introduces copyright and terms-of-service risk on a public portfolio.
- Data observability: Elementary turns dbt test results, freshness, and anomalies into a free monitoring surface.
- Documentation site: publish the theory companion and dbt docs together so the learning artifact is itself shareable.

---

## 10. Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Snowflake trial expiry ends the warehouse | High | DuckDB shadow keeps the project live; dashboard reads an exported snapshot |
| R2 free-tier limits exceeded | Medium | Keep data and images small; serve thumbnails only |
| Scope creep across ten phases | High | Phase gates with a definition of done; ship phase by phase |
| Frontend sits outside the core skill set | Medium | Use Next.js templates and keep the design simple, per the design philosophy |
| Image licensing violation | High | Use openly licensed sources only and record provenance |
| Always-on orchestration is not free | Medium | Run Airflow locally; use GitLab scheduled pipelines as production proof |
| Tracker scope grows larger than the core project | High | Timebox the tracker; keep it lean; the retail pipeline remains the headline portfolio asset |
| Cross-repo coupling between project and tracker | Medium | Integrate through the tracker API and a versioned template, never shared code or redeploys |

---

## 11. Sequencing and Milestones

The phases are linear and gated. Each milestone is reached when the corresponding phase definition of done is met. Because the work is self-paced, sequence and dependency matter more than calendar dates, and effort is allocated by importance rather than urgency.

One milestone precedes this plan entirely. The Project Tracker application is built and deployed first, under its own development plan, and is recording status before Phase 0 begins.

- M-1 Pre-project: Project Tracker live on Vercel, seeded from the migration template, and ready to record status. See the companion tracker development plan.
- M0 Foundation: repository, environment, and quality gates live.
- M1 Model locked: dimensions, facts, and metric dictionary agreed.
- M2 Data: synthetic generator producing tested Parquet.
- M3 Bronze: raw data landed in R2 and ingested to both targets.
- M4 Marts: silver and gold built, tested, documented in dbt.
- M5 Orchestrated: the full pipeline runs as a rerunnable DAG.
- M6 Containerized: one-command local run passes all tests.
- M7 CI/CD: merges gated on a green pipeline.
- M8 Dashboard: five domain views live on a public link.
- M9 Extensions: images, observability, and docs published.

