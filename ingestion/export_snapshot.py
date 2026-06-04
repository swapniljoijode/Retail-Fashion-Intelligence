"""Export gold mart aggregations from DuckDB to JSON for the dashboard snapshot.

The dashboard reads these JSON files at build time — fully decoupled from the
warehouse.  Run this after every dbt build to refresh the snapshot.

CLI:
    python -m ingestion.export_snapshot
    python -m ingestion.export_snapshot --db-path data/fashion_retail.duckdb \\
                                         --output-dir dashboard/public/data

Output files (one per domain + one overview):
    overview.json    High-level KPIs + monthly revenue trend
    sales.json       Monthly trend, channel split, category split, top products
    marketing.json   Session funnel, device mix, monthly sessions, return reasons
    category.json    Margin, revenue, markdown depth by category
    planning.json    Inventory trend, sell-through, stockout by category/store
    placement.json   Revenue and stockout by region and store type
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()


# ── helpers ───────────────────────────────────────────────────────────────────


def _q(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    """Execute SQL and return list-of-dicts (JSON-serialisable)."""
    result = conn.execute(sql)
    cols = [d[0] for d in result.description]
    return [dict(zip(cols, row, strict=True)) for row in result.fetchall()]


def _scalar(conn: duckdb.DuckDBPyConnection, sql: str):
    return conn.execute(sql).fetchone()[0]


def _dump(output_dir: Path, name: str, payload: dict) -> None:
    path = output_dir / f"{name}.json"
    path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
    rows = sum(len(v) if isinstance(v, list) else 1 for v in payload.values())
    print(f"  {name}.json  ({rows} items)")


# ── domain exporters ──────────────────────────────────────────────────────────


def export_overview(conn: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    kpis = _q(
        conn,
        """
        SELECT
            SUM(gross_revenue)                                  AS gross_revenue,
            SUM(net_revenue)                                    AS net_revenue,
            SUM(cogs)                                           AS total_cogs,
            SUM(gross_margin)                                   AS total_gross_margin,
            SUM(gross_margin) / NULLIF(SUM(net_revenue), 0)    AS gross_margin_pct,
            COUNT(DISTINCT order_id)                            AS total_orders,
            SUM(units_sold)                                     AS total_units,
            SUM(net_revenue) / NULLIF(COUNT(DISTINCT order_id), 0) AS aov
        FROM marts.fct_sales
    """,
    )[0]

    returns = _q(
        conn,
        """
        SELECT
            SUM(units_returned)                                 AS total_units_returned,
            SUM(refund_value)                                   AS total_refund_value,
            COUNT(*)                                            AS total_returns
        FROM marts.fct_returns
    """,
    )[0]

    kpis["return_rate_units"] = (
        (returns["total_units_returned"] or 0) / kpis["total_units"]
        if kpis["total_units"]
        else 0
    )
    kpis["total_units_returned"] = returns["total_units_returned"]
    kpis["total_refund_value"] = returns["total_refund_value"]

    inv = _q(
        conn,
        """
        SELECT
            AVG(CASE WHEN is_stockout THEN 1.0 ELSE 0.0 END)   AS stockout_rate,
            SUM(units_on_hand)                                  AS total_units_on_hand
        FROM marts.fct_inventory_snapshot
    """,
    )[0]
    kpis["stockout_rate"] = inv["stockout_rate"]

    web = _q(
        conn,
        """
        SELECT
            COUNT(DISTINCT session_id)                          AS total_sessions,
            COUNT(DISTINCT CASE WHEN event_type='purchase' THEN session_id END)
                                                                AS purchase_sessions,
            COUNT(DISTINCT CASE WHEN event_type='purchase' THEN session_id END)
                / NULLIF(COUNT(DISTINCT session_id), 0)         AS conversion_rate
        FROM marts.fct_web_events
    """,
    )[0]
    kpis["total_web_sessions"] = web["total_sessions"]
    kpis["web_conversion_rate"] = web["conversion_rate"]

    kpis["unique_customers"] = _scalar(
        conn,
        "SELECT COUNT(DISTINCT customer_id) FROM marts.dim_customer WHERE is_current",
    )

    revenue_by_month = _q(
        conn,
        """
        SELECT
            EXTRACT(YEAR  FROM sale_date)::INTEGER              AS year,
            EXTRACT(MONTH FROM sale_date)::INTEGER              AS month,
            strftime(sale_date, '%b')                           AS label,
            SUM(gross_revenue)                                  AS gross_revenue,
            SUM(net_revenue)                                    AS net_revenue,
            SUM(gross_margin)                                   AS gross_margin,
            COUNT(DISTINCT order_id)                            AS orders,
            SUM(units_sold)                                     AS units
        FROM marts.fct_sales
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
    """,
    )

    _dump(
        output_dir,
        "overview",
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "kpis": kpis,
            "revenue_by_month": revenue_by_month,
        },
    )


def export_sales(conn: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    monthly_trend = _q(
        conn,
        """
        SELECT
            EXTRACT(YEAR  FROM s.sale_date)::INTEGER            AS year,
            EXTRACT(MONTH FROM s.sale_date)::INTEGER            AS month,
            strftime(s.sale_date, '%b %Y')                      AS label,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.net_revenue)                                  AS net_revenue,
            SUM(s.discount_amount)                              AS discount_amount,
            SUM(s.gross_margin)                                 AS gross_margin,
            SUM(s.gross_margin) / NULLIF(SUM(s.net_revenue),0) AS gross_margin_pct,
            COUNT(DISTINCT s.order_id)                          AS orders,
            SUM(s.units_sold)                                   AS units,
            SUM(s.net_revenue) / NULLIF(COUNT(DISTINCT s.order_id), 0) AS aov,
            SUM(s.discount_amount) / NULLIF(SUM(s.gross_revenue), 0)   AS discount_rate
        FROM marts.fct_sales s
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
    """,
    )

    by_channel = _q(
        conn,
        """
        SELECT
            c.channel_name,
            c.channel_type,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.net_revenue)                                  AS net_revenue,
            COUNT(DISTINCT s.order_id)                          AS orders,
            SUM(s.units_sold)                                   AS units,
            SUM(s.gross_revenue)
                / NULLIF(SUM(SUM(s.gross_revenue)) OVER (), 0) AS revenue_share
        FROM marts.fct_sales s
        JOIN marts.dim_channel c ON s.channel_key = c.channel_key
        GROUP BY 1, 2
        ORDER BY gross_revenue DESC
    """,
    )

    by_category = _q(
        conn,
        """
        SELECT
            p.category,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.net_revenue)                                  AS net_revenue,
            SUM(s.gross_margin) / NULLIF(SUM(s.net_revenue),0) AS gross_margin_pct,
            COUNT(DISTINCT s.order_id)                          AS orders,
            SUM(s.units_sold)                                   AS units
        FROM marts.fct_sales s
        JOIN marts.dim_product p ON s.product_key = p.product_key
        GROUP BY 1
        ORDER BY gross_revenue DESC
    """,
    )

    top_products = _q(
        conn,
        """
        SELECT
            p.product_name,
            p.sku,
            p.category,
            p.brand,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.units_sold)                                   AS units,
            SUM(s.gross_margin) / NULLIF(SUM(s.net_revenue),0) AS gross_margin_pct
        FROM marts.fct_sales s
        JOIN marts.dim_product p ON s.product_key = p.product_key
        WHERE p.is_current
        GROUP BY 1, 2, 3, 4
        ORDER BY gross_revenue DESC
        LIMIT 10
    """,
    )

    by_promotion = _q(
        conn,
        """
        SELECT
            pr.promotion_name,
            pr.promotion_type,
            pr.is_no_promotion,
            COUNT(DISTINCT s.order_id)                          AS orders,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.discount_amount)                              AS discount_amount,
            AVG(s.discount_amount / NULLIF(s.gross_revenue,0)) AS avg_discount_rate
        FROM marts.fct_sales s
        JOIN marts.dim_promotion pr ON s.promotion_key = pr.promotion_key
        GROUP BY 1, 2, 3
        ORDER BY orders DESC
    """,
    )

    _dump(
        output_dir,
        "sales",
        {
            "monthly_trend": monthly_trend,
            "by_channel": by_channel,
            "by_category": by_category,
            "top_products": top_products,
            "by_promotion": by_promotion,
        },
    )


def export_marketing(conn: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    monthly_sessions = _q(
        conn,
        """
        SELECT
            EXTRACT(YEAR  FROM event_date)::INTEGER             AS year,
            EXTRACT(MONTH FROM event_date)::INTEGER             AS month,
            strftime(event_date, '%b %Y')                       AS label,
            COUNT(DISTINCT session_id)                          AS sessions,
            COUNT(DISTINCT CASE WHEN event_type='purchase' THEN session_id END)
                                                                AS conversions,
            COUNT(DISTINCT CASE WHEN event_type='purchase' THEN session_id END)
                / NULLIF(COUNT(DISTINCT session_id)::DOUBLE, 0) AS conversion_rate
        FROM marts.fct_web_events
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
    """,
    )

    funnel = _q(
        conn,
        """
        SELECT
            event_type,
            COUNT(*)                                            AS events,
            COUNT(DISTINCT session_id)                          AS sessions
        FROM marts.fct_web_events
        GROUP BY 1
        ORDER BY events DESC
    """,
    )

    by_device = _q(
        conn,
        """
        SELECT
            device_type,
            COUNT(DISTINCT session_id)                          AS sessions,
            COUNT(DISTINCT session_id)
                / NULLIF(SUM(COUNT(DISTINCT session_id)) OVER ()::DOUBLE, 0)
                                                                AS share
        FROM marts.fct_web_events
        GROUP BY 1
        ORDER BY sessions DESC
    """,
    )

    returns_by_reason = _q(
        conn,
        """
        SELECT
            return_reason,
            COUNT(*)                                            AS returns,
            SUM(units_returned)                                 AS units_returned,
            SUM(refund_value)                                   AS refund_value
        FROM marts.fct_returns
        GROUP BY 1
        ORDER BY returns DESC
    """,
    )

    returns_by_month = _q(
        conn,
        """
        SELECT
            EXTRACT(YEAR  FROM return_date)::INTEGER            AS year,
            EXTRACT(MONTH FROM return_date)::INTEGER            AS month,
            strftime(return_date, '%b %Y')                      AS label,
            COUNT(*)                                            AS returns,
            SUM(units_returned)                                 AS units_returned,
            SUM(refund_value)                                   AS refund_value
        FROM marts.fct_returns
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
    """,
    )

    _dump(
        output_dir,
        "marketing",
        {
            "monthly_sessions": monthly_sessions,
            "funnel": funnel,
            "by_device": by_device,
            "returns_by_reason": returns_by_reason,
            "returns_by_month": returns_by_month,
        },
    )


def export_category(conn: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    by_category = _q(
        conn,
        """
        SELECT
            p.category,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.net_revenue)                                  AS net_revenue,
            SUM(s.gross_margin) / NULLIF(SUM(s.net_revenue),0) AS gross_margin_pct,
            SUM(s.units_sold)                                   AS units_sold,
            SUM(s.discount_amount) / NULLIF(SUM(s.gross_revenue),0) AS discount_rate
        FROM marts.fct_sales s
        JOIN marts.dim_product p ON s.product_key = p.product_key
        GROUP BY 1
        ORDER BY gross_revenue DESC
    """,
    )

    markdown_by_category = _q(
        conn,
        """
        SELECT
            p.category,
            AVG(m.markdown_depth_pct)                           AS avg_markdown_depth,
            SUM(m.units_sold_on_markdown)                       AS units_on_markdown,
            SUM(m.revenue_on_markdown)                          AS revenue_on_markdown,
            COUNT(*)                                            AS markdown_events
        FROM marts.fct_markdown m
        JOIN marts.dim_product p ON m.product_key = p.product_key
        GROUP BY 1
        ORDER BY revenue_on_markdown DESC
    """,
    )

    by_season = _q(
        conn,
        """
        SELECT
            p.season,
            LEFT(p.season, 2)                                   AS retail_season,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.gross_margin) / NULLIF(SUM(s.net_revenue),0) AS gross_margin_pct,
            SUM(s.units_sold)                                   AS units_sold
        FROM marts.fct_sales s
        JOIN marts.dim_product p ON s.product_key = p.product_key
        GROUP BY 1, 2
        ORDER BY gross_revenue DESC
    """,
    )

    _dump(
        output_dir,
        "category",
        {
            "by_category": by_category,
            "markdown_by_category": markdown_by_category,
            "by_season": by_season,
        },
    )


def export_planning(conn: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    # Weekly inventory trend — avg across all product-store pairs
    weekly_inventory = _q(
        conn,
        """
        SELECT
            EXTRACT(YEAR  FROM snapshot_date)::INTEGER          AS year,
            EXTRACT(WEEK  FROM snapshot_date)::INTEGER          AS week_num,
            MIN(snapshot_date)                                  AS week_start,
            strftime(MIN(snapshot_date), 'W%W %Y')             AS label,
            AVG(units_on_hand)                                  AS avg_units_on_hand,
            AVG(CASE WHEN is_stockout THEN 1.0 ELSE 0.0 END)   AS stockout_rate,
            SUM(units_in_transit)                               AS units_in_transit
        FROM marts.fct_inventory_snapshot
        GROUP BY 1, 2
        ORDER BY 1, 2
    """,
    )

    # Sell-through by category: units sold vs average stock
    sell_through = _q(
        conn,
        """
        WITH sales_agg AS (
            SELECT p.category,
                   SUM(s.units_sold) AS units_sold
            FROM marts.fct_sales s
            JOIN marts.dim_product p ON s.product_key = p.product_key
            GROUP BY 1
        ),
        stock_agg AS (
            SELECT p.category,
                   AVG(i.units_on_hand) AS avg_stock
            FROM marts.fct_inventory_snapshot i
            JOIN marts.dim_product p ON i.product_key = p.product_key
            GROUP BY 1
        )
        SELECT
            s.category,
            s.units_sold,
            k.avg_stock,
            s.units_sold / NULLIF(s.units_sold + k.avg_stock, 0) AS sell_through_rate
        FROM sales_agg s
        LEFT JOIN stock_agg k ON s.category = k.category
        ORDER BY sell_through_rate DESC
    """,
    )

    stockout_by_category = _q(
        conn,
        """
        SELECT
            p.category,
            AVG(CASE WHEN i.is_stockout THEN 1.0 ELSE 0.0 END) AS stockout_rate,
            SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END)      AS stockout_days,
            COUNT(*)                                             AS total_days
        FROM marts.fct_inventory_snapshot i
        JOIN marts.dim_product p ON i.product_key = p.product_key
        GROUP BY 1
        ORDER BY stockout_rate DESC
    """,
    )

    stockout_by_store = _q(
        conn,
        """
        SELECT
            st.store_type,
            st.region,
            AVG(CASE WHEN i.is_stockout THEN 1.0 ELSE 0.0 END) AS stockout_rate,
            AVG(i.units_on_hand)                                AS avg_units_on_hand
        FROM marts.fct_inventory_snapshot i
        JOIN marts.dim_store st ON i.store_key = st.store_key
        GROUP BY 1, 2
        ORDER BY stockout_rate DESC
    """,
    )

    _dump(
        output_dir,
        "planning",
        {
            "weekly_inventory": weekly_inventory,
            "sell_through": sell_through,
            "stockout_by_category": stockout_by_category,
            "stockout_by_store": stockout_by_store,
        },
    )


def export_placement(conn: duckdb.DuckDBPyConnection, output_dir: Path) -> None:
    by_region = _q(
        conn,
        """
        SELECT
            st.region,
            COUNT(DISTINCT st.store_id)                         AS stores,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.net_revenue)                                  AS net_revenue,
            SUM(s.units_sold)                                   AS units_sold,
            SUM(s.gross_revenue) / NULLIF(COUNT(DISTINCT st.store_id), 0) AS revenue_per_store
        FROM marts.fct_sales s
        JOIN marts.dim_store st ON s.store_key = st.store_key
        GROUP BY 1
        ORDER BY gross_revenue DESC
    """,
    )

    by_store_type = _q(
        conn,
        """
        SELECT
            st.store_type,
            st.size_band,
            COUNT(DISTINCT st.store_id)                         AS stores,
            AVG(st.square_footage)                              AS avg_sqft,
            SUM(s.gross_revenue)                                AS gross_revenue,
            SUM(s.units_sold)                                   AS units_sold,
            SUM(s.gross_revenue) / NULLIF(COUNT(DISTINCT st.store_id), 0) AS revenue_per_store
        FROM marts.fct_sales s
        JOIN marts.dim_store st ON s.store_key = st.store_key
        GROUP BY 1, 2
        ORDER BY gross_revenue DESC
    """,
    )

    inventory_by_region = _q(
        conn,
        """
        SELECT
            st.region,
            AVG(i.units_on_hand)                                AS avg_units_on_hand,
            AVG(CASE WHEN i.is_stockout THEN 1.0 ELSE 0.0 END) AS stockout_rate,
            SUM(i.units_in_transit)                             AS total_in_transit
        FROM marts.fct_inventory_snapshot i
        JOIN marts.dim_store st ON i.store_key = st.store_key
        GROUP BY 1
        ORDER BY avg_units_on_hand DESC
    """,
    )

    revenue_vs_stock_by_region = _q(
        conn,
        """
        WITH rev AS (
            SELECT st.region,
                   SUM(s.gross_revenue)     AS gross_revenue,
                   SUM(s.gross_revenue) / NULLIF(SUM(SUM(s.gross_revenue)) OVER (), 0) AS revenue_share
            FROM marts.fct_sales s
            JOIN marts.dim_store st ON s.store_key = st.store_key
            GROUP BY 1
        ),
        stk AS (
            SELECT st.region,
                   AVG(i.units_on_hand)    AS avg_stock,
                   AVG(i.units_on_hand) / NULLIF(SUM(AVG(i.units_on_hand)) OVER (), 0) AS stock_share
            FROM marts.fct_inventory_snapshot i
            JOIN marts.dim_store st ON i.store_key = st.store_key
            GROUP BY 1
        )
        SELECT
            r.region,
            r.gross_revenue,
            r.revenue_share,
            s.avg_stock,
            s.stock_share,
            r.revenue_share - s.stock_share AS revenue_stock_imbalance
        FROM rev r JOIN stk s ON r.region = s.region
        ORDER BY revenue_stock_imbalance DESC
    """,
    )

    _dump(
        output_dir,
        "placement",
        {
            "by_region": by_region,
            "by_store_type": by_store_type,
            "inventory_by_region": inventory_by_region,
            "revenue_vs_stock_by_region": revenue_vs_stock_by_region,
        },
    )


# ── main ──────────────────────────────────────────────────────────────────────


def run_export(db_path: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path, read_only=True)

    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Exporting snapshot from {db_path}")
    print(f"Output directory:        {output_dir}")
    print(f"Timestamp:               {ts}\n")

    export_overview(conn, output_dir)
    export_sales(conn, output_dir)
    export_marketing(conn, output_dir)
    export_category(conn, output_dir)
    export_planning(conn, output_dir)
    export_placement(conn, output_dir)

    conn.close()
    print(f"\nSnapshot written to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export DuckDB gold marts to JSON for the dashboard",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv("DUCKDB_PATH", "data/fashion_retail.duckdb"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dashboard/public/data"),
    )
    args = parser.parse_args()
    run_export(args.db_path, args.output_dir)


if __name__ == "__main__":
    main()
