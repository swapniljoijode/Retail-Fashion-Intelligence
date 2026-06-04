"""Generators for all five fact tables."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from data_generation.config import VolumeConfig
from data_generation.taxonomy import (
    CATEGORIES,
    DEVICE_TYPES,
    DEVICE_WEIGHTS,
    FUNNEL_REACH,
    MONTHLY_DEMAND,
    RETURN_RATES,
    RETURN_REASON_WEIGHTS,
    RETURN_REASONS,
    SEASON_MONTHS,
)

# ── fact_sales ────────────────────────────────────────────────────────────────


def generate_fact_sales(
    config: VolumeConfig,
    rng: np.random.Generator,
    dims: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Sales fact at order-line grain.

    Demand is driven by:
    - MONTHLY_DEMAND seasonal curve
    - Weekend uplift (Sat 1.3×, Sun 1.1×)
    - Active promotion uplift (15 % per overlapping promotion)
    - Product-season affinity (SS products sell better Feb–Jul, AW Aug–Jan)
    - Store size weighting (larger stores attract more orders)
    """
    dim_product = dims["dim_product"]
    dim_store = dims["dim_store"]
    dim_customer = dims["dim_customer"]
    dim_channel = dims["dim_channel"]
    dim_promotion = dims["dim_promotion"]

    # Current-version products only for sales lookups
    current_products = dim_product[dim_product["is_current"]].copy()
    product_ids = current_products["product_id"].values
    prod_lookup = current_products.set_index("product_id").to_dict("index")

    store_ids = dim_store["store_id"].values
    store_sqft = dim_store["square_footage"].values.astype(float)
    store_weights = store_sqft / store_sqft.sum()
    store_type_map = dim_store.set_index("store_id")["store_type"].to_dict()

    current_customers = dim_customer[dim_customer["is_current"]]["customer_id"].values

    digital_ch = dim_channel[
        dim_channel["channel_type"].isin(["digital", "marketplace"])
    ]["channel_id"].values
    physical_ch_map = {
        "flagship": dim_channel[dim_channel["channel_id"] == "CH04"][
            "channel_id"
        ].values,
        "standard": dim_channel[dim_channel["channel_id"] == "CH05"][
            "channel_id"
        ].values,
        "outlet": dim_channel[dim_channel["channel_id"] == "CH06"]["channel_id"].values,
        "pop_up": dim_channel[dim_channel["channel_id"] == "CH07"]["channel_id"].values,
    }

    active_promos = dim_promotion[dim_promotion["promotion_id"] != "NONE"].copy()
    active_promos["start_date"] = pd.to_datetime(active_promos["start_date"]).dt.date
    active_promos["end_date"] = pd.to_datetime(active_promos["end_date"]).dt.date

    # Pre-compute per-month product selection weights (avoids recomputing per order)
    monthly_weights: dict[int, np.ndarray] = {}
    base_w = np.array(
        [CATEGORIES[prod_lookup[p]["category"]]["category_weight"] for p in product_ids]
    )
    for month in range(1, 13):
        w = base_w.copy()
        for i, pid in enumerate(product_ids):
            st = prod_lookup[pid]["season"][:2]  # "SS" or "AW"
            affinity = CATEGORIES[prod_lookup[pid]["category"]]["season_affinity"]
            if (st == "SS" and month in SEASON_MONTHS["SS"]) or (
                st == "AW" and month in SEASON_MONTHS["AW"]
            ):
                w[i] *= affinity[st]
            else:
                w[i] *= 1 / affinity[st]
        w = w / w.sum()
        monthly_weights[month] = w

    # Build a promotion lookup: date -> list of active promos
    date_to_promos: dict[date, list[dict]] = {}
    for dt in pd.date_range(config.start_date, config.end_date).date:
        date_to_promos[dt] = [
            row.to_dict()
            for _, row in active_promos[
                (active_promos["start_date"] <= dt) & (active_promos["end_date"] >= dt)
            ].iterrows()
        ]

    rows: list[dict] = []
    sale_key = 1
    order_counter = 1

    for dt in pd.date_range(config.start_date, config.end_date).date:
        month = dt.month
        dow = date(dt.year, dt.month, dt.day).weekday()  # 0=Mon

        seasonal_mult = MONTHLY_DEMAND[month]
        day_mult = 1.30 if dow == 5 else (1.10 if dow == 6 else 1.00)
        promos_today = date_to_promos[dt]
        promo_mult = 1.0 + 0.15 * len(promos_today)

        n_orders = int(
            rng.poisson(config.avg_daily_orders * seasonal_mult * day_mult * promo_mult)
        )

        pw = monthly_weights[month]

        for _ in range(n_orders):
            store_id = str(rng.choice(store_ids, p=store_weights))
            store_type = store_type_map[store_id]

            # 65 % of physical-store orders use the matched physical channel,
            # 35 % come through digital (click-and-collect / same-day delivery)
            if rng.random() < 0.65 and store_type in physical_ch_map:
                channel_id = str(rng.choice(physical_ch_map[store_type]))
            else:
                channel_id = str(rng.choice(digital_ch))

            customer_id = str(rng.choice(current_customers))

            # Assign promotion if one is active and the order qualifies
            promo_id = "NONE"
            discount_rate = 0.0
            if promos_today and rng.random() < 0.30:
                promo = promos_today[int(rng.integers(0, len(promos_today)))]
                promo_id = promo["promotion_id"]
                discount_rate = float(promo["discount_pct"] or 0.0)

            n_lines = int(rng.integers(1, 5))
            order_id = f"ORD-{order_counter:08d}"
            order_counter += 1

            selected_pids = rng.choice(product_ids, size=n_lines, p=pw, replace=True)

            for pid in selected_pids:
                p = prod_lookup[pid]
                units = int(rng.integers(1, 4))
                retail = float(p["retail_price"])
                gross = round(units * retail, 2)
                disc = round(gross * discount_rate, 2)
                net = round(gross - disc, 2)
                cost = float(p["cost_price"])
                cogs = round(units * cost, 2)
                margin = round(net - cogs, 2)

                rows.append(
                    {
                        "sale_key": sale_key,
                        "order_id": order_id,
                        "order_line_id": f"ORL-{sale_key:09d}",
                        "sale_date": dt,
                        "product_id": pid,
                        "store_id": store_id,
                        "customer_id": customer_id,
                        "channel_id": channel_id,
                        "promotion_id": promo_id,
                        "units_sold": units,
                        "unit_retail_price": retail,
                        "gross_revenue": gross,
                        "discount_amount": disc,
                        "net_revenue": net,
                        "unit_cost": cost,
                        "cogs": cogs,
                        "gross_margin": margin,
                    }
                )
                sale_key += 1

    return pd.DataFrame(rows)


