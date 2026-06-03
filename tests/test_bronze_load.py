"""Tests for DuckDB bronze layer ingestion.

Fixture setup (session-scoped, runs once):
  1. Generate TEST-volume data in memory (5 styles, 3 stores, 50 customers, 31 days).
  2. Apply dirtiness and write Parquet to a temporary directory.
  3. Run bronze_load once with reset=True.

Tests then verify schema, row counts, lineage metadata, and append-only behaviour.
"""
from __future__ import annotations

import numpy as np
import pytest
import duckdb

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
from ingestion.bronze_load import _TABLE_GLOBS, run_bronze_load


# ── Session fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def bronze_env(tmp_path_factory):
    """Generate TEST Parquet, run bronze_load once, expose results for all tests."""
    rng = np.random.default_rng(TEST.seed)

    dims = {
        "dim_date":      generate_dim_date(TEST),
        "dim_product":   generate_dim_product(TEST, rng),
        "dim_store":     generate_dim_store(TEST, rng),
        "dim_customer":  generate_dim_customer(TEST, rng),
        "dim_channel":   generate_dim_channel(),
        "dim_promotion": generate_dim_promotion(TEST, rng),
    }

    # Facts must be generated in dependency order: inventory/returns/markdown all
    # consume fact_sales, so generate that first with the same rng.
    fact_sales = generate_fact_sales(TEST, rng, dims)

    all_tables = {
        **dims,
        "fact_sales":              fact_sales,
        "fact_inventory_snapshot": generate_fact_inventory_snapshot(TEST, rng, dims, fact_sales),
        "fact_returns":            generate_fact_returns(TEST, rng, dims, fact_sales),
        "fact_web_events":         generate_fact_web_events(TEST, rng, dims),
        "fact_markdown":           generate_fact_markdown(TEST, rng, dims, fact_sales),
    }

    dirty = apply_dirtiness(all_tables, rng)

    source_dir = tmp_path_factory.mktemp("bronze_source")
    db_path = str(tmp_path_factory.mktemp("bronze_db") / "fashion_retail.duckdb")

    write_all(dirty, source_dir)
    log_rows = run_bronze_load(source_dir, db_path, reset=True)

    return {
        "source_dir": source_dir,
        "db_path": db_path,
        "log_rows": log_rows,
        "source_tables": dirty,
    }


@pytest.fixture(scope="session")
def bconn(bronze_env):
    """Read-only DuckDB connection to the bronze database."""
    conn = duckdb.connect(bronze_env["db_path"], read_only=True)
    yield conn
    conn.close()


# ── Schema tests ──────────────────────────────────────────────────────────────


class TestBronzeSchema:
    def test_all_11_tables_exist(self, bconn):
        tables = {
            row[0]
            for row in bconn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'bronze' AND table_type = 'BASE TABLE'"
            ).fetchall()
        }
        for expected in _TABLE_GLOBS:
            assert expected in tables, f"Missing bronze table: {expected}"

    def test_ingestion_log_exists(self, bconn):
        tables = {
            row[0]
            for row in bconn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'bronze'"
            ).fetchall()
        }
        assert "ingestion_log" in tables

    def test_source_file_column_present(self, bconn):
        for tbl in _TABLE_GLOBS:
            cols = [row[0] for row in bconn.execute(f"DESCRIBE bronze.{tbl}").fetchall()]
            assert "_source_file" in cols, f"_source_file missing from bronze.{tbl}"

    def test_load_timestamp_column_present(self, bconn):
        for tbl in _TABLE_GLOBS:
            cols = [row[0] for row in bconn.execute(f"DESCRIBE bronze.{tbl}").fetchall()]
            assert "_load_timestamp" in cols, f"_load_timestamp missing from bronze.{tbl}"


# ── Row-count tests ───────────────────────────────────────────────────────────


class TestBronzeRowCounts:
    def test_all_tables_non_empty(self, bconn):
        for tbl in _TABLE_GLOBS:
            count = bconn.execute(f"SELECT COUNT(*) FROM bronze.{tbl}").fetchone()[0]
            assert count > 0, f"bronze.{tbl} is empty after initial load"

    def test_source_to_bronze_counts_match(self, bronze_env):
        for row in bronze_env["log_rows"]:
            assert row["count_match"], (
                f"{row['table_name']}: source_rows={row['source_rows']} "
                f"!= loaded_rows={row['loaded_rows']}"
            )

    def test_all_runs_succeeded(self, bronze_env):
        for row in bronze_env["log_rows"]:
            assert row["status"] == "SUCCESS", (
                f"{row['table_name']} status={row['status']} "
                f"error={row.get('error_message')}"
            )

    def test_ingestion_log_has_one_entry_per_table(self, bconn):
        count = bconn.execute(
            "SELECT COUNT(*) FROM bronze.ingestion_log"
        ).fetchone()[0]
        assert count == len(_TABLE_GLOBS)

    def test_log_source_rows_match_source_tables(self, bronze_env, bconn):
        """Row counts in ingestion_log match the actual source DataFrames."""
        for tbl, df in bronze_env["source_tables"].items():
            if tbl not in _TABLE_GLOBS:
                continue
            logged = bconn.execute(
                f"SELECT source_rows FROM bronze.ingestion_log WHERE table_name = '{tbl}'"
            ).fetchone()[0]
            assert logged == len(df), (
                f"{tbl}: ingestion_log.source_rows={logged} != len(df)={len(df)}"
            )


