"""
Fashion Retail Intelligence — End-to-End Pipeline DAG

Pipeline stages
───────────────
  generate_data      Generate synthetic Parquet (small volume, fixed seed 42).
  load_bronze        Load Parquet into DuckDB bronze layer (reset for idempotency).
  install_dbt_deps   Run `dbt deps` to pull dbt-expectations package.
  [dbt_fashion_retail] Cosmos DbtTaskGroup — one Airflow task per model/test across
                     staging → intermediate → marts.  Retries isolated per model.
  export_snapshot    COPY gold marts to data/served/*.parquet — the static snapshot
                     the Phase 8 dashboard will read.
  upload_r2          (conditional) Upload served/ to Cloudflare R2 if credentials
                     are present in the environment.

Design principles
─────────────────
  • Every task is idempotent: reruns produce identical state, no side effects.
  • Bronze load uses --reset so duplicate Parquet files never accumulate.
  • dbt build (run + test) is idempotent by design.
  • The served snapshot is fully overwritten on each run.
  • The R2 upload is skipped gracefully when credentials are absent — useful for
    local/CI runs where cloud credentials may not be available.

Schedule: weekly (@weekly) — adjust via AIRFLOW_VAR_PIPELINE_SCHEDULE if needed.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from cosmos import (
    DbtTaskGroup,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.config import LoadMode

log = logging.getLogger(__name__)

# ── Container-internal paths ──────────────────────────────────────────────────
# All paths are resolved inside the Docker container.
# On the host, the data/ directory is bind-mounted to /opt/airflow/data.

_ROOT = Path("/opt/airflow")
_DATA = _ROOT / "data"
_GENERATED = _DATA / "generated"
_SERVED = _DATA / "served"
_DB = _DATA / "fashion_retail.duckdb"
_DBT = _ROOT / "dbt"

# ── DAG defaults ──────────────────────────────────────────────────────────────

_DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# ── Cosmos configuration ──────────────────────────────────────────────────────

_project_config = ProjectConfig(
    dbt_project_path=_DBT,
    project_name="fashion_retail",
)

_profile_config = ProfileConfig(
    profile_name="fashion_retail",
    target_name="duckdb",
    # profiles.yml is bind-mounted from docker/airflow/dbt_profiles.yml
    profiles_yml_filepath=_DBT / "profiles.yml",
)

_execution_config = ExecutionConfig(
    # pip --user installs land in ~/.local/bin inside the container
    dbt_executable_path=Path("/home/airflow/.local/bin/dbt"),
)

_render_config = RenderConfig(
    load_method=LoadMode.DBT_LS,
    select=["path:models/staging", "path:models/intermediate", "path:models/marts"],
)

# ── Task callables ────────────────────────────────────────────────────────────


def _generate_data(**_context) -> None:
    """Generate small-volume synthetic data to _GENERATED."""
    import subprocess
    import sys

    _GENERATED.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_generation.main",
            "--volume",
            "small",
            "--output-dir",
            str(_GENERATED),
        ],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        log.info(result.stdout)
    if result.returncode != 0:
        log.error(result.stderr)
        raise RuntimeError(f"data_generation.main failed (exit {result.returncode})")


def _load_bronze(**_context) -> None:
    """Load Parquet into DuckDB bronze layer. --reset ensures idempotency."""
    from ingestion.bronze_load import run_bronze_load

    log_rows = run_bronze_load(
        source_dir=_GENERATED,
        db_path=str(_DB),
        reset=True,
    )
    failed = [r for r in log_rows if r["status"] != "SUCCESS"]
    if failed:
        raise RuntimeError(
            f"Bronze load failed for: {[r['table_name'] for r in failed]}"
        )


def _export_snapshot(**_context) -> None:
    """COPY gold mart tables from DuckDB to data/served/*.parquet."""
    import duckdb

    _SERVED.mkdir(parents=True, exist_ok=True)

    marts = [
        "dim_date",
        "dim_product",
        "dim_store",
        "dim_customer",
        "dim_channel",
        "dim_promotion",
        "fct_sales",
        "fct_inventory_snapshot",
        "fct_returns",
        "fct_web_events",
        "fct_markdown",
    ]

    conn = duckdb.connect(str(_DB), read_only=True)
    try:
        for mart in marts:
            out_path = _SERVED / f"{mart}.parquet"
            conn.execute(
                f"COPY (SELECT * FROM marts.{mart}) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION SNAPPY)"
            )
            log.info("Exported marts.%s → %s", mart, out_path)
    finally:
        conn.close()

    log.info("Snapshot complete: %d tables written to %s", len(marts), _SERVED)


def _r2_credentials_present(**_context) -> bool:
    """Return True only when all R2 env vars are populated.

    Used as a ShortCircuitOperator guard — the upload_r2 task is skipped
    gracefully when running locally without cloud credentials.
    """
    required = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        log.info("R2 credentials not set (%s) — skipping upload.", missing)
        return False
    return True


def _upload_r2(**_context) -> None:
    """Upload the served snapshot to Cloudflare R2 fashion-retail-served bucket."""
    from ingestion.upload_r2 import upload_parquet

    bucket = os.environ.get("R2_SERVED_BUCKET", "fashion-retail-served")
    upload_parquet(input_dir=_SERVED, bucket=bucket, prefix="snapshot")


# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="fashion_retail_pipeline",
    description="End-to-end medallion pipeline: generate → bronze → dbt → snapshot",
    default_args=_DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@weekly",
    catchup=False,
    max_active_runs=1,
    tags=["fashion-retail", "medallion", "dbt", "cosmos"],
    doc_md=__doc__,
) as dag:

    # ── Stage 1: generate synthetic data ─────────────────────────────────────
    generate_data = PythonOperator(
        task_id="generate_data",
        python_callable=_generate_data,
        doc_md="Generate small-volume Parquet output using seed=42 (reproducible).",
    )

    # ── Stage 2: load DuckDB bronze layer ────────────────────────────────────
    load_bronze = PythonOperator(
        task_id="load_bronze",
        python_callable=_load_bronze,
        doc_md=(
            "Reset and reload all 11 bronze tables from Parquet. "
            "reset=True makes this task safe to rerun."
        ),
    )

    # ── Stage 3: install dbt packages ────────────────────────────────────────
    install_dbt_deps = BashOperator(
        task_id="install_dbt_deps",
        bash_command="cd /opt/airflow/dbt && dbt deps --profiles-dir . --no-partial-parse",
        doc_md="Pull dbt-expectations (metaplane) from the dbt Hub before running models.",
    )

    # ── Stage 4: dbt run + test via Cosmos ───────────────────────────────────
    dbt_group = DbtTaskGroup(
        group_id="dbt_fashion_retail",
        project_config=_project_config,
        profile_config=_profile_config,
        execution_config=_execution_config,
        render_config=_render_config,
        operator_args={
            "retries": 1,
            "retry_delay": timedelta(minutes=2),
        },
    )

    # ── Stage 5: export served snapshot ──────────────────────────────────────
    export_snapshot = PythonOperator(
        task_id="export_snapshot",
        python_callable=_export_snapshot,
        doc_md="COPY all 11 gold mart tables from DuckDB to data/served/*.parquet.",
    )

    # ── Stage 6: upload to R2 (conditional) ──────────────────────────────────
    check_r2_creds = ShortCircuitOperator(
        task_id="check_r2_credentials",
        python_callable=_r2_credentials_present,
        doc_md="Skip the R2 upload if cloud credentials are not set in the environment.",
    )

    upload_r2 = PythonOperator(
        task_id="upload_r2",
        python_callable=_upload_r2,
        doc_md="Upload data/served/*.parquet to Cloudflare R2 fashion-retail-served bucket.",
    )

    # ── Task dependencies ─────────────────────────────────────────────────────
    (
        generate_data
        >> load_bronze
        >> install_dbt_deps
        >> dbt_group
        >> export_snapshot
        >> check_r2_creds
        >> upload_r2
    )
