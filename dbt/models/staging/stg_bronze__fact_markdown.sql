-- Only populated for clearance months: January (AW), July and August (SS).
-- Empty for periods outside those windows.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'fact_markdown') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY markdown_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    markdown_key,
    week_start_date,
    product_id,
    store_id,
    regular_price,
    markdown_price,
    markdown_depth_pct,
    units_sold_on_markdown,
    revenue_on_markdown

FROM deduped
