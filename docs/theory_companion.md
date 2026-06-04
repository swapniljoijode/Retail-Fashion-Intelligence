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
