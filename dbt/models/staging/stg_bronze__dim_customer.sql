-- Intentional nulls retained:
--   region: ~5 % null (dirtiness module)
--   city:   ~4 % null (dirtiness module)
-- These represent customers with unknown geography and are valid silver data.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'dim_customer') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY customer_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    customer_key,
    customer_id,
    customer_segment,
    loyalty_tier,
    region,
    city,
    acquisition_channel,
    cast(first_purchase_date AS date) AS first_purchase_date,
    is_current,
    cast(effective_date AS date) AS effective_date,
    try_cast(expiry_date AS date) AS expiry_date

FROM deduped
