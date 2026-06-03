"""Tests for dimension generators — schema, uniqueness, and value ranges."""
from __future__ import annotations

import pandas as pd
import pytest

from data_generation.taxonomy import BUYING_SEASONS, CATEGORIES, CHANNEL_SEED


class TestDimDate:
    def test_row_count(self, dims, config):
        expected = (config.end_date - config.start_date).days + 1
        assert len(dims["dim_date"]) == expected

    def test_required_columns(self, dims):
        required = {
            "date_key", "date", "day_of_week", "day_name", "day_of_month",
            "day_of_year", "week_of_year", "month_number", "month_name",
            "quarter_number", "year", "retail_season", "calendar_season",
            "is_weekend", "is_public_holiday", "holiday_name",
        }
        assert required.issubset(set(dims["dim_date"].columns))

    def test_date_key_unique(self, dims):
        assert dims["dim_date"]["date_key"].is_unique

    def test_date_key_format(self, dims):
        sample = dims["dim_date"]["date_key"].iloc[0]
        assert 20_000_101 <= sample <= 20_991_231

    def test_day_of_week_range(self, dims):
        assert dims["dim_date"]["day_of_week"].between(1, 7).all()

    def test_retail_season_values(self, dims):
        assert set(dims["dim_date"]["retail_season"].unique()).issubset({"SS", "AW"})

    def test_no_nulls_in_critical_columns(self, dims):
        for col in ("date_key", "date", "month_number", "year", "is_weekend"):
            assert dims["dim_date"][col].isna().sum() == 0


class TestDimProduct:
    def test_product_key_unique(self, dims):
        assert dims["dim_product"]["product_key"].is_unique

    def test_required_columns(self, dims):
        required = {
            "product_key", "product_id", "sku", "product_name", "category",
            "subcategory", "brand", "color", "size", "season", "cost_price",
            "retail_price", "margin_pct", "is_current", "effective_date",
        }
        assert required.issubset(set(dims["dim_product"].columns))

    def test_categories_valid(self, dims):
        valid = set(CATEGORIES.keys())
        assert set(dims["dim_product"]["category"].dropna().unique()).issubset(valid)

    def test_seasons_valid(self, dims):
        valid = set(BUYING_SEASONS)
        assert set(dims["dim_product"]["season"].unique()).issubset(valid)

    def test_retail_price_positive(self, dims):
        assert (dims["dim_product"]["retail_price"] > 0).all()

    def test_cost_less_than_retail(self, dims):
        assert (dims["dim_product"]["cost_price"] < dims["dim_product"]["retail_price"]).all()

    def test_margin_between_zero_and_one(self, dims):
        assert dims["dim_product"]["margin_pct"].between(0, 1).all()

    def test_exactly_one_current_row_per_product_id(self, dims):
        current_counts = (
            dims["dim_product"]
            .groupby("product_id")["is_current"]
            .sum()
        )
        assert (current_counts == 1).all(), "Each product_id must have exactly one current row"

    def test_scd_versions_have_non_null_expiry(self, dims):
        non_current = dims["dim_product"][~dims["dim_product"]["is_current"]]
        if len(non_current) > 0:
            assert non_current["expiry_date"].isna().sum() == 0


class TestDimStore:
    def test_store_key_unique(self, dims):
        assert dims["dim_store"]["store_key"].is_unique

    def test_row_count(self, dims, config):
        assert len(dims["dim_store"]) == config.n_stores

    def test_required_columns(self, dims):
        required = {"store_key", "store_id", "store_name", "region", "city", "store_type", "square_footage"}
        assert required.issubset(set(dims["dim_store"].columns))

    def test_square_footage_positive(self, dims):
        assert (dims["dim_store"]["square_footage"] > 0).all()

    def test_store_type_valid(self, dims):
        valid = {"flagship", "standard", "outlet", "pop_up"}
        assert set(dims["dim_store"]["store_type"].unique()).issubset(valid)


class TestDimCustomer:
    def test_customer_key_unique(self, dims):
        assert dims["dim_customer"]["customer_key"].is_unique

    def test_required_columns(self, dims):
        required = {
            "customer_key", "customer_id", "customer_segment", "loyalty_tier",
            "acquisition_channel", "first_purchase_date", "is_current",
        }
        assert required.issubset(set(dims["dim_customer"].columns))

    def test_exactly_one_current_row_per_customer_id(self, dims):
        counts = dims["dim_customer"].groupby("customer_id")["is_current"].sum()
        assert (counts == 1).all()

    def test_segment_values_valid(self, dims):
        valid = {"budget", "mid_market", "premium", "luxury"}
        assert set(dims["dim_customer"]["customer_segment"].unique()).issubset(valid)


class TestDimChannel:
    def test_exactly_seven_rows(self, dims):
        assert len(dims["dim_channel"]) == len(CHANNEL_SEED)

    def test_channel_key_unique(self, dims):
        assert dims["dim_channel"]["channel_key"].is_unique

    def test_channel_ids_match_seed(self, dims):
        expected_ids = {row["channel_id"] for row in CHANNEL_SEED}
        assert set(dims["dim_channel"]["channel_id"].unique()) == expected_ids


class TestDimPromotion:
    def test_sentinel_row_present(self, dims):
        assert "NONE" in dims["dim_promotion"]["promotion_id"].values

    def test_promotion_key_unique(self, dims):
        assert dims["dim_promotion"]["promotion_key"].is_unique

    def test_discount_pct_range(self, dims):
        real_promos = dims["dim_promotion"].dropna(subset=["discount_pct"])
        assert real_promos["discount_pct"].between(0, 1).all()
