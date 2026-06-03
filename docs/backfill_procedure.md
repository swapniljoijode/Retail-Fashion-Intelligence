# Backfill Procedure

## What is a backfill?

A backfill re-runs a DAG for historical date ranges that were missed — either because the
DAG was not yet deployed during that period, or because a run failed and the data must
be regenerated.  In Airflow, every DAG run is tied to a **logical date** (formerly called
`execution_date`).  Backfilling creates runs for each logical date between the start and
end of the requested range.

## When to backfill in this project

The `fashion_retail_pipeline` DAG is scheduled `@weekly` with `catchup=False`, so Airflow
will not automatically create missed runs.  You would trigger a backfill manually when:

- The DAG is deployed for the first time and you want a historical snapshot.
- A run failed mid-pipeline and partially written data must be cleaned up and reprocessed.
- The synthetic data generator seed or volume is changed and all downstream tables must
  be refreshed.

## Pre-requisites

1. The Airflow stack is running (`make airflow-up`).
2. You have access to a shell in the scheduler container:
   ```bash
   docker compose -f docker/airflow/docker-compose.yml exec airflow-scheduler bash
   ```

## Backfill commands

### Trigger a backfill via the CLI

```bash
# Inside the scheduler container:
airflow dags backfill \
  --start-date 2024-01-01 \
  --end-date   2024-12-31 \
  --reset-dagruns \
  fashion_retail_pipeline
```

| Flag | Purpose |
|---|---|
| `--start-date` | First logical date to backfill (inclusive). |
| `--end-date` | Last logical date to backfill (inclusive). |
| `--reset-dagruns` | Clears any existing run state for the range so tasks can rerun. |
| `--dry-run` | Print the task list without executing — useful to verify the plan. |

### Trigger a single manual run via the UI

1. Open the Airflow UI at [http://localhost:8080](http://localhost:8080).
2. Find the `fashion_retail_pipeline` DAG and click **Trigger DAG**.
3. Optionally set the **Logical date** to a specific past date.
4. Click **Trigger**.

### Trigger a single manual run via the CLI

```bash
airflow dags trigger \
  --exec-date 2024-06-01 \
  fashion_retail_pipeline
```

## Idempotency guarantee

Every task in the pipeline is designed to be rerun safely:

| Task | Idempotency mechanism |
|---|---|
| `generate_data` | Fixed seed=42 + fixed volume produces identical Parquet output. |
| `load_bronze` | `reset=True` drops and recreates all bronze tables before loading. |
| `install_dbt_deps` | `dbt deps` is a no-op if packages are already up-to-date. |
| `dbt_fashion_retail.*` | dbt models are fully deterministic and drop-recreate by default. |
| `export_snapshot` | Overwrites `data/served/*.parquet` completely on every run. |
| `upload_r2` | Boto3 PUT is idempotent — uploading the same key twice replaces the object. |

## Clearing a failed run

If a run is in a `failed` state and you want to rerun only the failed tasks:

```bash
# Clear all tasks from a specific run
airflow tasks clear \
  --start-date 2024-06-01 \
  --end-date   2024-06-01 \
  fashion_retail_pipeline

# Or clear only a specific task
airflow tasks clear \
  --start-date 2024-06-01 \
  --end-date   2024-06-01 \
  --task-ids   load_bronze \
  fashion_retail_pipeline
```

Cleared tasks return to `None` state and will be picked up by the scheduler.

## Monitoring a running backfill

Watch the scheduler logs in real time:

```bash
make airflow-logs
```

Or open the **Grid view** in the Airflow UI to see each logical date's run status
colour-coded across tasks.

## GitLab scheduled pipeline as production proof

Because always-on Airflow hosting is not free, the Airflow instance runs locally for
demonstration.  In the GitLab CI/CD pipeline (Phase 7), a **scheduled pipeline** serves
as the lightweight production-grade orchestration proof:

```yaml
# .gitlab-ci.yml — scheduled pipeline stage
pipeline:scheduled:
  stage: dbt-run:scheduled
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
  script:
    - make seed
    - make bronze-reset
    - make dbt-build
```

This runs the full medallion on DuckDB every night without any hosted Airflow, and can
be configured to run on any schedule from the GitLab UI under **CI/CD → Schedules**.
