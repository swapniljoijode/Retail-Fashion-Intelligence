# Theory Companion

A structured reference of every concept used in this platform — what it is, why it exists, when it breaks, and the interview questions it answers.

---

## Data Engineering Fundamentals

### Medallion Architecture (Bronze / Silver / Gold)

**What it is.** A layered data organisation pattern where data moves through increasing levels of quality: raw and immutable (bronze), cleaned and conformed (silver), business-ready (gold).

**Why it exists.** Separates concerns: raw ingestion is decoupled from transformation, and transformation is decoupled from serving. Each layer can be rebuilt independently. The raw layer is the system of record — if something goes wrong in silver or gold, you re-derive rather than re-ingest.

**When it breaks.** When teams skip the raw layer and clean in-flight, losing the ability to replay from source. Or when silver becomes a dumping ground for business logic that belongs in gold.

**Interview questions.**
- *Why keep bronze immutable?* Because it is your recovery point. If silver transforms are wrong, you fix the transform and replay — you can't replay if bronze was already modified.
- *What materializes at each layer?* Bronze: external tables or raw copies. Silver: views (no storage cost, always fresh). Gold: tables (pre-computed, query-fast).

---

### Star Schema vs Snowflake Schema

**What they are.** In a star schema, a fact table references dimension tables directly. In a snowflake schema, dimensions are normalised into sub-dimension tables.

**Why star schema is preferred in analytics.** Fewer JOINs = faster queries. Denormalisation costs a little storage but saves a lot of compute. Analysts can reason about the model without following chains of relationships.

**When it breaks.** Star schema wastes storage on wide, repeating dimension values. Snowflake schema is appropriate when dimension cardinality is very high and storage is the binding constraint.

**Interview questions.**
- *What is fan-out?* A JOIN that multiplies rows unintentionally when one fact row matches many dimension rows. Star schemas avoid this by using surrogate keys with uniqueness guarantees.

---

### Slowly Changing Dimensions (SCD)

**What they are.** Dimension rows that change over time. Type 1 overwrites. Type 2 inserts a new row with date ranges. Type 3 adds a column for the previous value.

**This platform uses.** Type 2 on `dim_product` (when `retail_price` changes) and `dim_customer` (when `customer_segment` changes). Each version has `effective_date` and `expiry_date`; the current version has `expiry_date IS NULL`.

**Why Type 2.** Preserves history so you can answer "what was this product's price on the day it was sold?" — essential for accurate margin calculation.

**Date-range JOIN pattern.**
```sql
left join dim_product p
    on  f.product_id  = p.product_id
    and f.sale_date  >= p.effective_date
    and (f.sale_date <= p.expiry_date or p.expiry_date is null)
```

**Interview questions.**
- *What is the -1 sentinel?* A row in the dimension with surrogate key -1 representing "unknown". Facts that can't resolve a surrogate key coalesce to -1 rather than NULL so aggregations don't silently drop rows.

---

### Surrogate vs Natural Keys

**Natural key:** the business identifier (e.g. `product_id = "P001"`). Meaningful but mutable — the business can rename a product.

**Surrogate key:** a system-generated integer or hash. Meaningless but stable. Used as the FK in fact tables so dimension changes (SCD2) create new surrogate keys without invalidating historical fact rows.

---

### Additive vs Semi-Additive vs Non-Additive Measures

