"""
Execute snowflake_bronze.sql programmatically using key-pair auth.

Bypasses the Snowsight UI bug ("cannot set properties of undefined")
that occurs when running long multi-statement scripts in the browser.
Executes each statement individually so a failure in one does not
block the rest.

Usage (from project root):
    uv run python -m ingestion.run_snowflake_bronze
"""

import os
import re
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from dotenv import load_dotenv

load_dotenv()


def _load_private_key():
    key_path = Path(os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "snowflake_key.p8"))
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found at {key_path}.")
    pem = key_path.read_bytes()
    passphrase_str = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")
    passphrase = passphrase_str.encode() if passphrase_str else None
    return load_pem_private_key(pem, password=passphrase, backend=default_backend())


def _connect(role: str) -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key=_load_private_key(),
        role=role,
        database=os.environ.get("SNOWFLAKE_DATABASE", "FASHION_RETAIL"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "FASHION_WH"),
    )


def _split_statements(sql: str) -> list[str]:
    """
    Split a SQL file into individual statements on semicolons.
    Handles multi-line statements; strips comment-only blocks.
    """
    # Split on semicolons (end of statement marker)
    raw_parts = re.split(r";[ \t]*(?:\n|$)", sql)
    statements = []
    for part in raw_parts:
        # Remove pure-comment and blank lines to check if anything is left
        lines = [
            ln
            for ln in part.splitlines()
            if ln.strip() and not ln.strip().startswith("--")
        ]
        if lines:
            statements.append(part.strip())
    return statements


def _grant_privileges():
    """Grant schema-level privileges SYSADMIN needs (one-time, idempotent)."""
    print("Granting schema privileges as ACCOUNTADMIN...")
    conn = _connect("ACCOUNTADMIN")
    cur = conn.cursor()
    grants = [
        "GRANT CREATE SCHEMA      ON DATABASE    FASHION_RETAIL        TO ROLE SYSADMIN",
        "GRANT CREATE STAGE       ON SCHEMA      FASHION_RETAIL.PUBLIC TO ROLE SYSADMIN",
        "GRANT CREATE FILE FORMAT ON SCHEMA      FASHION_RETAIL.PUBLIC TO ROLE SYSADMIN",
        "GRANT CREATE TABLE       ON SCHEMA      FASHION_RETAIL.PUBLIC TO ROLE SYSADMIN",
        "GRANT USAGE              ON SCHEMA      FASHION_RETAIL.PUBLIC TO ROLE SYSADMIN",
    ]
    for g in grants:
        try:
            cur.execute(g)
            print(f"  OK  {g}")
        except Exception as e:
            print(f"  SKIP {g[:60]}  ({e})")
    conn.close()
    print()


def _run_bronze_sql(conn) -> tuple[int, int]:
    """Execute every statement in snowflake_bronze.sql; return (ok, errors)."""
    sql_path = Path(__file__).parent / "snowflake_bronze.sql"
    statements = _split_statements(sql_path.read_text(encoding="utf-8"))

    print(f"Executing {sql_path.name}  ({len(statements)} statements)")
    print("-" * 64)

    ok = errors = 0
    cur = conn.cursor()

    for i, stmt in enumerate(statements, 1):
        label = stmt.replace("\n", " ")[:72]
        try:
            cur.execute(stmt)
            rows = cur.fetchall()

            # Print the row-count validation result set
            if cur.description and rows and len(cur.description) == 2:
                col0 = cur.description[0][0].upper()
                col1 = cur.description[1][0].upper()
                if "TABLE" in col0 and "ROW" in col1:
                    print(f"\n  {'TABLE':<38} {'ROWS':>10}")
                    print(f"  {'-'*38} {'-'*10}")
                    for row in rows:
                        print(f"  {str(row[0]):<38} {row[1]:>10,}")
                    print()
                    ok += 1
                    continue

            print(f"  OK  [{i:>2}] {label}")
            ok += 1

        except snowflake.connector.errors.ProgrammingError as e:
            msg = str(e)
            if "already exists" in msg.lower():
                print(f"  --  [{i:>2}] (already exists) {label}")
                ok += 1
            else:
                print(f"  ERR [{i:>2}] {label}")
                print(f"       {msg}")
                errors += 1

    print("-" * 64)
    print(f"  {ok} OK  |  {errors} errors\n")
    return ok, errors


def run_bronze():
    _grant_privileges()

    print("Connecting as SYSADMIN...")
    conn = _connect("SYSADMIN")
    print("Connected.\n")

    ok, errors = _run_bronze_sql(conn)
    conn.close()

    if errors:
        print(f"Completed with {errors} error(s) — review output above.")
    else:
        print("Bronze load complete — all 11 tables loaded from R2.")


if __name__ == "__main__":
    run_bronze()
