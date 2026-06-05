SELECT
    customer_key,
    customer_id,
    customer_segment,
    loyalty_tier,
    region,
    city,
    acquisition_channel,
    first_purchase_date,
    is_current,
    effective_date,
    expiry_date,

    count(*) OVER (PARTITION BY customer_id) AS version_count,
    count(*) OVER (PARTITION BY customer_id) > 1 AS had_segment_change

FROM {{ ref('stg_bronze__dim_customer') }}
