# Metric Dictionary — Fashion Retail Intelligence Platform

**Version:** 1.0 | **Phase:** 1 | **Status:** Locked

Every KPI used in the dashboard and marts is defined here before data generation begins. This is the single source of truth. Any metric not in this dictionary does not exist in the platform. Changes require a version bump and a note on what changed and why.

Columns in each table:
- **Name** — the exact identifier used in dbt models and the dashboard
- **Definition** — what it measures in plain English
- **Formula** — SQL-expressible calculation
- **Grain** — the level at which the metric is meaningful
- **Additive** — whether it can be summed across dimensions without distortion
- **Owning mart** — the primary mart that exposes this metric

---

## Sales Mart Metrics

| # | Name | Definition | Formula | Grain | Additive | Owning mart |
|---|---|---|---|---|---|---|
| S1 | gross_revenue | Total revenue before any discounts or returns | `SUM(fact_sales.gross_revenue)` | Order line, any rollup | Yes | mart_sales |
| S2 | discount_amount | Total value of discounts applied | `SUM(fact_sales.discount_amount)` | Order line, any rollup | Yes | mart_sales |
| S3 | net_revenue | Revenue after discounts, before returns | `SUM(fact_sales.net_revenue)` | Order line, any rollup | Yes | mart_sales |
| S4 | cogs | Total cost of goods sold | `SUM(fact_sales.cogs)` | Order line, any rollup | Yes | mart_sales |
| S5 | gross_margin | Net revenue minus COGS | `SUM(fact_sales.gross_margin)` | Order line, any rollup | Yes | mart_sales |
| S6 | gross_margin_pct | Gross margin as a percentage of net revenue | `SUM(gross_margin) / NULLIF(SUM(net_revenue), 0)` | Any rollup | No (ratio) | mart_sales |
| S7 | units_sold | Total units purchased | `SUM(fact_sales.units_sold)` | Order line, any rollup | Yes | mart_sales |
| S8 | transaction_count | Number of distinct orders | `COUNT(DISTINCT fact_sales.order_id)` | Any rollup | Yes | mart_sales |
| S9 | average_order_value | Average net revenue per order | `SUM(net_revenue) / NULLIF(COUNT(DISTINCT order_id), 0)` | Any rollup | No (ratio) | mart_sales |
| S10 | average_units_per_order | Average number of units per order | `SUM(units_sold) / NULLIF(COUNT(DISTINCT order_id), 0)` | Any rollup | No (ratio) | mart_sales |
| S11 | discount_rate | Proportion of gross revenue given away as discount | `SUM(discount_amount) / NULLIF(SUM(gross_revenue), 0)` | Any rollup | No (ratio) | mart_sales |
| S12 | revenue_on_promotion | Net revenue from promoted order lines | `SUM(net_revenue) WHERE promotion_key != -1` | Any rollup | Yes | mart_sales |
| S13 | promotion_penetration | Share of revenue that came through a promotion | `SUM(net_revenue WHERE promotion) / NULLIF(SUM(net_revenue), 0)` | Any rollup | No (ratio) | mart_sales |

---

## Marketing Mart Metrics

