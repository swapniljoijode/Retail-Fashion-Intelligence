"""
Controlled data quality issues injected into raw output.

Every issue here is intentional and documented so that:
  1. The silver dbt layer knows exactly what to clean and why.
  2. Interview answers about "what does your cleaning layer do?" are precise.

Issues applied:
  dim_customer    - 5 % null region, 4 % null city
  dim_product     - 2 % null color, 8 % inconsistent category casing
  fact_sales      - 3 % type-drifted units_sold (int → string),
                    0.8 % duplicate rows
  fact_returns    - 0.5 % duplicate rows
  fact_inventory  - 2 % type-drifted units_on_hand (int → string)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ── Specification ─────────────────────────────────────────────────────────────

_NULL_SPEC: dict[str, list[tuple[str, float]]] = {
    "dim_customer": [("region", 0.05), ("city", 0.04)],
    "dim_product": [("color", 0.02)],
}

_CASING_SPEC: dict[str, list[tuple[str, float]]] = {
    "dim_product": [("category", 0.08)],
}

_TYPE_DRIFT_SPEC: dict[str, list[tuple[str, float]]] = {
    "fact_sales": [("units_sold", 0.03)],
    "fact_inventory_snapshot": [("units_on_hand", 0.02)],
}

_DUPLICATE_SPEC: dict[str, float] = {
    "fact_sales": 0.008,
    "fact_returns": 0.005,
}


# ── Applicators ───────────────────────────────────────────────────────────────


def apply_dirtiness(
    tables: dict[str, pd.DataFrame],
    rng: np.random.Generator,
) -> dict[str, pd.DataFrame]:
    """Return a new dict of DataFrames with all controlled dirtiness applied."""
    dirty = {name: df.copy() for name, df in tables.items()}

    for table, col_rates in _NULL_SPEC.items():
        if table not in dirty:
            continue
        df = dirty[table]
        for col, rate in col_rates:
            if col not in df.columns:
                continue
            mask = rng.random(len(df)) < rate
            df.loc[mask, col] = None

    for table, col_rates in _CASING_SPEC.items():
        if table not in dirty:
            continue
        df = dirty[table]
        for col, rate in col_rates:
            if col not in df.columns:
                continue
            mask = rng.random(len(df)) < rate
            # Alternate between upper and lower to create inconsistency
            upper_mask = mask & (rng.random(len(df)) < 0.50)
            lower_mask = mask & ~upper_mask
            df.loc[upper_mask, col] = df.loc[upper_mask, col].str.upper()
            df.loc[lower_mask, col] = df.loc[lower_mask, col].str.lower()

    for table, col_rates in _TYPE_DRIFT_SPEC.items():
        if table not in dirty:
            continue
        df = dirty[table]
        for col, rate in col_rates:
            if col not in df.columns:
                continue
            mask = rng.random(len(df)) < rate
            # Cast the drifted rows to object (stores the integer as a string)
            df[col] = df[col].astype(object)
            df.loc[mask, col] = df.loc[mask, col].apply(lambda v: str(v))

    for table, rate in _DUPLICATE_SPEC.items():
        if table not in dirty:
            continue
        df = dirty[table]
        n_dupes = max(1, int(len(df) * rate))
        dupe_indices = rng.choice(len(df), size=n_dupes, replace=False)
        dupes = df.iloc[dupe_indices].copy()
        dirty[table] = pd.concat([df, dupes], ignore_index=True)

    return dirty
