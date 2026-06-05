WITH source AS (
    SELECT * FROM {{ source('bronze', 'dim_store') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number() OVER (PARTITION BY store_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    store_key,
    store_id,
    store_name,
    region,
    city,
    country,
    store_type,
    square_footage,
    opening_date

FROM deduped