| # | Name | Definition | Formula | Grain | Additive | Owning mart |
|---|---|---|---|---|---|---|
| M1 | sessions | Distinct browser sessions | `COUNT(DISTINCT fact_web_events.session_id)` | Any rollup | Yes | mart_marketing |
| M2 | product_views | Sessions that included at least one product_view event | `COUNT(DISTINCT session_id WHERE event_type = 'product_view')` | Any rollup | Yes | mart_marketing |
| M3 | add_to_cart_sessions | Sessions with at least one add_to_cart event | `COUNT(DISTINCT session_id WHERE event_type = 'add_to_cart')` | Any rollup | Yes | mart_marketing |
| M4 | purchase_sessions | Sessions that completed a purchase | `COUNT(DISTINCT session_id WHERE event_type = 'purchase')` | Any rollup | Yes | mart_marketing |
| M5 | abandon_cart_sessions | Sessions with add_to_cart but no purchase | `COUNT(DISTINCT session_id WHERE add_to_cart AND NOT purchase)` | Any rollup | Yes | mart_marketing |
| M6 | conversion_rate | Share of sessions that resulted in a purchase | `purchase_sessions / NULLIF(sessions, 0)` | Any rollup | No (ratio) | mart_marketing |
| M7 | add_to_cart_rate | Share of sessions that added to cart | `add_to_cart_sessions / NULLIF(sessions, 0)` | Any rollup | No (ratio) | mart_marketing |
| M8 | cart_abandonment_rate | Share of add-to-cart sessions that did not purchase | `abandon_cart_sessions / NULLIF(add_to_cart_sessions, 0)` | Any rollup | No (ratio) | mart_marketing |
| M9 | new_customers | Customers whose first_purchase_date falls in the period | `COUNT(DISTINCT customer_id WHERE first_purchase_date IN period)` | Period, channel, region | Yes | mart_marketing |
| M10 | returning_customers | Customers who purchased in the period but first purchased before it | `COUNT(DISTINCT customer_id) - new_customers` | Period, channel | Yes | mart_marketing |
| M11 | new_customer_pct | Share of purchasing customers who are new | `new_customers / NULLIF(new_customers + returning_customers, 0)` | Period, channel | No (ratio) | mart_marketing |
| M12 | revenue_by_channel | Net revenue attributed to each channel | `SUM(net_revenue) GROUP BY channel_key` | Channel, period | Yes | mart_marketing |
| M13 | units_returned | Total units returned | `SUM(fact_returns.units_returned)` | Any rollup | Yes | mart_marketing |
| M14 | refund_value | Total value of refunds issued | `SUM(fact_returns.refund_value)` | Any rollup | Yes | mart_marketing |
| M15 | return_rate_units | Units returned as a proportion of units sold | `SUM(units_returned) / NULLIF(SUM(units_sold), 0)` | Product, channel, period | No (ratio) | mart_marketing |
| M16 | return_rate_value | Refund value as a proportion of net revenue | `SUM(refund_value) / NULLIF(SUM(net_revenue), 0)` | Any rollup | No (ratio) | mart_marketing |

---

## Category Management Mart Metrics

| # | Name | Definition | Formula | Grain | Additive | Owning mart |
|---|---|---|---|---|---|---|
| C1 | category_net_revenue | Net revenue within a category | `SUM(net_revenue) GROUP BY category` | Category, period | Yes | mart_category |
| C2 | category_gross_margin | Gross margin within a category | `SUM(gross_margin) GROUP BY category` | Category, period | Yes | mart_category |
| C3 | category_gross_margin_pct | Gross margin % within a category | `SUM(gross_margin) / NULLIF(SUM(net_revenue), 0) BY category` | Category, period | No (ratio) | mart_category |
| C4 | category_units_sold | Units sold within a category | `SUM(units_sold) GROUP BY category` | Category, period | Yes | mart_category |
| C5 | space_to_sales_ratio | Net revenue per square foot of selling space | `SUM(net_revenue) / NULLIF(SUM(square_footage), 0)` | Store, period | No (ratio) | mart_category |
| C6 | category_sell_through_rate | Units sold as a share of total intake (sold + on hand) | `SUM(units_sold) / NULLIF(SUM(units_sold) + AVG(units_on_hand), 0)` | Category, store, period | No (ratio) | mart_category |
| C7 | markdown_depth_avg | Average markdown depth across markdown events | `AVG(fact_markdown.markdown_depth_pct)` | Category, store, week | No (average) | mart_category |
| C8 | revenue_on_markdown | Revenue earned on marked-down product | `SUM(fact_markdown.revenue_on_markdown)` | Category, store, week | Yes | mart_category |
| C9 | markdown_penetration | Share of category revenue sold on markdown | `SUM(revenue_on_markdown) / NULLIF(SUM(category_net_revenue), 0)` | Category, period | No (ratio) | mart_category |
| C10 | top_mover_rank | Rank of product by net revenue within its category and period | `RANK() OVER (PARTITION BY category, period ORDER BY net_revenue DESC)` | Product, category, period | N/A (rank) | mart_category |

---

## Product Planning Mart Metrics

