"""Shared pytest fixtures.

The TEST volume (5 styles, 3 stores, 50 customers, 31 days) runs in < 5 s,
keeping the suite fast while exercising all code paths.
"""

from __future__ import annotations

import numpy as np
import pytest

from data_generation.config import TEST
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


@pytest.fixture(scope="session")
def config():
    return TEST


@pytest.fixture(scope="session")
def rng():
    return np.random.default_rng(TEST.seed)


@pytest.fixture(scope="session")
def dims(config, rng):
    return {
        "dim_date": generate_dim_date(config),
        "dim_product": generate_dim_product(config, rng),
        "dim_store": generate_dim_store(config, rng),
        "dim_customer": generate_dim_customer(config, rng),
        "dim_channel": generate_dim_channel(),
        "dim_promotion": generate_dim_promotion(config, rng),
    }


@pytest.fixture(scope="session")
def fact_sales(config, rng, dims):
    return generate_fact_sales(config, rng, dims)


@pytest.fixture(scope="session")
def fact_inventory(config, rng, dims, fact_sales):
    return generate_fact_inventory_snapshot(config, rng, dims, fact_sales)


@pytest.fixture(scope="session")
def fact_returns(config, rng, dims, fact_sales):
    return generate_fact_returns(config, rng, dims, fact_sales)


@pytest.fixture(scope="session")
def fact_web_events(config, rng, dims):
    return generate_fact_web_events(config, rng, dims)


@pytest.fixture(scope="session")
def fact_markdown(config, rng, dims, fact_sales):
    return generate_fact_markdown(config, rng, dims, fact_sales)


@pytest.fixture(scope="session")
def all_facts(fact_sales, fact_inventory, fact_returns, fact_web_events, fact_markdown):
    return {
        "fact_sales": fact_sales,
        "fact_inventory_snapshot": fact_inventory,
        "fact_returns": fact_returns,
        "fact_web_events": fact_web_events,
        "fact_markdown": fact_markdown,
    }