# ── fact_inventory_snapshot ───────────────────────────────────────────────────


def generate_fact_inventory_snapshot(
    config: VolumeConfig,
    rng: np.random.Generator,
    dims: dict[str, pd.DataFrame],
    fact_sales: pd.DataFrame,
) -> pd.DataFrame:
    """
    Inventory snapshot at product-store-day grain.

    Stock is tracked from an initial level, depleted by actual sales,
    and replenished on a per-product-store cycle. This makes sell-through
    and weeks-of-supply metrics meaningful in the gold layer.
    """
    current_products = dims["dim_product"][dims["dim_product"]["is_current"]]
    product_ids = current_products["product_id"].values
    store_ids = dims["dim_store"]["store_id"].values
    store_sqft = dims["dim_store"].set_index("store_id")["square_footage"].to_dict()
    dates = list(pd.date_range(config.start_date, config.end_date).date)

    # Pre-aggregate daily sales per product-store-date for O(1) lookup
    daily_sales = (
        fact_sales.groupby(["product_id", "store_id", "sale_date"])["units_sold"]
        .sum()
        .to_dict()
    )

    rows: list[dict] = []
    inv_key = 1

    for pid in product_ids:
        for sid in store_ids:
            sqft = store_sqft[sid]
            # Larger stores carry more stock
            max_stock = int(sqft / 100)
            start_stock = int(rng.integers(max(5, max_stock // 3), max(6, max_stock)))
            reorder_point = max(2, start_stock // 4)
            replenishment_cycle = int(rng.integers(10, 21))
            replenishment_qty = int(rng.integers(start_stock // 2, start_stock + 1))

            stock = start_stock
            transit = 0

            for day_idx, dt in enumerate(dates):
                sold = int(daily_sales.get((pid, sid, dt), 0))
                stock = max(0, stock - sold)

                # Replenish: place an order every cycle; goods arrive 3 days later
                if day_idx % replenishment_cycle == (replenishment_cycle - 1):
                    transit += replenishment_qty
                if (
                    day_idx % replenishment_cycle
                    == (replenishment_cycle - 1 + 3) % replenishment_cycle
                ):
                    arriving = min(transit, replenishment_qty)
                    stock += arriving
                    transit = max(0, transit - arriving)

                rows.append(
                    {
                        "inventory_key": inv_key,
                        "snapshot_date": dt,
                        "product_id": pid,
                        "store_id": sid,
                        "units_on_hand": stock,
                        "units_in_transit": transit,
                        "units_on_order": (
                            replenishment_qty
                            if day_idx % replenishment_cycle == 0
                            else 0
                        ),
                        "reorder_point": reorder_point,
                        "is_stockout": stock == 0,
                    }
                )
                inv_key += 1

    return pd.DataFrame(rows)


# ── fact_returns ──────────────────────────────────────────────────────────────


def generate_fact_returns(
    config: VolumeConfig,
    rng: np.random.Generator,
    dims: dict[str, pd.DataFrame],
    fact_sales: pd.DataFrame,
) -> pd.DataFrame:
    """
    Returns fact at return-line grain.

    Return probability is drawn from category-specific RETURN_RATES.
    Returns happen 1–30 days after the original sale. Return channel
    may differ from the purchase channel.
    """
    prod_category = dims["dim_product"].set_index("product_id")["category"].to_dict()
    channel_ids = dims["dim_channel"]["channel_id"].values

    rows: list[dict] = []
    return_key = 1
    return_counter = 1

    for _, sale in fact_sales.iterrows():
        pid = sale["product_id"]
        category = prod_category.get(pid, "Tops")
        return_rate = RETURN_RATES.get(category, 0.15)

        if rng.random() > return_rate:
            continue

        units_returned = int(rng.integers(1, min(sale["units_sold"] + 1, 4)))
        return_lag = int(rng.integers(1, 31))
        return_date = sale["sale_date"] + timedelta(days=return_lag)
        if return_date > config.end_date:
            return_date = config.end_date

        refund = round(
            units_returned * sale["unit_retail_price"] * float(rng.uniform(0.90, 1.00)),
            2,
        )

        rows.append(
            {
                "return_key": return_key,
                "return_id": f"RET-{return_counter:07d}",
                "return_line_id": f"RTL-{return_key:09d}",
                "original_order_id": sale["order_id"],
                "return_date": return_date,
                "original_sale_date": sale["sale_date"],
                "product_id": pid,
                "store_id": sale["store_id"],
                "customer_id": sale["customer_id"],
                "channel_id": str(rng.choice(channel_ids)),
                "units_returned": units_returned,
                "refund_value": refund,
                "return_reason": str(
                    rng.choice(RETURN_REASONS, p=RETURN_REASON_WEIGHTS)
                ),
            }
        )
        return_key += 1
        return_counter += 1

    return pd.DataFrame(rows)


# ── fact_web_events ───────────────────────────────────────────────────────────


def generate_fact_web_events(
    config: VolumeConfig,
    rng: np.random.Generator,
    dims: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Web events fact at session-event grain.

    Simulates the conversion funnel (page_view → product_view →
    add_to_cart → checkout_start → purchase / abandon_cart).
    Anonymous sessions have no customer_id. Session volume scales
    with the same seasonal demand curve as fact_sales.
    """
    digital_channels = dims["dim_channel"][
        dims["dim_channel"]["channel_type"].isin(["digital", "marketplace"])
    ]["channel_id"].values

    current_products = dims["dim_product"][dims["dim_product"]["is_current"]][
        "product_id"
    ].values
    current_customers = dims["dim_customer"][dims["dim_customer"]["is_current"]][
        "customer_id"
    ].values

    # 5 % conversion rate implies ~20 sessions per online order
    sessions_per_order = 20

    rows: list[dict] = []
    event_key = 1
    session_counter = 1

    for dt in pd.date_range(config.start_date, config.end_date).date:
        month = dt.month
        dow = date(dt.year, dt.month, dt.day).weekday()
        seasonal_mult = MONTHLY_DEMAND[month]
        day_mult = 1.30 if dow == 5 else (1.10 if dow == 6 else 1.00)

        # Online orders are ~60 % of avg_daily_orders
        n_online_orders = int(config.avg_daily_orders * 0.60 * seasonal_mult * day_mult)
        n_sessions = int(rng.poisson(n_online_orders * sessions_per_order))

        for _ in range(n_sessions):
            session_id = f"SES-{session_counter:010d}"
            session_counter += 1
            channel_id = str(rng.choice(digital_channels))
            device = str(rng.choice(DEVICE_TYPES, p=DEVICE_WEIGHTS))
            duration = int(rng.integers(10, 900))

            # Anonymous 30 % of the time
            customer_id = (
                str(rng.choice(current_customers)) if rng.random() > 0.30 else None
            )

            # Funnel: each stage probabilistically reached
            reached_product_view = rng.random() < FUNNEL_REACH["product_view"]
            reached_add_to_cart = reached_product_view and rng.random() < (
                FUNNEL_REACH["add_to_cart"] / FUNNEL_REACH["product_view"]
            )
            reached_checkout = reached_add_to_cart and rng.random() < (
                FUNNEL_REACH["checkout_start"] / FUNNEL_REACH["add_to_cart"]
            )
            reached_purchase = reached_checkout and rng.random() < (
                FUNNEL_REACH["purchase"] / FUNNEL_REACH["checkout_start"]
            )
            abandoned = reached_add_to_cart and not reached_purchase

            base = {
                "session_id": session_id,
                "event_date": dt,
                "customer_id": customer_id,
                "channel_id": channel_id,
                "device_type": device,
                "session_duration_seconds": duration,
            }
            product_id = (
                str(rng.choice(current_products)) if reached_product_view else None
            )

            # Emit one row per event type reached in this session
            event_types = ["page_view"]
            if reached_product_view:
                event_types.append("product_view")
            if reached_add_to_cart:
                event_types.append("add_to_cart")
            if reached_checkout:
                event_types.append("checkout_start")
            if reached_purchase:
                event_types.append("purchase")
            if abandoned:
                event_types.append("abandon_cart")

            for evt in event_types:
                rows.append(
                    {
                        "event_key": event_key,
                        **base,
                        "product_id": product_id if evt not in ("page_view",) else None,
                        "event_type": evt,
                    }
                )
                event_key += 1

    return pd.DataFrame(rows)


# ── fact_markdown ─────────────────────────────────────────────────────────────


def generate_fact_markdown(
    config: VolumeConfig,
    rng: np.random.Generator,
    dims: dict[str, pd.DataFrame],
    fact_sales: pd.DataFrame,
) -> pd.DataFrame:
    """
    Markdown fact at product-store-week grain.

    Markdowns occur during clearance and sale promotion windows.
    Markdown depth increases toward end-of-season to clear residual stock.
    Only products that actually sold on markdown in a given week are included.
    """
    current_products = dims["dim_product"][dims["dim_product"]["is_current"]].copy()
    prod_price = current_products.set_index("product_id")["retail_price"].to_dict()
    prod_season = current_products.set_index("product_id")["season"].to_dict()

    # Build weekly sales aggregates to know which products sold each week
    sales_copy = fact_sales.copy()
    sales_copy["sale_date"] = pd.to_datetime(sales_copy["sale_date"])
    sales_copy["week_start"] = (
        sales_copy["sale_date"].dt.to_period("W").apply(lambda p: p.start_time.date())
    )
    weekly_sales = (
        sales_copy.groupby(["product_id", "store_id", "week_start"])["units_sold"]
        .sum()
        .reset_index()
    )

    rows: list[dict] = []
    markdown_key = 1

    # Identify clearance/sale weeks: July (SS clearance) and January/August (AW clearance)
    clearance_months = {7, 1, 8}
    all_weeks = sorted(weekly_sales["week_start"].unique())

    for week in all_weeks:
        month = week.month
        if month not in clearance_months:
            continue

        # SS products clear in July; AW products clear in Jan/Aug
        target_season_prefix = "SS" if month == 7 else "AW"

        week_sales = weekly_sales[weekly_sales["week_start"] == week]

        for _, row in week_sales.iterrows():
            pid = row["product_id"]
            sid = row["store_id"]
            if prod_season.get(pid, "")[:2] != target_season_prefix:
                continue
            if rng.random() > 0.60:  # 60 % of clearance-season SKUs are on markdown
                continue

            regular_price = prod_price.get(pid, 50.0)
            # Depth increases through the clearance period
            week_num_in_month = (week.day - 1) // 7 + 1
            base_depth = 0.20 + (week_num_in_month - 1) * 0.05
            depth = round(min(0.60, base_depth + float(rng.uniform(-0.05, 0.05))), 2)

            markdown_price = round(regular_price * (1 - depth), 2)
            units_on_markdown = int(row["units_sold"])
            revenue_on_markdown = round(units_on_markdown * markdown_price, 2)

            rows.append(
                {
                    "markdown_key": markdown_key,
                    "week_start_date": week,
                    "product_id": pid,
                    "store_id": sid,
                    "regular_price": regular_price,
                    "markdown_price": markdown_price,
                    "markdown_depth_pct": depth,
                    "units_sold_on_markdown": units_on_markdown,
                    "revenue_on_markdown": revenue_on_markdown,
                }
            )
            markdown_key += 1

    return pd.DataFrame(rows)
