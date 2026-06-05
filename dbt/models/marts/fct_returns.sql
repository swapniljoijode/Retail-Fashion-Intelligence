-- Grain: one row per return line.
-- Resolves product and customer surrogate keys at the return_date.

WITH stg_ret AS (
    SELECT * FROM {{ ref('stg_bronze__fact_returns') }}
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
)

SELECT
    r.return_key,
    r.return_id,
    r.return_line_id,
    r.original_order_id,
    r.return_date,
    r.original_sale_date,

    r.product_id,
    r.store_id,
    r.customer_id,
    r.channel_id,

    r.units_returned,
    r.refund_value,
    r.return_reason,
    coalesce(p.product_key, -1) AS product_key,

    coalesce(st.store_key, -1) AS store_key,
    coalesce(c.customer_key, -1) AS customer_key,
    coalesce(ch.channel_key, -1) AS channel_key

FROM stg_ret AS r

LEFT JOIN dim_product AS p
    ON
        r.product_id = p.product_id
        AND r.return_date >= p.effective_date
        AND (r.return_date <= p.expiry_date OR p.expiry_date IS null)

LEFT JOIN dim_store AS st
    ON r.store_id = st.store_id

LEFT JOIN dim_customer AS c
    ON
        r.customer_id = c.customer_id
        AND r.return_date >= c.effective_date
        AND (r.return_date <= c.expiry_date OR c.expiry_date IS null)

LEFT JOIN dim_channel AS ch
    ON r.channel_id = ch.channel_id