| Type | Can SUM across | Examples |
|---|---|---|
| Additive | All dimensions | revenue, units sold, cost |
| Semi-additive | Some dimensions (not time) | inventory on hand (take latest, don't sum) |
| Non-additive | No dimensions | ratios, percentages, ranks |

**Key rule:** Never average a percentage. Always recompute `numerator / denominator` from the summed components.

---

## dbt

### Materializations

| Type | When to use | Trade-off |
|---|---|---|
| `view` | Staging layer — always fresh, no storage cost | Recomputed on every query |
| `table` | Gold marts — fast query, pre-computed | Stale until next dbt run |
| `incremental` | Large fact tables — append or upsert only new rows | Complex idempotency requirements |
| `ephemeral` | Intermediate logic used once — no object in the warehouse | Can't be queried directly |

### Model contracts

Contracts enforce column names, types, and constraints at build time. If a model's output doesn't match the declared contract, `dbt build` fails. This platform enforces contracts on `dim_date` and `dim_product`.

### `ref()` and `source()`

`ref('model_name')` creates a DAG dependency between models and resolves to the correct schema regardless of target. `source('schema', 'table')` declares an external dependency and enables freshness checks. Never hardcode schema names.

### dbt-expectations

Extends dbt's built-in tests with distribution-level checks: value ranges, column sums, cardinality. This platform uses `expect_column_values_to_be_between` for price ranges and `expect_column_pair_values_to_be_equal` for referential checks.

---

## Orchestration

### Why Airflow beats a cron job

A cron job runs a command. Airflow runs a DAG — it tracks success/failure per task, retries on failure, supports backfills, exposes logs per task, and models dependencies explicitly. If task B depends on task A, Airflow enforces that; cron cannot.

### astronomer-cosmos

Renders a dbt project as native Airflow tasks: one task per model, one per test. This gives you per-model retry, per-model logs, and a visible dependency graph in the Airflow UI — instead of a single opaque "dbt run" bash task that succeeds or fails as a unit.

### Idempotency

An idempotent operation produces the same result whether run once or ten times. Required for safe retries and backfills. This platform achieves it by:
- Bronze load with `--reset` flag truncates and reloads
- dbt models are `CREATE OR REPLACE` (view) or `INSERT OVERWRITE` (table)
- The gold snapshot export overwrites the same output files

---

## Containers and CI/CD

### Docker layers and build caching

Each `RUN`, `COPY`, and `ADD` instruction creates a layer. Docker caches layers; if the instruction and all prior instructions are unchanged, the cached layer is reused. Place expensive steps (package install) before volatile steps (COPY source code) to maximise cache hits.

### Why test against DuckDB in CI

Snowflake has per-second compute charges. Running `dbt build` against DuckDB in CI costs nothing, takes seconds, and catches 95% of bugs. Reserve Snowflake for the manual trial build that generates the interview artifact.

### The testing pyramid for data

1. **Unit tests** — Python logic in isolation (generators, ingestion functions). Fast, no infrastructure.
2. **dbt tests** — Schema contracts, referential integrity, value ranges. Runs against DuckDB.
3. **Integration / smoke tests** — Full pipeline end-to-end on test volume. Validates the whole chain once, not every layer separately.

---

## Serving

### Static snapshot pattern

The dashboard reads JSON files exported from DuckDB gold marts. The files are committed to the repository and served at build time by Vercel. This means:

- No runtime database dependency
- No serverless cold start from a warehouse query
- No Snowflake cost after the trial
- Vercel rebuilds the static site whenever a new snapshot is committed

**Trade-off:** data is as fresh as the last scheduled pipeline run (weekly). For a portfolio, this is fine. For a production system, you'd use a CDN-fronted API route or a queryable edge database (Cloudflare D1, Neon).

### Server Components vs Client Components (Next.js App Router)

Server Components run at build time (or request time on the server). They can call `readFileSync` but cannot hold React state or use browser APIs. Client Components (`'use client'`) run in the browser, can use hooks and events, but cannot receive function props from Server Components — only serializable values (strings, numbers, arrays, plain objects).

**This platform's pattern:** pages are Server Components (read JSON, compute aggregates). Chart wrappers are Client Components (Recharts needs the browser DOM). Format type is passed as a string enum (`format="currency"`) not a function (`formatter={(v) => ...}`) to stay serializable across the boundary.

---

## Storage

### Parquet vs CSV

| | Parquet | CSV |
|---|---|---|
| Format | Binary columnar | Text row-oriented |
| Compression | Built-in per column | None or gzip whole file |
| Schema | Self-describing | No schema, inferred |
| Predicate pushdown | Yes (skip row groups) | No |
| Read performance | Fast for analytic (read few columns) | Slow |

**Why this platform uses Parquet:** DuckDB's `read_parquet()` reads only the columns needed for a query, and skips row groups that don't match a WHERE clause — no equivalent exists for CSV.

### Cloudflare R2 vs AWS S3

R2 is S3-compatible (same boto3 API, same path syntax) but has no egress fees and a permanent free tier (10 GB storage, 1M writes, 10M reads/month). S3's free tier expires after 12 months and charges for egress. For a permanent portfolio project, R2 is the correct choice.

### Object vs Block vs File Storage

| Type | Examples | Unit | Use case |
|---|---|---|---|
| Object | R2, S3, GCS | Object (arbitrary bytes + metadata) | Data lakes, backups, media — cheap, durable, no filesystem |
| Block | EBS, Azure Disk | Fixed-size block | Databases, VMs — fast random read/write, mounts like a disk |
| File | EFS, NFS | File/directory | Shared filesystems across machines |

**Why object storage for raw data:** you never need to seek within a file — you read whole Parquet files or stream them. Object storage is 10-100× cheaper than block storage at data lake scale and requires zero administration.

### CDN Delivery and Egress Economics

A CDN (Content Delivery Network) caches assets at edge nodes close to the user. For a dashboard that reads static JSON snapshots:
- Without CDN: every request hits the origin server (Vercel), and data transfer from origin costs egress fees
- With CDN: the first request caches the file at the edge; subsequent requests are served from cache at near-zero cost

Cloudflare R2's zero-egress policy is the key design decision here — serving snapshots from R2 directly (or via Cloudflare Pages) costs nothing regardless of traffic, unlike S3 which charges per GB out.

---

## Project Setup

### Monorepo vs Polyrepo

**Monorepo:** all components (data generation, ingestion, dbt, Airflow, dashboard) in one repository. One CI pipeline, one commit history, one lockfile.

**Polyrepo:** each component has its own repository. Stronger isolation, independent release cycles, but cross-component changes require coordinating multiple PRs.

**Why monorepo here:** the pipeline is a single unit — a change in the data generator cascades through bronze, silver, gold, and the dashboard. A monorepo makes that cascade visible in one commit and testable in one CI run. The tradeoff is a larger, slower CI pipeline.

**Interview question.** *When would you choose polyrepo?* When teams are truly independent and deploy at different cadences — e.g., a frontend team and a data team with separate on-call rotations. For a pipeline where every layer depends on the previous, monorepo wins.

### Why Lockfiles Matter

A lockfile (`uv.lock`, `poetry.lock`, `package-lock.json`) records the exact version of every dependency and every transitive dependency resolved at one point in time.

**Without a lockfile:** `pip install` resolves the latest compatible versions at install time. Two clones a week apart may install different versions and behave differently.

**With a lockfile:** every clone is byte-for-byte identical. CI, local development, and Docker builds all use the same graph. Bugs introduced by a dependency upgrade are caught at the one `uv lock` commit, not silently at a random engineer's `pip install`.

### Pre-commit Hooks and Shift-Left Quality

**Shift-left:** move quality checks earlier in the development cycle — before commit, not at PR review or CI.

**Pre-commit hooks** run on every `git commit`. If any hook fails (ruff finds a lint error, black reformats a file), the commit is blocked until the issue is fixed. The developer sees the problem immediately, in their editor, before it ever reaches CI.

**Why this matters at scale:** a lint error that takes 5 seconds to fix in your editor takes 5 minutes to fix via a CI cycle (push → wait → fail → fix → push → wait). Pre-commit hooks compress that loop to seconds.

### The 12-Factor Principle: Config in the Environment

Factor 3 of the 12-factor app methodology: *store config in the environment, not in code.*

**In practice:** credentials (`SNOWFLAKE_ACCOUNT`, `R2_SECRET_ACCESS_KEY`) live in `.env` (local) or CI/CD secrets (deployed) — never hardcoded in source. The code reads `os.environ.get('SNOWFLAKE_ACCOUNT')`. The same codebase runs locally, in Docker, and in CI with different configs purely through environment variables.

**Why it matters:** a secret hardcoded in code will eventually be committed to git (by accident or negligence) and is extremely hard to rotate. An env var can be rotated without touching the codebase.

---

## Data Generation and Testing

### Why Synthetic Data

Synthetic data is generated programmatically rather than sampled from real customers. For a portfolio project it is the only viable option (no real data access), but it has genuine engineering advantages:

- **Controllable volume:** small for fast local iteration, large for warehouse performance testing
- **Intentional dirtiness:** nulls, type drift, casing inconsistency injected on purpose so the silver layer has real work to do — and you can speak precisely to what was cleaned and why
- **Reproducible:** seeded with a fixed integer (`GENERATION_SEED=42`) so every run produces identical data, enabling deterministic tests

**Interview question.** *Why not use a library like SDV?* SDV synthesises data that statistically resembles a training dataset. That's useful for privacy-preserving analytics but opaque for a portfolio — you can't explain why a column has a certain distribution. A transparent generator is far more defensible in interviews.

### Partitioning

Partitioning splits a dataset into sub-directories by a column value, typically a date:

```
data_generation/output/
  fact_sales/
    year=2024/month=01/fact_sales_2024-01.parquet
    year=2024/month=02/fact_sales_2024-02.parquet
```

**Why it matters:** a query filtering on `year=2024 AND month=03` can skip all other partitions without reading them. DuckDB and Snowflake both implement partition pruning — `WHERE sale_date BETWEEN '2024-03-01' AND '2024-03-31'` reads only the March partition. Without partitioning, the engine scans everything.

### Referential Integrity

Every foreign key value in a fact table must exist in the referenced dimension. `fact_sales.product_id = 'P001'` requires `P001` to exist in `dim_product`.

**In this platform:** the data generators produce dimension tables first, then use their keys to generate fact rows. dbt `relationships` tests then verify that no fact row references a key that doesn't exist in the dimension — any violation is a generator bug.

### Reproducible Randomness and Seeds

`numpy.random.Generator(numpy.random.PCG64(seed=42))` produces the same sequence of random numbers every time seed 42 is used. This means:
- Tests can assert exact row counts and specific values
- Two engineers running `make seed` get identical Parquet files
- A bug that only appears with certain random data can be reproduced

**Interview question.** *What breaks reproducibility?* Using `datetime.now()` or `uuid.uuid4()` without seeding. This platform generates timestamps from seeded date ranges and uses deterministic ID sequences to avoid this.

### pytest Fixtures

A fixture is a function decorated with `@pytest.fixture` that pytest injects as an argument into test functions. It handles setup and teardown.

```python
@pytest.fixture(scope="session")
def pipeline():
    # setup — runs once per test session
    run_bronze_load(...)
    run_dbt_build(...)
    yield conn  # conn is available to every test that requests it
    # teardown — runs after all tests
    conn.close()
```

**Scope** controls how often the fixture runs: `function` (default, once per test), `class`, `module`, or `session` (once for the whole run). The smoke test uses `session` scope so the expensive dbt build runs once and all 13 gold-layer assertions share the same database.

---

## Snowflake Concepts

### Schema-on-Read vs Schema-on-Write

**Schema-on-write (traditional warehouse):** you define the column types before loading data. The database enforces the schema at insert time. Bad data is rejected.

**Schema-on-read (data lake / bronze):** you store the data as-is (e.g. raw Parquet) without enforcing types. Types are inferred when you query. A column that contains mostly integers but occasionally strings is stored as `VARCHAR` — the silver layer casts and validates.

**Bronze is schema-on-read by design.** `units_sold VARCHAR` preserves the intentional type drift injected by the generator. If we enforced an INTEGER type at load time, the dirty rows would be silently dropped. Instead they land in bronze and the silver model explicitly handles them with `TRY_CAST`.

### External Stages and COPY INTO

A Snowflake **external stage** is a pointer to an object storage location (R2, S3, GCS) plus credentials. It is not a copy of the data — it is a reference.

`COPY INTO` reads files from a stage, applies a schema, and inserts rows into a Snowflake table. It is idempotent by default: Snowflake tracks which files have been loaded and skips them on re-runs (unless `FORCE = TRUE`). This is the recommended bulk ingestion pattern for large datasets because it parallelises across files and uses Snowflake's internal optimiser rather than row-by-row INSERT.

**Interview question.** *What is `ON_ERROR = SKIP_FILE`?* Instead of aborting the entire COPY when a corrupt file is encountered, Snowflake skips that file and continues. The COPY history records which files were skipped so you can investigate. Used here so a single bad Parquet file doesn't block ingestion of all 11 tables.

### Micro-partitions in Snowflake

Snowflake automatically divides every table into **micro-partitions**: contiguous units of 50–500 MB of uncompressed data, stored columnar and compressed. Metadata (min, max, distinct count) is recorded per column per micro-partition.

**Why it matters for queries:**
- A filter `WHERE sale_date = '2024-03-15'` lets Snowflake skip every micro-partition whose `sale_date` range doesn't include that date — without a manual index
- Clustering keys (`CLUSTER BY (sale_date)`) co-locate rows with similar values into the same micro-partitions, improving the skip rate

**Contrast with DuckDB:** DuckDB uses row groups in Parquet files for the same purpose. The concept (skip partitions based on metadata) is identical; the implementation differs.

---

## Advanced dbt

### Incremental Models and Idempotency

An incremental model only processes new or changed rows rather than rebuilding the entire table. On the first run it creates the table; on subsequent runs it inserts/updates only rows that match the incremental filter.

```sql
{{ config(materialized='incremental', unique_key='sale_key') }}

SELECT * FROM {{ ref('stg_bronze__fact_sales') }}
{% if is_incremental() %}
  WHERE _load_timestamp > (SELECT MAX(_load_timestamp) FROM {{ this }})
{% endif %}
```

**Idempotency requirement:** if the pipeline reruns (due to failure or backfill), the result must be identical to a clean run. This requires either `unique_key` (upsert on conflict) or a reliable watermark that doesn't double-count. Without idempotency, retries produce duplicate rows.

**Why this platform uses `table` not `incremental` for gold marts:** gold mart tables are small (< 1 M rows for small volume). The simplicity of `CREATE OR REPLACE TABLE` outweighs the scan cost savings of incremental. Incremental is the right choice when the full rebuild cost is prohibitive — typically fact tables > 100 M rows.

### dbt Snapshots vs SCD Type 2 in Marts

dbt has a native `snapshot` materialisation that implements SCD Type 2 automatically. This platform implements SCD2 manually in intermediate ephemeral models instead.

**Why manual SCD2:**
- The source data already contains `effective_date` and `expiry_date` columns from the generator
- `dbt snapshot` is designed for live source tables where dbt itself detects the change; here the history is pre-baked into the Parquet
- Manual SCD2 gives explicit control over the date-range JOIN logic and is easier to test and document

**Interview question.** *When would you use `dbt snapshot`?* When you're ingesting from a source system that only exposes the current state (no history). dbt snapshot detects changes between runs and inserts new versions — exactly what a Type 2 SCD should do.

### The Lineage Graph

dbt generates a directed acyclic graph (DAG) of every model, source, and test. The nodes are SQL objects; the edges are `{{ ref() }}` and `{{ source() }}` calls.

**What it proves in an interview:** you understand that transformation pipelines are not isolated scripts but a dependency graph. Changes propagate — modify `stg_bronze__fact_sales` and you know exactly which intermediate models, marts, and tests depend on it. The graph makes impact analysis instant.

**In this platform:** `source → 11 staging views → 2 ephemeral intermediates → 11 gold tables → 190 tests`. The graph is visible at the dbt docs site linked from the README.

---

## CI/CD in Depth

### CI vs CD

**Continuous Integration (CI):** every commit triggers an automated build and test run. The goal is to detect integration failures immediately, before they compound. "Always keep the main branch shippable."

**Continuous Delivery (CD):** every passing build can be deployed to production with one click (or automatically). The pipeline extends CI with packaging, deployment, and smoke tests against the live environment.

**In this platform:** the GitHub Actions pipeline is CI only — it builds and tests but does not deploy (the dashboard deploys via Vercel's GitHub integration, not the CI pipeline). The scheduled pipeline is closer to CD: it runs the full medallion end-to-end and uploads a production snapshot.

### Trunk-Based Development and Merge Gates

**Trunk-based development:** developers work on short-lived feature branches and merge to `main` (the trunk) frequently — typically within a day or two. Long-lived branches accumulate divergence and create painful merges.

**Merge gate:** a branch protection rule that prevents merging to `main` unless:
1. A pull request has been opened
2. All required status checks (lint, test-unit, test-integration) are green

**Why this matters:** a green main branch means the latest code is always deployable. A broken main blocks the entire team. Merge gates enforce this invariant automatically.

### Secrets Management in CI

Credentials must never appear in source code, logs, or error messages. GitHub Actions provides **encrypted secrets** stored outside the repository. They are injected as environment variables at runtime and are masked in logs (any log line containing the secret value is replaced with `***`).

**Best practice hierarchy:**
1. Never commit credentials (enforced by `.gitignore` + pre-commit)
2. Store in CI/CD secrets (GitHub Actions, GitLab CI/CD variables)
3. Scope secrets to the narrowest environment (protected branches only)
4. Rotate on any suspected exposure

---

## Serving and Dashboard Design

### Dashboard Information Hierarchy

A well-designed analytical dashboard follows a deliberate hierarchy:

1. **Executive KPIs at the top** — the one-number answer to "how are we doing?" Positive/negative indicators give immediate directional signal.
2. **Supporting charts below** — each chart answers a specific question that a business user would ask after seeing the KPIs. Not decorative.
3. **Detail tables at the bottom** — for users who want to interrogate specific rows. Never the entry point.

**What this platform avoids:** chart clutter (more charts = less insight), duplicate charts (two charts showing the same metric from different angles), and drillthrough for its own sake (every click should earn its keep).

### Caching and Revalidation

**Build-time static generation (this platform):** Next.js reads the JSON snapshot at build time and generates static HTML. Zero runtime cost, instant page loads, no staleness risk during a session.

**Revalidation strategies for dynamic dashboards:**
- **Time-based revalidation** (`revalidate: 3600`): Next.js caches the page and rebuilds it when a request arrives after 1 hour
- **On-demand revalidation**: a webhook triggers a rebuild when new data lands
- **Edge caching**: a CDN serves cached pages globally and invalidates when the origin pushes a new version

**The static snapshot trade-off:** data is as fresh as the last scheduled pipeline run (weekly here). For a live retail dashboard you'd use time-based revalidation at hourly granularity backed by a queryable edge database (Cloudflare D1, Neon, PlanetScale).

---

## Data Observability

### Data Observability vs Data Testing

| | Data Testing | Data Observability |
|---|---|---|
| **When** | At pipeline run time | Continuously, across time |
| **What** | Schema contracts, value ranges, referential integrity | Freshness, volume anomalies, schema drift, distribution shift |
| **Tools** | dbt tests, Great Expectations | Elementary, Monte Carlo, Soda |
| **Failure mode** | Pipeline fails hard | Alert raised, pipeline continues |

**Key insight:** testing tells you whether your pipeline produced the right output *this run*. Observability tells you whether the *pattern of outputs over time* is healthy. A column that was always 100% populated and is now 40% null passes a `not_null` test if the threshold isn't set, but observability catches the anomaly.

### Freshness and Anomaly Detection

**Source freshness:** dbt can check when a source table was last updated. If `bronze.fact_sales._load_timestamp` hasn't advanced in 48 hours, dbt raises a warning. This catches upstream pipeline failures before they silently propagate stale data to consumers.

**Volume anomalies (Elementary):** Elementary tracks row counts per model per run. If `fct_sales` had 54,936 rows last Monday and has 0 rows this Monday, it flags an anomaly. This catches silent failures — a bug that produces an empty table without raising an error.

**Calibration period:** Elementary's anomaly detection uses a rolling baseline (14 days by default in this platform). The first 14 runs establish what "normal" looks like; anomaly alerts only fire once the baseline is stable. This is why the first few Elementary reports show no anomaly alerts.

### Elementary in This Platform

Elementary runs as a dbt package — its incremental models (`data_monitoring_metrics`, `dbt_models`, `dbt_run_results`, `dbt_tests`) run as part of every `dbt build` and populate the `staging.elementary_*` schema. The `edr report` CLI then reads from those tables to generate an HTML report.

The `scheduled.yml` pipeline generates the report after every weekly dbt build and uploads it as a 30-day GitHub Actions artifact. To view it: go to a completed "Scheduled Pipeline" workflow run → Artifacts → download `elementary-report-<run_id>`.

---

## Interview Question Bank

A curated set of the questions this project is designed to answer, grouped by domain.

**Architecture**
- Why use a medallion architecture instead of loading directly to a star schema?
- How does the dashboard stay live after the Snowflake trial expires?
- Why DuckDB instead of PostgreSQL for the shadow warehouse?

**dbt and Transformations**
- What is the difference between `ref()` and `source()`?
- When would you use an ephemeral materialisation?
- How does SCD Type 2 work and why is the -1 sentinel important?
- What does a dbt model contract enforce?

**Orchestration**
- What makes a pipeline task idempotent?
- What is astronomer-cosmos and why use it instead of a BashOperator?
- How would you backfill 3 months of historical data safely?

**Storage and Ingestion**
- What is schema-on-read and when is it preferable to schema-on-write?
- Why does COPY INTO require a file format object?
- What are Snowflake micro-partitions and how do they affect query performance?

**CI/CD and Quality**
- What is the difference between CI and CD?
- Why do you test against DuckDB in CI instead of Snowflake?
- What is a merge gate and what problem does it solve?

**Data Quality**
- What is the difference between data testing and data observability?
- What does Elementary's anomaly detection require before it can raise alerts?
- Why is `never average a percentage` a critical rule for data modelling?