# ── Lineage / metadata tests ──────────────────────────────────────────────────


class TestBronzeLineage:
    def test_source_file_never_null(self, bconn):
        for tbl in _TABLE_GLOBS:
            nulls = bconn.execute(
                f"SELECT COUNT(*) FROM bronze.{tbl} WHERE _source_file IS NULL"
            ).fetchone()[0]
            assert nulls == 0, f"{nulls} NULL _source_file rows in bronze.{tbl}"

    def test_load_timestamp_never_null(self, bconn):
        for tbl in _TABLE_GLOBS:
            nulls = bconn.execute(
                f"SELECT COUNT(*) FROM bronze.{tbl} WHERE _load_timestamp IS NULL"
            ).fetchone()[0]
            assert nulls == 0, f"{nulls} NULL _load_timestamp rows in bronze.{tbl}"

    def test_source_file_ends_with_parquet(self, bconn):
        for tbl in _TABLE_GLOBS:
            sample = bconn.execute(
                f"SELECT _source_file FROM bronze.{tbl} LIMIT 1"
            ).fetchone()[0]
            assert sample.endswith(".parquet"), (
                f"Unexpected _source_file value '{sample}' in bronze.{tbl}"
            )

    def test_all_rows_share_one_run_id_per_table(self, bconn):
        """First load should yield exactly one distinct _load_timestamp per table."""
        for tbl in _TABLE_GLOBS:
            distinct = bconn.execute(
                f"SELECT COUNT(DISTINCT _load_timestamp) FROM bronze.{tbl}"
            ).fetchone()[0]
            assert distinct == 1, (
                f"Expected 1 distinct _load_timestamp in bronze.{tbl}, got {distinct}"
            )


# ── Append-only / idempotency tests ──────────────────────────────────────────
# These tests open read-write connections and must not share the session-scoped
# read-only bconn fixture.  They get their own isolated database.


@pytest.fixture(scope="class")
def appendable_db(bronze_env, tmp_path_factory):
    """Fresh writable DB seeded from the shared Parquet output."""
    db_path = str(tmp_path_factory.mktemp("append_db") / "fashion_retail.duckdb")
    run_bronze_load(bronze_env["source_dir"], db_path, reset=True)
    return {"source_dir": bronze_env["source_dir"], "db_path": db_path}


class TestBronzeAppendOnly:
    def test_second_load_doubles_row_count(self, appendable_db):
        """A second load appends — bronze is never deduplicated in the raw layer."""
        source_dir = appendable_db["source_dir"]
        db_path = appendable_db["db_path"]

        conn = duckdb.connect(db_path)
        counts_before = {
            tbl: conn.execute(f"SELECT COUNT(*) FROM bronze.{tbl}").fetchone()[0]
            for tbl in _TABLE_GLOBS
        }
        conn.close()

        run_bronze_load(source_dir, db_path, reset=False)

        conn = duckdb.connect(db_path)
        for tbl in _TABLE_GLOBS:
            count_after = conn.execute(f"SELECT COUNT(*) FROM bronze.{tbl}").fetchone()[0]
            assert count_after == counts_before[tbl] * 2, (
                f"{tbl}: expected {counts_before[tbl] * 2} after second load, got {count_after}"
            )
        conn.close()

    def test_reset_clears_then_reloads(self, appendable_db):
        """--reset drops tables and reloads to the original single-load count."""
        source_dir = appendable_db["source_dir"]
        db_path = appendable_db["db_path"]

        # Previous test doubled rows; --reset should restore the baseline.
        log_rows = run_bronze_load(source_dir, db_path, reset=True)

        conn = duckdb.connect(db_path, read_only=True)
        for row in log_rows:
            tbl = row["table_name"]
            count = conn.execute(f"SELECT COUNT(*) FROM bronze.{tbl}").fetchone()[0]
            assert count == row["source_rows"], (
                f"{tbl}: after reset expected {row['source_rows']}, got {count}"
            )
        conn.close()
