"""Load Parquet files from local disk (or R2-mounted path) into DuckDB bronze tables.

Bronze contract:
  - Schema is inferred from the source Parquet — no casting, no cleaning.
  - Two lineage columns are appended to every row:
        _source_file     VARCHAR    — full path of the originating Parquet file
        _load_timestamp  VARCHAR    — ISO-8601 UTC timestamp of the ingestion run
  - Tables live in the 'bronze' schema inside the DuckDB database file.
  - The ingestion_log table records a summary row for every table per run.
  - Bronze is append-only; running twice doubles the row count. Use --reset
    to drop and recreate tables for a clean load during development.

CLI:
    python -m ingestion.bronze_load
    python -m ingestion.bronze_load --source-dir data_generation/output
    python -m ingestion.bronze_load --source-dir data_generation/output --db-path data/bronze.duckdb
    python -m ingestion.bronze_load --reset
"""
from __future__ import annotations

import argparse
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()

# Maps each bronze table name to the glob pattern (relative to source_dir)
# used to read its Parquet files.  Dimensions land as a single file;
# facts are year/month partitioned so the recursive glob is needed.
_TABLE_GLOBS: dict[str, str] = {
    "dim_date":                "dim_date/dim_date.parquet",
    "dim_product":             "dim_product/dim_product.parquet",
    "dim_store":               "dim_store/dim_store.parquet",
    "dim_customer":            "dim_customer/dim_customer.parquet",
    "dim_channel":             "dim_channel/dim_channel.parquet",
    "dim_promotion":           "dim_promotion/dim_promotion.parquet",
    "fact_sales":              "fact_sales/**/*.parquet",
    "fact_inventory_snapshot": "fact_inventory_snapshot/**/*.parquet",
    "fact_returns":            "fact_returns/**/*.parquet",
    "fact_web_events":         "fact_web_events/**/*.parquet",
    "fact_markdown":           "fact_markdown/**/*.parquet",
}


def _connect(db_path: str) -> duckdb.DuckDBPyConnection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(db_path)


def _bootstrap(conn: duckdb.DuckDBPyConnection) -> None:
    """Ensure the bronze schema and ingestion_log table exist."""
    conn.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bronze.ingestion_log (
            run_id          VARCHAR,
            table_name      VARCHAR,
            source_files    INTEGER,
            source_rows     BIGINT,
            loaded_rows     BIGINT,
            count_match     BOOLEAN,
            load_timestamp  VARCHAR,
            status          VARCHAR,
            error_message   VARCHAR
        )
    """)


def _glob_to_duckdb(source_dir: Path, pattern: str) -> str:
    """Build a forward-slash glob string safe for DuckDB on all platforms."""
    return str(source_dir / pattern).replace("\\", "/")


def _load_table(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    source_dir: Path,
    glob_pattern: str,
    run_id: str,
    load_ts: str,
) -> dict:
    """Ingest one table from Parquet into bronze.<table_name>.

    Creates the table on first load (schema derived from Parquet).
    Subsequent loads append rows — bronze is immutable / append-only.
    Returns one ingestion_log row dict.
    """
    glob = _glob_to_duckdb(source_dir, glob_pattern)

    source_rows: int = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{glob}')"
    ).fetchone()[0]

    source_files: int = conn.execute(
        f"SELECT COUNT(DISTINCT filename) FROM read_parquet('{glob}', filename=true)"
    ).fetchone()[0]

    # Create the table on first load using schema-on-read from Parquet.
    # The WHERE FALSE clause builds the schema without inserting any rows.
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS bronze.{table_name} AS
        SELECT
            *,
            filename        AS _source_file,
            '{load_ts}'     AS _load_timestamp
        FROM read_parquet('{glob}', filename=true)
        WHERE FALSE
    """)

    # Append this run's rows with lineage metadata attached.
    conn.execute(f"""
        INSERT INTO bronze.{table_name}
        SELECT
            *,
            filename        AS _source_file,
            '{load_ts}'     AS _load_timestamp
        FROM read_parquet('{glob}', filename=true)
    """)

    loaded_rows: int = conn.execute(
        f"SELECT COUNT(*) FROM bronze.{table_name} WHERE _load_timestamp = '{load_ts}'"
    ).fetchone()[0]

    count_match = source_rows == loaded_rows
    status = "SUCCESS" if count_match else "COUNT_MISMATCH"
    match_symbol = "✓" if count_match else "✗ MISMATCH"

    print(
        f"  {table_name:<35}  src={source_rows:>8,}  loaded={loaded_rows:>8,}  {match_symbol}"
    )

    return {
        "run_id": run_id,
        "table_name": table_name,
        "source_files": source_files,
        "source_rows": source_rows,
        "loaded_rows": loaded_rows,
        "count_match": count_match,
        "load_timestamp": load_ts,
        "status": status,
        "error_message": None,
    }


