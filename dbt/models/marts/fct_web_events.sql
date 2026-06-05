-- Grain: one row per session event.
-- customer_key is nullable (anonymous sessions).
-- product_key is nullable (page_view events have no product context).

WITH stg_web AS (
    SELECT * FROM {{ ref('stg_bronze__fact_web_events') }}
),

dim_customer AS (
    SELECT
        customer_key,
        customer_id,
        effective_date,
        expiry_date
    FROM {{ ref('int_customer__scd2_surrogate') }}
),

dim_channel AS (
    SELECT
        channel_key,
        channel_id
    FROM {{ ref('stg_bronze__dim_channel') }}
),

dim_product AS (
    SELECT
        product_key,
        product_id,
        effective_date,
        expiry_date
    FROM {{ ref('int_product__scd2_surrogate') }}
)

SELECT
    w.event_key,
    w.session_id,
    w.event_date,

    -- Nullable surrogate keys
    c.customer_key,
    p.product_key,
    w.customer_id,

    w.channel_id,
    w.device_type,
    w.session_duration_seconds,
    w.product_id,
    w.event_type,
    coalesce(ch.channel_key, -1) AS channel_key

FROM stg_web AS w

LEFT JOIN dim_customer AS c
    ON
        w.customer_id = c.customer_id
        AND w.event_date >= c.effective_date
        AND (w.event_date <= c.expiry_date OR c.expiry_date IS null)

LEFT JOIN dim_channel AS ch
    ON w.channel_id = ch.channel_id

LEFT JOIN dim_product AS p
    ON
        w.product_id = p.product_id
        AND w.event_date >= p.effective_date
        AND (w.event_date <= p.expiry_date OR p.expiry_date IS null)
