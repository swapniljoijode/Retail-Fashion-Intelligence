from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class VolumeConfig:
    name: str
    seed: int
    start_date: date
    end_date: date
    n_styles: int           # unique product styles before size expansion
    n_stores: int
    n_customers: int
    n_promotions: int
    avg_daily_orders: int   # base daily order volume before seasonal adjustment


# One month, tiny counts — used exclusively by pytest for speed
TEST = VolumeConfig(
    name="test",
    seed=42,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    n_styles=5,
    n_stores=3,
    n_customers=50,
    n_promotions=2,
    avg_daily_orders=10,
)

# One year — fast DuckDB iteration
SMALL = VolumeConfig(
    name="small",
    seed=42,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    n_styles=25,
    n_stores=8,
    n_customers=300,
    n_promotions=8,
    avg_daily_orders=50,
)

# Two years — Snowflake trial build
LARGE = VolumeConfig(
    name="large",
    seed=42,
    start_date=date(2023, 1, 1),
    end_date=date(2024, 12, 31),
    n_styles=100,
    n_stores=30,
    n_customers=2000,
    n_promotions=20,
    avg_daily_orders=250,
)

CONFIGS: dict[str, VolumeConfig] = {"test": TEST, "small": SMALL, "large": LARGE}
