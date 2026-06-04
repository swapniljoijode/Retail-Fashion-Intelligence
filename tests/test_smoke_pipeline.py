"""
Integration smoke test — full end-to-end pipeline on TEST volume.

Runs once per pytest session (session-scoped fixture) and covers:
  1. Synthetic data generation (TEST volume, seed=42)
  2. Bronze ingestion (DuckDB, --reset)
  3. dbt build (staging → intermediate → marts, DuckDB target)
  4. Gold mart assertions (non-empty tables, resolved surrogate keys)

Marked @pytest.mark.integration so it is excluded from the default fast run
and included in the CI / Docker full run.

Run only the smoke test:
    uv run pytest tests/test_smoke_pipeline.py -v

Run everything including smoke:
    uv run pytest tests/ -v -m ''
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import duckdb
import numpy as np
import pytest

from data_generation.config import TEST
from data_generation.dirtiness import apply_dirtiness
from data_generation.generators.dimensions import (
    generate_dim_channel,
    generate_dim_customer,
    generate_dim_date,
    generate_dim_product,
    generate_dim_promotion,
    generate_dim_store,
)
from data_generation.generators.facts import (
    generate_fact_inventory_snapshot,
    generate_fact_markdown,
    generate_fact_returns,
    generate_fact_sales,
    generate_fact_web_events,
)
from data_generation.writer import write_all
from ingestion.bronze_load import run_bronze_load

pytestmark = pytest.mark.integration

_DBT_DIR = Path(__file__).parent.parent / "dbt"
_DBT_PACKAGES = _DBT_DIR / "dbt_packages"

_GOLD_DIMS = [
    "dim_date",
    "dim_product",
    "dim_store",
    "dim_customer",
    "dim_channel",
    "dim_promotion",
]
_GOLD_FACTS = [
    "fct_sales",
    "fct_inventory_snapshot",
    "fct_returns",
    "fct_web_events",
    "fct_markdown",
]
_ALL_MARTS = _GOLD_DIMS + _GOLD_FACTS


# ── helpers ───────────────────────────────────────────────────────────────────


def _dbt_cmd() -> list[str]:
    """Return the dbt invocation prefix for the current environment."""
    if shutil.which("uv"):
        return ["uv", "run", "dbt"]
    if shutil.which("dbt"):
        return ["dbt"]
    pytest.skip("dbt not found — run: uv sync --extra dbt")


def _run_dbt(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*_dbt_cmd(), *args],
        capture_output=True,
        text=True,
        check=check,
    )


# ── session fixture ───────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def pipeline(tmp_path_factory):
    """Run the complete pipeline once; expose db_path and run metadata."""

    # ── 1. Generate TEST volume Parquet ──────────────────────────────────────
    rng = np.random.default_rng(TEST.seed)
    dims = {
        "dim_date": generate_dim_date(TEST),
        "dim_product": generate_dim_product(TEST, rng),
        "dim_store": generate_dim_store(TEST, rng),
        "dim_customer": generate_dim_customer(TEST, rng),
        "dim_channel": generate_dim_channel(),
        "dim_promotion": generate_dim_promotion(TEST, rng),
    }
    fact_sales = generate_fact_sales(TEST, rng, dims)
    all_tables = {
        **dims,
        "fact_sales": fact_sales,
        "fact_inventory_snapshot": generate_fact_inventory_snapshot(
            TEST, rng, dims, fact_sales
        ),
        "fact_returns": generate_fact_returns(TEST, rng, dims, fact_sales),
        "fact_web_events": generate_fact_web_events(TEST, rng, dims),
        "fact_markdown": generate_fact_markdown(TEST, rng, dims, fact_sales),
    }
    dirty = apply_dirtiness(all_tables, rng)

    parquet_dir = tmp_path_factory.mktemp("smoke_parquet")
    db_dir = tmp_path_factory.mktemp("smoke_db")
    db_path = str(db_dir / "fashion_retail.duckdb")

    write_all(dirty, parquet_dir)

    # ── 2. Bronze ingestion ───────────────────────────────────────────────────
    log_rows = run_bronze_load(parquet_dir, db_path, reset=True)

    # ── 3. Write a temp dbt profiles.yml pointing at the test DuckDB ─────────
    profiles_dir = tmp_path_factory.mktemp("smoke_profiles")
    (profiles_dir / "profiles.yml").write_text(
        f"fashion_retail:\n"
        f"  target: duckdb\n"
        f"  outputs:\n"
        f"    duckdb:\n"
        f"      type: duckdb\n"
        f"      path: {db_path}\n"
        f"      threads: 4\n"
    )

    # ── 4. dbt deps (skip if dbt_packages already present from dev work) ──────
    if not _DBT_PACKAGES.exists():
        _run_dbt(
            [
                "deps",
                "--project-dir",
                str(_DBT_DIR),
                "--profiles-dir",
                str(profiles_dir),
            ],
            check=True,
        )

    # ── 5. dbt build — run + test all layers ─────────────────────────────────
    dbt_result = _run_dbt(
        [
            "build",
            "--project-dir",
            str(_DBT_DIR),
            "--profiles-dir",
            str(profiles_dir),
            "--target",
            "duckdb",
            "--no-partial-parse",
        ]
    )

    return {
        "db_path": db_path,
        "log_rows": log_rows,
        "dbt_returncode": dbt_result.returncode,
        "dbt_stdout": dbt_result.stdout,
        "dbt_stderr": dbt_result.stderr,
        "source_tables": dirty,
    }


# ── Test classes ──────────────────────────────────────────────────────────────


class TestSmokeGenerate:
    """Verify data generation and bronze ingestion completed cleanly."""

    def test_all_tables_loaded(self, pipeline):
        assert len(pipeline["log_rows"]) == 11

    def test_no_bronze_errors(self, pipeline):
        failed = [r for r in pipeline["log_rows"] if r["status"] != "SUCCESS"]
        assert not failed, f"Bronze load errors: {[r['table_name'] for r in failed]}"

    def test_bronze_row_counts_positive(self, pipeline):
        for row in pipeline["log_rows"]:
            assert row["source_rows"] > 0, f"{row['table_name']} has 0 source rows"

    def test_source_bronze_counts_match(self, pipeline):
        for row in pipeline["log_rows"]:
            assert row["count_match"], (
                f"{row['table_name']}: source {row['source_rows']} "
                f"!= bronze {row['loaded_rows']}"
            )


class TestSmokeDbtBuild:
    """dbt build (run + test) must pass with zero failures."""

    def test_dbt_exits_zero(self, pipeline):
        assert pipeline["dbt_returncode"] == 0, (
            "dbt build failed.\n"
            f"STDOUT:\n{pipeline['dbt_stdout'][-3000:]}\n"
            f"STDERR:\n{pipeline['dbt_stderr'][-1000:]}"
        )

    def test_dbt_reports_no_errors(self, pipeline):
        # dbt build summary line: "Done. PASS=N WARN=0 ERROR=0 SKIP=0"
        assert (
            "ERROR=0" in pipeline["dbt_stdout"]
        ), "dbt output shows errors. Check pipeline['dbt_stdout'] for details."


class TestSmokeGoldLayer:
    """Gold mart tables must exist, be non-empty, and have correct structure."""

    def test_all_mart_tables_exist(self, pipeline):
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'marts'"
            ).fetchall()
        }
        conn.close()
        missing = [m for m in _ALL_MARTS if m not in tables]
        assert not missing, f"Missing gold mart tables: {missing}"

    def test_all_dim_tables_non_empty(self, pipeline):
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        for dim in _GOLD_DIMS:
            count = conn.execute(f"SELECT COUNT(*) FROM marts.{dim}").fetchone()[0]
            assert count > 0, f"marts.{dim} is empty after dbt build"
        conn.close()

    def test_all_fact_tables_non_empty(self, pipeline):
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        for fct in _GOLD_FACTS:
            count = conn.execute(f"SELECT COUNT(*) FROM marts.{fct}").fetchone()[0]
            assert count > 0, f"marts.{fct} is empty after dbt build"
        conn.close()

    def test_fct_sales_product_keys_resolved(self, pipeline):
        """SCD2 join must resolve every product_key — no -1 sentinel rows."""
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        unresolved = conn.execute(
            "SELECT COUNT(*) FROM marts.fct_sales WHERE product_key = -1"
        ).fetchone()[0]
        conn.close()
        assert unresolved == 0, (
            f"{unresolved} fct_sales rows have unresolved product_key (-1). "
            "Check the SCD2 date-range join in fct_sales.sql."
        )

    def test_fct_sales_customer_keys_resolved(self, pipeline):
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        unresolved = conn.execute(
            "SELECT COUNT(*) FROM marts.fct_sales WHERE customer_key = -1"
        ).fetchone()[0]
        conn.close()
        assert (
            unresolved == 0
        ), f"{unresolved} fct_sales rows have unresolved customer_key (-1)."

    def test_dim_product_contracts_enforced(self, pipeline):
        """Contract enforcement: product_key must be unique (enforced in dim_product)."""
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        dupes = conn.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT product_key FROM marts.dim_product "
            "  GROUP BY product_key HAVING COUNT(*) > 1"
            ")"
        ).fetchone()[0]
        conn.close()
        assert dupes == 0, f"{dupes} duplicate product_keys in marts.dim_product"

    def test_gold_row_counts_match_staging(self, pipeline):
        """Mart fact row counts must equal staging counts (no rows dropped by dbt)."""
        conn = duckdb.connect(pipeline["db_path"], read_only=True)
        pairs = [
            ("staging.stg_bronze__fact_sales", "marts.fct_sales"),
            ("staging.stg_bronze__fact_returns", "marts.fct_returns"),
            ("staging.stg_bronze__fact_markdown", "marts.fct_markdown"),
        ]
        for stg, mart in pairs:
            stg_count = conn.execute(f"SELECT COUNT(*) FROM {stg}").fetchone()[0]
            mart_count = conn.execute(f"SELECT COUNT(*) FROM {mart}").fetchone()[0]
            assert (
                stg_count == mart_count
            ), f"{mart}: expected {stg_count} rows (same as {stg}), got {mart_count}"
        conn.close()
