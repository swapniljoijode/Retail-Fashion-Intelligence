-- Grain: one row per product × store × week (clearance weeks only).
-- markdown_depth_pct increases toward end-of-season to clear residual stock.

WITH stg_md AS (
    SELECT * FROM {{ ref('stg_bronze__fact_markdown') }}
),

dim_product AS (
    SELECT
        product_key,
        product_id,
        effective_date,
        expiry_date
    FROM {{ ref('int_product__scd2_surrogate') }}
),

dim_store AS (
    SELECT
        store_key,
        store_id
    FROM {{ ref('stg_bronze__dim_store') }}
)

SELECT
    m.markdown_key,
    m.week_start_date,

    m.product_id,
    m.store_id,

    m.regular_price,
    m.markdown_price,
    m.markdown_depth_pct,
    m.units_sold_on_markdown,
    m.revenue_on_markdown,
    coalesce(p.product_key, -1) AS product_key,
    coalesce(st.store_key, -1) AS store_key

FROM stg_md AS m

LEFT JOIN dim_product AS p
    ON
        m.product_id = p.product_id
        AND m.week_start_date >= p.effective_date
        AND (m.week_start_date <= p.expiry_date OR p.expiry_date IS null)

LEFT JOIN dim_store AS st
    ON m.store_id = st.store_id
