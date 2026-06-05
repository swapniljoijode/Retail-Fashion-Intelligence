-- Grain: one row per order line.
-- Surrogate keys are resolved via SCD Type 2 date-range joins so that
-- each line references the product price and customer segment that were
-- active at the time of sale.

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_bronze__fact_sales') }}
),

dim_product AS (
    SELECT
        product_key,
        product_id,
        effective_date,
        expiry_date
    FROM {{ ref('int_product__scd2_surrogate') }}
),

dim_customer AS (
    SELECT
        customer_key,
        customer_id,
        effective_date,
        expiry_date
    FROM {{ ref('int_customer__scd2_surrogate') }}
),

dim_store AS (
    SELECT
        store_key,
        store_id
    FROM {{ ref('stg_bronze__dim_store') }}
),

dim_channel AS (
    SELECT
        channel_key,
        channel_id
    FROM {{ ref('stg_bronze__dim_channel') }}
),

dim_promotion AS (
    SELECT
        promotion_key,
        promotion_id
    FROM {{ ref('stg_bronze__dim_promotion') }}
),

with_keys AS (
    SELECT
        s.sale_key,
        s.order_id,
        s.order_line_id,
        s.sale_date,

        -- Surrogate keys
        s.product_id,
        s.store_id,
        s.customer_id,
        s.channel_id,
        s.promotion_id,

        -- Natural keys retained for auditability
        s.units_sold,
        s.unit_retail_price,
        s.gross_revenue,
        s.discount_amount,
        s.net_revenue,

        -- Measures
        s.unit_cost,
        s.cogs,
        s.gross_margin,
        coalesce(p.product_key, -1) AS product_key,
        coalesce(st.store_key, -1) AS store_key,
        coalesce(c.customer_key, -1) AS customer_key,
        coalesce(ch.channel_key, -1) AS channel_key,
        coalesce(pr.promotion_key, -1) AS promotion_key

    FROM stg_sales AS s

    LEFT JOIN dim_product AS p
        ON
            s.product_id = p.product_id
            AND s.sale_date >= p.effective_date
            AND (s.sale_date <= p.expiry_date OR p.expiry_date IS null)

    LEFT JOIN dim_store AS st
        ON s.store_id = st.store_id

    LEFT JOIN dim_customer AS c
        ON
            s.customer_id = c.customer_id
            AND s.sale_date >= c.effective_date
            AND (s.sale_date <= c.expiry_date OR c.expiry_date IS null)

    LEFT JOIN dim_channel AS ch
        ON s.channel_id = ch.channel_id

    LEFT JOIN dim_promotion AS pr
        ON s.promotion_id = pr.promotion_id
)

SELECT * FROM with_keys
