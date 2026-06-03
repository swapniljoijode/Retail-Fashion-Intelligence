"""Tests for fact generators — schema, value ranges, and business rules."""
from __future__ import annotations

import pandas as pd
import pytest


class TestFactSales:
    def test_non_empty(self, fact_sales):
        assert len(fact_sales) > 0

    def test_required_columns(self, fact_sales):
        required = {
            "sale_key", "order_id", "order_line_id", "sale_date",
            "product_id", "store_id", "customer_id", "channel_id", "promotion_id",
            "units_sold", "unit_retail_price", "gross_revenue", "discount_amount",
            "net_revenue", "unit_cost", "cogs", "gross_margin",
        }
        assert required.issubset(set(fact_sales.columns))

    def test_sale_key_unique(self, fact_sales):
        assert fact_sales["sale_key"].is_unique

    def test_units_sold_positive(self, fact_sales):
        numeric_units = pd.to_numeric(fact_sales["units_sold"], errors="coerce")
        assert (numeric_units > 0).all()

    def test_net_revenue_non_negative(self, fact_sales):
        assert (fact_sales["net_revenue"] >= 0).all()

    def test_gross_revenue_gte_net_revenue(self, fact_sales):
        assert (fact_sales["gross_revenue"] >= fact_sales["net_revenue"]).all()

    def test_sale_dates_in_range(self, fact_sales, config):
        dates = pd.to_datetime(fact_sales["sale_date"]).dt.date
        assert dates.min() >= config.start_date
        assert dates.max() <= config.end_date

    def test_gross_margin_can_be_negative(self, fact_sales):
        # Markdown orders can theoretically yield negative margin — valid business case
        assert "gross_margin" in fact_sales.columns

    def test_no_null_keys(self, fact_sales):
        for col in ("order_id", "product_id", "store_id", "customer_id", "channel_id"):
            assert fact_sales[col].isna().sum() == 0


class TestFactInventory:
    def test_non_empty(self, fact_inventory):
        assert len(fact_inventory) > 0

    def test_required_columns(self, fact_inventory):
        required = {
            "inventory_key", "snapshot_date", "product_id", "store_id",
            "units_on_hand", "units_in_transit", "is_stockout",
        }
        assert required.issubset(set(fact_inventory.columns))

    def test_units_on_hand_non_negative(self, fact_inventory):
        numeric = pd.to_numeric(fact_inventory["units_on_hand"], errors="coerce")
        assert (numeric >= 0).all()

    def test_stockout_flag_consistent(self, fact_inventory):
        df = fact_inventory.copy()
        numeric_uoh = pd.to_numeric(df["units_on_hand"], errors="coerce")
        expected_stockout = numeric_uoh == 0
        assert (df["is_stockout"] == expected_stockout).all()


class TestFactReturns:
    def test_required_columns(self, fact_returns):
        required = {
            "return_key", "return_id", "original_order_id",
            "return_date", "original_sale_date",
            "product_id", "store_id", "customer_id", "channel_id",
            "units_returned", "refund_value", "return_reason",
        }
        assert required.issubset(set(fact_returns.columns))

    def test_return_date_after_sale_date(self, fact_returns):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated for this config")
        ret_dates = pd.to_datetime(fact_returns["return_date"]).dt.date
        sale_dates = pd.to_datetime(fact_returns["original_sale_date"]).dt.date
        assert (ret_dates >= sale_dates).all()

    def test_refund_value_positive(self, fact_returns):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated")
        assert (fact_returns["refund_value"] > 0).all()

    def test_return_reason_valid(self, fact_returns):
        if len(fact_returns) == 0:
            pytest.skip("No returns generated")
        valid = {"size", "quality", "changed_mind", "damaged", "wrong_item", "late_delivery"}
        assert set(fact_returns["return_reason"].unique()).issubset(valid)


class TestFactWebEvents:
    def test_non_empty(self, fact_web_events):
        assert len(fact_web_events) > 0

    def test_required_columns(self, fact_web_events):
        required = {
            "event_key", "session_id", "event_date",
            "channel_id", "device_type", "event_type",
        }
        assert required.issubset(set(fact_web_events.columns))

    def test_event_types_valid(self, fact_web_events):
        valid = {
            "page_view", "product_view", "add_to_cart",
            "checkout_start", "purchase", "abandon_cart",
        }
        assert set(fact_web_events["event_type"].unique()).issubset(valid)

    def test_page_view_most_common(self, fact_web_events):
        counts = fact_web_events["event_type"].value_counts()
        assert counts.index[0] == "page_view"

    def test_purchase_count_less_than_add_to_cart(self, fact_web_events):
        counts = fact_web_events["event_type"].value_counts()
        assert counts.get("purchase", 0) <= counts.get("add_to_cart", 0)


class TestFactMarkdown:
    def test_required_columns(self, fact_markdown):
        required = {
            "markdown_key", "week_start_date", "product_id", "store_id",
            "regular_price", "markdown_price", "markdown_depth_pct",
            "units_sold_on_markdown", "revenue_on_markdown",
        }
        assert required.issubset(set(fact_markdown.columns))

    def test_markdown_price_less_than_regular(self, fact_markdown):
        if len(fact_markdown) == 0:
            pytest.skip("No markdowns generated for this config")
        assert (fact_markdown["markdown_price"] <= fact_markdown["regular_price"]).all()

    def test_depth_between_zero_and_one(self, fact_markdown):
        if len(fact_markdown) == 0:
            pytest.skip("No markdowns generated for this config")
        assert fact_markdown["markdown_depth_pct"].between(0, 1).all()