| # | Name | Definition | Formula | Grain | Additive | Owning mart |
|---|---|---|---|---|---|---|
| P1 | sell_through_rate | Units sold as a share of total available units (sold + on hand) | `SUM(units_sold) / NULLIF(SUM(units_sold) + SUM(units_on_hand), 0)` | Product, store, season | No (ratio) | mart_product_planning |
| P2 | units_on_hand | Current stock position (latest snapshot) | `SUM(units_on_hand) WHERE date_key = latest_snapshot_date` | Product, store | Semi-additive | mart_product_planning |
| P3 | units_in_transit | Units shipped from supplier but not yet received | `SUM(units_in_transit) WHERE date_key = latest_snapshot_date` | Product, store | Semi-additive | mart_product_planning |
| P4 | rate_of_sale | Average units sold per trading day | `SUM(units_sold) / NULLIF(COUNT(DISTINCT trading_days), 0)` | Product, store, period | No (rate) | mart_product_planning |
| P5 | weeks_of_supply | How many weeks of stock remain at the current rate of sale | `SUM(units_on_hand) / NULLIF(rate_of_sale * 7, 0)` | Product, store | No (ratio) | mart_product_planning |
| P6 | stockout_flag | Whether a product is currently out of stock | `MAX(is_stockout) WHERE date_key = latest_snapshot_date` | Product, store | N/A (flag) | mart_product_planning |
| P7 | stockout_days | Number of days a product was out of stock in a period | `COUNT(date_key WHERE is_stockout = TRUE)` | Product, store, period | Yes | mart_product_planning |
| P8 | size_curve_share | Share of units sold in each size within a product-category | `SUM(units_sold BY size) / NULLIF(SUM(units_sold), 0)` | Product, category, season | No (ratio) | mart_product_planning |
| P9 | target_sell_through | Planned sell-through rate (static target, seeded) | Seed value per category and season | Product category, season | N/A (target) | mart_product_planning |
| P10 | sell_through_vs_target | Actual sell-through minus target | `sell_through_rate - target_sell_through` | Product, season | No (delta) | mart_product_planning |

---

## Placement Mart Metrics

| # | Name | Definition | Formula | Grain | Additive | Owning mart |
|---|---|---|---|---|---|---|
| PL1 | regional_revenue_share | Region's net revenue as a share of total estate revenue | `SUM(net_revenue BY region) / NULLIF(SUM(net_revenue), 0)` | Region, period | No (ratio) | mart_placement |
| PL2 | regional_stock_share | Region's units on hand as a share of total estate stock | `SUM(units_on_hand BY region) / NULLIF(SUM(units_on_hand), 0)` | Region, latest snapshot | No (ratio) | mart_placement |
| PL3 | stock_revenue_imbalance | Difference between stock share and revenue share by region | `regional_stock_share - regional_revenue_share` | Region, period | No (delta) | mart_placement |
| PL4 | stockout_rate | Share of product-store-days where a product was out of stock | `COUNT(is_stockout = TRUE) / NULLIF(COUNT(*), 0)` | Product, store, period | No (ratio) | mart_placement |
| PL5 | allocation_index | Store's actual units received as a proportion of its demand-weighted entitlement | `store_units_received / NULLIF(demand_weighted_entitlement, 0)` | Store, product, period | No (ratio) | mart_placement |
| PL6 | replenishment_coverage | Units in transit as a fraction of current on-hand, indicating how topped-up the pipeline is | `SUM(units_in_transit) / NULLIF(SUM(units_on_hand), 0)` | Store, product | No (ratio) | mart_placement |
| PL7 | inventory_turns | How many times inventory sold through in a period | `SUM(cogs) / NULLIF(AVG(units_on_hand * unit_cost), 0)` | Store, category, period | No (ratio) | mart_placement |
| PL8 | transfer_candidate_flag | Flag for products that are overstocked in one region and understocked in another | Derived: stockout in region A AND weeks_of_supply > threshold in region B | Product, region | N/A (flag) | mart_placement |

---

## Cross-Mart Shared Metrics

These metrics are computed identically in multiple marts and must always use the same formula.

| Name | Shared by | Canonical formula |
|---|---|---|
| net_revenue | All five marts | `SUM(fact_sales.net_revenue)` |
| gross_margin_pct | mart_sales, mart_category | `SUM(gross_margin) / NULLIF(SUM(net_revenue), 0)` |
| units_sold | mart_sales, mart_category, mart_product_planning | `SUM(fact_sales.units_sold)` |
| sell_through_rate | mart_category, mart_product_planning | `SUM(units_sold) / NULLIF(SUM(units_sold) + SUM(units_on_hand), 0)` |
| return_rate_units | mart_marketing, mart_sales | `SUM(units_returned) / NULLIF(SUM(units_sold), 0)` |

---

## Metric Governance Rules

1. **One definition per metric.** If two marts need the same number, they both reference the same intermediate model — not two independently written calculations.
2. **No metric in a dashboard that is not in this dictionary.** If a chart needs a number, define it here first.
3. **Ratio metrics are never additive.** Always recompute numerator and denominator separately before dividing — never average a ratio.
4. **Semi-additive metrics (inventory snapshots) must state the aggregation method.** Use the latest available snapshot for point-in-time values; use a daily average for period-over-period comparisons.
5. **NULL-safe denominators.** All division uses `NULLIF(denominator, 0)` to prevent division-by-zero errors silently propagating.
