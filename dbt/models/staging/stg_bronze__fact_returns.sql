-- Deduplication: ~0.5 % duplicate rows injected by dirtiness module.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'fact_returns') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY return_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    return_key,
    return_id,
    return_line_id,
    original_order_id,
    return_date,
    original_sale_date,
    product_id,
    store_id,
    customer_id,
    channel_id,
    units_returned,
    refund_value,
    return_reason

FROM deduped
