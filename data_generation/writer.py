"""Write generated DataFrames to date-partitioned Parquet files."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

log = logging.getLogger(__name__)

# Fact tables that need year/month partitioning, and the date column to partition on
_FACT_DATE_COLS: dict[str, str] = {
    "fact_sales": "sale_date",
    "fact_inventory_snapshot": "snapshot_date",
    "fact_returns": "return_date",
    "fact_web_events": "event_date",
    "fact_markdown": "week_start_date",
}


def write_all(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Write all dimension and fact tables to Parquet under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, df in tables.items():
        if name in _FACT_DATE_COLS:
            _write_fact(df, name, output_dir, _FACT_DATE_COLS[name])
        else:
            _write_dimension(df, name, output_dir)


def _coerce_mixed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert object columns that contain mixed Python types to all-string.

    Type-drift dirtiness leaves some numeric columns with a mix of int and str
    values (object dtype). PyArrow rejects these as ArrowInvalid. Converting to
    all-string preserves the dirtiness in the raw Parquet so the silver layer
    can cast them. All other columns are left untouched.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype != object:
            continue
        non_null = df[col].dropna()
        if len(non_null) == 0:
            continue
        if len({type(v) for v in non_null}) > 1:
            df[col] = df[col].apply(lambda v: str(v) if pd.notna(v) else None)
    return df


def _write_dimension(df: pd.DataFrame, name: str, output_dir: Path) -> None:
    out_path = output_dir / name / f"{name}.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(_coerce_mixed_columns(df), preserve_index=False)
    pq.write_table(table, out_path, compression="snappy")
    log.info("  %s → %s (%d rows)", name, out_path.relative_to(output_dir), len(df))


def _write_fact(df: pd.DataFrame, name: str, output_dir: Path, date_col: str) -> None:
    df = _coerce_mixed_columns(df)
    df["_dt"] = pd.to_datetime(df[date_col])
    df["_year"] = df["_dt"].dt.year
    df["_month"] = df["_dt"].dt.month

    total_rows = 0
    for (year, month), chunk in df.groupby(["_year", "_month"]):
        part = chunk.drop(columns=["_dt", "_year", "_month"])
        out_path = (
            output_dir / name / f"year={year}" / f"month={month:02d}" / f"{name}.parquet"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pandas(part, preserve_index=False)
        pq.write_table(table, out_path, compression="snappy")
        total_rows += len(part)

    log.info("  %s → %s/year=*/month=*/ (%d rows)", name, name, total_rows)
