"""Referential integrity tests — every FK in a fact table must exist in its dimension."""
from __future__ import annotations

import pandas as pd
import pytest


def _orphan_count(fact: pd.DataFrame, fk_col: str, dim: pd.DataFrame, pk_col: str) -> int:
    """Return the number of fact rows whose FK value is not in the dimension."""
    fact_vals = set(fact[fk_col].dropna().unique())
    dim_vals = set(dim[pk_col].unique())
    return len(fact_vals - dim_vals)


class TestSalesReferentialIntegrity:
    def test_product_ids_exist(self, fact_sales, dims):
        orphans = _orphan_count(fact_sales, "product_id", dims["dim_product"], "product_id")
        assert orphans == 0, f"{orphans} product_ids in fact_sales not found in dim_product"

    def test_store_ids_exist(self, fact_sales, dims):
        orphans = _orphan_count(fact_sales, "store_id", dims["dim_store"], "store_id")
        assert orphans == 0

    def test_customer_ids_exist(self, fact_sales, dims):
        orphans = _orphan_count(fact_sales, "customer_id", dims["dim_customer"], "customer_id")
        assert orphans == 0

    def test_channel_ids_exist(self, fact_sales, dims):
        orphans = _orphan_count(fact_sales, "channel_id", dims["dim_channel"], "channel_id")
        assert orphans == 0

    def test_promotion_ids_exist(self, fact_sales, dims):
        orphans = _orphan_count(fact_sales, "promotion_id", dims["dim_promotion"], "promotion_id")
        assert orphans == 0


class TestInventoryReferentialIntegrity:
    def test_product_ids_exist(self, fact_inventory, dims):
        orphans = _orphan_count(fact_inventory, "product_id", dims["dim_product"], "product_id")
        assert orphans == 0

    def test_store_ids_exist(self, fact_inventory, dims):
        orphans = _orphan_count(fact_inventory, "store_id", dims["dim_store"], "store_id")
        assert orphans == 0


class TestReturnsReferentialIntegrity:
    def test_product_ids_exist(self, fact_returns, dims):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated")
        orphans = _orphan_count(fact_returns, "product_id", dims["dim_product"], "product_id")
        assert orphans == 0

    def test_store_ids_exist(self, fact_returns, dims):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated")
        orphans = _orphan_count(fact_returns, "store_id", dims["dim_store"], "store_id")
        assert orphans == 0

    def test_customer_ids_exist(self, fact_returns, dims):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated")
        orphans = _orphan_count(fact_returns, "customer_id", dims["dim_customer"], "customer_id")
        assert orphans == 0

    def test_original_order_ids_exist_in_sales(self, fact_returns, fact_sales):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated")
        orphans = _orphan_count(fact_returns, "original_order_id", fact_sales, "order_id")
        assert orphans == 0, f"{orphans} return order_ids not found in fact_sales"


class TestWebEventsReferentialIntegrity:
    def test_channel_ids_exist(self, fact_web_events, dims):
        orphans = _orphan_count(fact_web_events, "channel_id", dims["dim_channel"], "channel_id")
        assert orphans == 0

    def test_product_ids_exist_where_present(self, fact_web_events, dims):
        with_product = fact_web_events.dropna(subset=["product_id"])
        if len(with_product) == 0:
            pytest.skip("No product-linked web events")
        orphans = _orphan_count(with_product, "product_id", dims["dim_product"], "product_id")
        assert orphans == 0


class TestMarkdownReferentialIntegrity:
    def test_product_ids_exist(self, fact_markdown, dims):
        if len(fact_markdown) == 0:
            pytest.skip("No markdowns generated")
        orphans = _orphan_count(fact_markdown, "product_id", dims["dim_product"], "product_id")
        assert orphans == 0

    def test_store_ids_exist(self, fact_markdown, dims):
        if len(fact_markdown) == 0:
            pytest.skip("No markdowns generated")
        orphans = _orphan_count(fact_markdown, "store_id", dims["dim_store"], "store_id")
        assert orphans == 0