def _write_log_row(conn: duckdb.DuckDBPyConnection, row: dict) -> None:
    conn.execute(
        """
        INSERT INTO bronze.ingestion_log
            (run_id, table_name, source_files, source_rows, loaded_rows,
             count_match, load_timestamp, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            row["run_id"],
            row["table_name"],
            row["source_files"],
            row["source_rows"],
            row["loaded_rows"],
            row["count_match"],
            row["load_timestamp"],
            row["status"],
            row["error_message"],
        ],
    )


def run_bronze_load(
    source_dir: Path,
    db_path: str,
    reset: bool = False,
) -> list[dict]:
    """Run a full bronze ingestion pass over source_dir into db_path.

    Args:
        source_dir: Root directory produced by data_generation.writer.write_all.
        db_path:    Path to the DuckDB database file (created if absent).
        reset:      Drop and recreate all bronze tables before loading.
                    Use during development; never in production.

    Returns:
        List of ingestion_log row dicts — one per table.
    """
    conn = _connect(db_path)
    _bootstrap(conn)

    if reset:
        for tbl in _TABLE_GLOBS:
            conn.execute(f"DROP TABLE IF EXISTS bronze.{tbl}")
        print("Reset: dropped all bronze tables.\n")

    run_id = str(uuid.uuid4())
    load_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")

    print(f"Bronze load run : {run_id}")
    print(f"Source          : {source_dir}")
    print(f"Target          : {db_path}")
    print(f"Timestamp       : {load_ts}\n")
    print(f"  {'Table':<35}  {'Source':>12}  {'Loaded':>12}  Match")
    print("  " + "-" * 72)

    log_rows: list[dict] = []

    for table_name, glob_pattern in _TABLE_GLOBS.items():
        try:
            row = _load_table(conn, table_name, source_dir, glob_pattern, run_id, load_ts)
        except Exception as exc:
            row = {
                "run_id": run_id,
                "table_name": table_name,
                "source_files": 0,
                "source_rows": 0,
                "loaded_rows": 0,
                "count_match": False,
                "load_timestamp": load_ts,
                "status": "ERROR",
                "error_message": str(exc),
            }
            print(f"  {table_name:<35}  ERROR: {exc}")

        _write_log_row(conn, row)
        log_rows.append(row)

    conn.close()

    issues = [r for r in log_rows if r["status"] != "SUCCESS"]
    print(f"\n{'=' * 72}")
    print(
        f"Run complete — {len(log_rows)} tables, "
        f"{sum(r['source_rows'] for r in log_rows):,} total rows, "
        f"{len(issues)} issues"
    )
    if issues:
        print("Issues:")
        for r in issues:
            msg = r.get("error_message") or ""
            print(f"  {r['table_name']}: {r['status']}  {msg}")

    return log_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Parquet files into DuckDB bronze layer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(os.getenv("BRONZE_SOURCE_DIR", "data_generation/output")),
        help="Root directory containing Parquet output",
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv("DUCKDB_PATH", "data/fashion_retail.duckdb"),
        help="Path to the DuckDB database file",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all bronze tables before loading",
    )
    args = parser.parse_args()

    log_rows = run_bronze_load(args.source_dir, args.db_path, args.reset)

    failed = [r for r in log_rows if r["status"] != "SUCCESS"]
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
