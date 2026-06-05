-- customer_id: nullable — ~30 % of sessions are anonymous.
-- product_id:  nullable — only populated when a product was viewed.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'fact_web_events') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number() OVER (PARTITION BY event_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    event_key,
    session_id,
    event_date,
    customer_id,
    channel_id,
    device_type,
    session_duration_seconds,
    product_id,
    event_type

FROM deduped
