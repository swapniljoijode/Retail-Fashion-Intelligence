"""Generators for all six conformed dimensions."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from data_generation.config import VolumeConfig
from data_generation.taxonomy import (
    ACQUISITION_CHANNELS,
    ACQUISITION_WEIGHTS,
    BRANDS,
    BUYING_SEASONS,
    CATEGORIES,
    CHANNEL_SEED,
    COLORS,
    CUSTOMER_SEGMENTS,
    LOYALTY_TIERS,
    LOYALTY_WEIGHTS,
    NAMED_PROMOTIONS,
    SEASON_MONTHS,
    SEGMENT_WEIGHTS,
    STORE_SQFT_RANGES,
    STORE_TYPE_POOL,
    UK_CITIES_BY_REGION,
    UK_REGIONS,
)

# ── dim_date ──────────────────────────────────────────────────────────────────


def generate_dim_date(config: VolumeConfig) -> pd.DataFrame:
    """Static date dimension spanning start_date to end_date."""
    dates = pd.date_range(config.start_date, config.end_date, freq="D")
    df = pd.DataFrame({"date": dates})

    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["day_of_week"] = df["date"].dt.dayofweek + 1  # 1 = Monday
    df["day_name"] = df["date"].dt.day_name()
    df["day_of_month"] = df["date"].dt.day
    df["day_of_year"] = df["date"].dt.dayofyear
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["month_number"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["quarter_number"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["retail_season"] = df["month_number"].apply(
        lambda m: "SS" if m in SEASON_MONTHS["SS"] else "AW"
    )
    df["calendar_season"] = df["month_number"].apply(_calendar_season)
    df["is_weekend"] = df["day_of_week"].isin([6, 7])

    holidays = _uk_public_holidays(config.start_date.year, config.end_date.year)
    holiday_map = {h[0]: h[1] for h in holidays}
    df["_date_only"] = df["date"].dt.date
    df["is_public_holiday"] = df["_date_only"].isin(holiday_map.keys())
    df["holiday_name"] = df["_date_only"].map(holiday_map)
    df["trading_day_of_week"] = df["day_of_week"].where(
        df["day_of_week"] <= 5, other=None
    )

    return df.drop(columns=["_date_only"]).reset_index(drop=True)


def _calendar_season(month: int) -> str:
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    if month in (9, 10, 11):
        return "Autumn"
    return "Winter"


def _uk_public_holidays(start_year: int, end_year: int) -> list[tuple[date, str]]:
    """Simplified fixed UK public holidays — moveable feasts omitted for brevity."""
    rows = []
    for y in range(start_year, end_year + 1):
        rows += [
            (date(y, 1, 1), "New Year's Day"),
            (date(y, 5, 27), "Spring Bank Holiday"),  # approximate
            (date(y, 8, 26), "Summer Bank Holiday"),  # approximate
            (date(y, 12, 25), "Christmas Day"),
            (date(y, 12, 26), "Boxing Day"),
        ]
    return rows


# ── dim_product ───────────────────────────────────────────────────────────────


def generate_dim_product(
    config: VolumeConfig, rng: np.random.Generator
) -> pd.DataFrame:
    """
    Product dimension with SCD Type 2 on retail_price.

    Generates n_styles base product styles and expands each to per-size SKUs.
    Roughly 20 % of styles get a mid-period price change, creating a second
    SCD row with is_current=True and the original row closed with expiry_date set.
    """
    category_names = list(CATEGORIES.keys())
    cat_weights = [CATEGORIES[c]["category_weight"] for c in category_names]
    cat_weights_norm = [w / sum(cat_weights) for w in cat_weights]
    style_categories = rng.choice(
        category_names, size=config.n_styles, p=cat_weights_norm
    )

    product_key = 1
    sku_counter = 1
    rows: list[dict] = []

    for style_idx in range(config.n_styles):
        cat = style_categories[style_idx]
        info = CATEGORIES[cat]

        subcategory = rng.choice(info["subcategories"])
        brand = rng.choice(BRANDS)
        color = rng.choice(COLORS)
        season = rng.choice(BUYING_SEASONS)
        product_name = f"{brand} {color} {subcategory}"

        lo, hi = info["price_range"]
        retail_price = _charm_price(float(rng.uniform(lo, hi)))
        m_lo, m_hi = info["margin_range"]
        margin = float(rng.uniform(m_lo, m_hi))
        cost_price = round(retail_price * (1 - margin), 2)

        # SCD Type 2 price change for ~20 % of styles
        has_price_change = rng.random() < 0.20
        period_days = (config.end_date - config.start_date).days
        price_change_date: date | None = None
        if has_price_change:
            offset = int(rng.integers(60, max(61, period_days // 2)))
            price_change_date = config.start_date + timedelta(days=offset)

        for size in info["sizes"]:
            product_id = f"PRD-{sku_counter:05d}"
            sku = f"{brand[:3].upper()}-{cat[:3].upper()}-{color[:3].upper()}-{size}"
            sku_counter += 1

            base = {
                "product_id": product_id,
                "sku": sku,
                "product_name": product_name,
                "category": cat,
                "subcategory": subcategory,
                "brand": brand,
                "color": color,
                "size": size,
                "season": season,
                "cost_price": cost_price,
            }

            if has_price_change and price_change_date is not None:
                # Version 1 — original price, now expired
                rows.append(
                    {
                        "product_key": product_key,
                        **base,
                        "retail_price": retail_price,
                        "margin_pct": round(margin, 4),
                        "is_current": False,
                        "effective_date": config.start_date,
                        "expiry_date": price_change_date - timedelta(days=1),
                    }
                )
                product_key += 1

                new_price = _charm_price(retail_price * float(rng.uniform(0.85, 1.20)))
                new_margin = round((new_price - cost_price) / new_price, 4)

                # Version 2 — current price
                rows.append(
                    {
                        "product_key": product_key,
                        **base,
                        "retail_price": new_price,
                        "margin_pct": new_margin,
                        "is_current": True,
                        "effective_date": price_change_date,
                        "expiry_date": None,
                    }
                )
                product_key += 1
            else:
                rows.append(
                    {
                        "product_key": product_key,
                        **base,
                        "retail_price": retail_price,
                        "margin_pct": round(margin, 4),
                        "is_current": True,
                        "effective_date": config.start_date,
                        "expiry_date": None,
                    }
                )
                product_key += 1

    return pd.DataFrame(rows)


def _charm_price(price: float) -> float:
    """Round to the nearest .95 or .99 retail charm price."""
    base = int(price)
    frac = price - base
    if frac < 0.50:
        return max(0.95, (base - 1) + 0.95)
    if frac < 0.97:
        return base + 0.95
    return base + 0.99


# ── dim_store ─────────────────────────────────────────────────────────────────


def generate_dim_store(config: VolumeConfig, rng: np.random.Generator) -> pd.DataFrame:
    """Store dimension with realistic UK geography and square footage."""
    faker = Faker("en_GB")
    faker.seed_instance(config.seed + 100)

    region_names = [r[0] for r in UK_REGIONS]
    region_weights = [r[1] for r in UK_REGIONS]
    region_weights_norm = [w / sum(region_weights) for w in region_weights]

    rows: list[dict] = []
    for i in range(config.n_stores):
        store_type = rng.choice(STORE_TYPE_POOL)
        region = rng.choice(region_names, p=region_weights_norm)
        city = rng.choice(UK_CITIES_BY_REGION[region])
        sqft_lo, sqft_hi = STORE_SQFT_RANGES[store_type]
        sqft = int(rng.integers(sqft_lo, sqft_hi + 1))
        opening_year = int(rng.integers(2010, 2024))
        opening_date = date(opening_year, int(rng.integers(1, 13)), 1)

        rows.append(
            {
                "store_key": i + 1,
                "store_id": f"STR-{i + 1:03d}",
                "store_name": f"{city} {store_type.replace('_', ' ').title()}",
                "region": region,
                "city": city,
                "country": "GB",
                "store_type": store_type,
                "square_footage": sqft,
                "opening_date": opening_date,
            }
        )

    return pd.DataFrame(rows)


# ── dim_customer ──────────────────────────────────────────────────────────────


def generate_dim_customer(
    config: VolumeConfig, rng: np.random.Generator
) -> pd.DataFrame:
    """
    Customer dimension with SCD Type 2 on customer_segment.

    ~15 % of customers receive a segment upgrade/downgrade mid-period,
    creating a second row. first_purchase_date is spread across the period.
    """
    faker = Faker("en_GB")
    faker.seed_instance(config.seed + 200)

    region_names = [r[0] for r in UK_REGIONS]
    _total_w = sum(w for _, w in UK_REGIONS)
    region_weights = [w / _total_w for _, w in UK_REGIONS]

    customer_key = 1
    rows: list[dict] = []
    period_days = (config.end_date - config.start_date).days

    for i in range(config.n_customers):
        customer_id = f"CST-{i + 1:06d}"
        segment = rng.choice(CUSTOMER_SEGMENTS, p=SEGMENT_WEIGHTS)
        loyalty_tier = rng.choice(LOYALTY_TIERS, p=LOYALTY_WEIGHTS)
        region = rng.choice(region_names, p=region_weights)
        city = rng.choice(UK_CITIES_BY_REGION[region])
        acq_channel = rng.choice(ACQUISITION_CHANNELS, p=ACQUISITION_WEIGHTS)
        days_offset = int(rng.integers(0, max(1, period_days - 30)))
        first_purchase_date = config.start_date + timedelta(days=days_offset)

        has_segment_change = rng.random() < 0.15
        segment_change_date: date | None = None
        if has_segment_change:
            change_offset = int(
                rng.integers(days_offset + 10, max(days_offset + 11, period_days - 10))
            )
            segment_change_date = config.start_date + timedelta(days=change_offset)

        base = {
            "customer_id": customer_id,
            "loyalty_tier": loyalty_tier,
            "region": region,
            "city": city,
            "acquisition_channel": acq_channel,
            "first_purchase_date": first_purchase_date,
        }

        if has_segment_change and segment_change_date is not None:
            rows.append(
                {
                    "customer_key": customer_key,
                    **base,
                    "customer_segment": segment,
                    "is_current": False,
                    "effective_date": config.start_date,
                    "expiry_date": segment_change_date - timedelta(days=1),
                }
            )
            customer_key += 1

            # Pass full list with the current segment zeroed out so numpy
            # array size matches probability array size.
            new_segment = rng.choice(
                CUSTOMER_SEGMENTS,
                p=_reweight(SEGMENT_WEIGHTS, CUSTOMER_SEGMENTS, segment),
            )
            rows.append(
                {
                    "customer_key": customer_key,
                    **base,
                    "customer_segment": new_segment,
                    "is_current": True,
                    "effective_date": segment_change_date,
                    "expiry_date": None,
                }
            )
            customer_key += 1
        else:
            rows.append(
                {
                    "customer_key": customer_key,
                    **base,
                    "customer_segment": segment,
                    "is_current": True,
                    "effective_date": config.start_date,
                    "expiry_date": None,
                }
            )
            customer_key += 1

    return pd.DataFrame(rows)


def _reweight(weights: list[float], items: list[str], exclude: str) -> list[float]:
    """Return normalized weights with the excluded item zeroed out."""
    w = [v if items[i] != exclude else 0.0 for i, v in enumerate(weights)]
    total = sum(w)
    return [v / total for v in w]


# ── dim_channel ───────────────────────────────────────────────────────────────


def generate_dim_channel() -> pd.DataFrame:
    """Static channel dimension seeded from taxonomy — 7 rows, no generation needed."""
    df = pd.DataFrame(CHANNEL_SEED)
    df.insert(0, "channel_key", range(1, len(df) + 1))
    return df


# ── dim_promotion ─────────────────────────────────────────────────────────────


def generate_dim_promotion(
    config: VolumeConfig, rng: np.random.Generator
) -> pd.DataFrame:
    """
    Promotion dimension.

    Selects n_promotions from NAMED_PROMOTIONS and assigns concrete start/end
    dates within the config period. A 'No Promotion' sentinel row is always
    prepended at promotion_key = -1 so fact_sales can reference it safely.
    """
    n = min(config.n_promotions, len(NAMED_PROMOTIONS))
    chosen_indices = rng.choice(len(NAMED_PROMOTIONS), size=n, replace=False)
    chosen = [NAMED_PROMOTIONS[i] for i in sorted(chosen_indices)]

    rows: list[dict] = [
        {
            "promotion_key": -1,
            "promotion_id": "NONE",
            "promotion_name": "No Promotion",
            "promotion_type": None,
            "discount_pct": None,
            "start_date": None,
            "end_date": None,
            "is_sitewide": False,
        }
    ]

    for key_idx, (
        name,
        promo_type,
        peak_month,
        discount_pct,
        duration_days,
    ) in enumerate(chosen, start=1):
        # Anchor start_date to the peak_month within the config period
        for year in range(config.start_date.year, config.end_date.year + 1):
            month = peak_month
            try:
                start = date(year, month, int(rng.integers(1, 15)))
            except ValueError:
                start = date(year, month, 1)

            if start < config.start_date or start > config.end_date:
                continue

            end = min(start + timedelta(days=duration_days - 1), config.end_date)
            rows.append(
                {
                    "promotion_key": key_idx,
                    "promotion_id": f"PRM-{key_idx:03d}",
                    "promotion_name": name,
                    "promotion_type": promo_type,
                    "discount_pct": discount_pct,
                    "start_date": start,
                    "end_date": end,
                    "is_sitewide": rng.random() < 0.40,
                }
            )
            break  # one occurrence per promotion per period

    return pd.DataFrame(rows)
