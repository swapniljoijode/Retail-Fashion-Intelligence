"""CLI entry point for synthetic data generation.

Usage:
    python -m data_generation.main --volume small
    python -m data_generation.main --volume large
    python -m data_generation.main --volume small --seed 99 --output-dir ./my_output
"""
from __future__ import annotations

import argparse
import dataclasses
import logging
import time
from pathlib import Path

import numpy as np

from data_generation.config import CONFIGS
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fashion retail data")
    parser.add_argument(
        "--volume", choices=["test", "small", "large"], default="small",
        help="Data volume profile (default: small)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Override the profile's random seed",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data_generation/output"),
        help="Root output directory (default: data_generation/output)",
    )
    args = parser.parse_args()

    config = CONFIGS[args.volume]
    if args.seed is not None:
        config = dataclasses.replace(config, seed=args.seed)

    rng = np.random.default_rng(config.seed)

    log.info("Volume=%s  seed=%d  %s → %s", config.name, config.seed, config.start_date, config.end_date)
    t0 = time.perf_counter()

    # ── Dimensions ────────────────────────────────────────────────────────────
    log.info("Generating dimensions …")
    dims: dict = {
        "dim_date":      generate_dim_date(config),
        "dim_product":   generate_dim_product(config, rng),
        "dim_store":     generate_dim_store(config, rng),
        "dim_customer":  generate_dim_customer(config, rng),
        "dim_channel":   generate_dim_channel(),
        "dim_promotion": generate_dim_promotion(config, rng),
    }
    log.info("  dim_date      %6d rows", len(dims["dim_date"]))
    log.info("  dim_product   %6d rows  (incl. SCD versions)", len(dims["dim_product"]))
    log.info("  dim_store     %6d rows", len(dims["dim_store"]))
    log.info("  dim_customer  %6d rows  (incl. SCD versions)", len(dims["dim_customer"]))
    log.info("  dim_channel   %6d rows", len(dims["dim_channel"]))
    log.info("  dim_promotion %6d rows", len(dims["dim_promotion"]))

    # ── Facts — order matters: inventory and returns depend on sales ──────────
    log.info("Generating fact_sales …")
    fact_sales = generate_fact_sales(config, rng, dims)
    log.info("  fact_sales    %6d rows", len(fact_sales))

    log.info("Generating fact_inventory_snapshot …")
    fact_inv = generate_fact_inventory_snapshot(config, rng, dims, fact_sales)
    log.info("  fact_inventory_snapshot  %6d rows", len(fact_inv))

    log.info("Generating fact_returns …")
    fact_ret = generate_fact_returns(config, rng, dims, fact_sales)
    log.info("  fact_returns  %6d rows", len(fact_ret))

    log.info("Generating fact_web_events …")
    fact_web = generate_fact_web_events(config, rng, dims)
    log.info("  fact_web_events  %6d rows", len(fact_web))

    log.info("Generating fact_markdown …")
    fact_md = generate_fact_markdown(config, rng, dims, fact_sales)
    log.info("  fact_markdown %6d rows", len(fact_md))

    facts: dict = {
        "fact_sales": fact_sales,
        "fact_inventory_snapshot": fact_inv,
        "fact_returns": fact_ret,
        "fact_web_events": fact_web,
        "fact_markdown": fact_md,
    }

    # ── Dirtiness ─────────────────────────────────────────────────────────────
    log.info("Applying controlled dirtiness …")
    all_tables = {**dims, **facts}
    dirty = apply_dirtiness(all_tables, rng)

    # ── Write Parquet ─────────────────────────────────────────────────────────
    log.info("Writing Parquet to %s …", args.output_dir)
    write_all(dirty, args.output_dir)

    elapsed = time.perf_counter() - t0
    total_rows = sum(len(df) for df in dirty.values())
    log.info("Done in %.1f s — %d total rows written.", elapsed, total_rows)


if __name__ == "__main__":
    main()
