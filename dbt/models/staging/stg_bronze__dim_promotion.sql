-- The NONE sentinel row (promotion_key = -1) is retained in staging.
-- Fact tables reference it when no promotion applied.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'dim_promotion') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY promotion_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    promotion_key,
    promotion_id,
    promotion_name,
    promotion_type,
    discount_pct,
    is_sitewide,
    try_cast(start_date AS date) AS start_date,
    try_cast(end_date AS date) AS end_date

FROM deduped
