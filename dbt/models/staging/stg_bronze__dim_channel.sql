WITH source AS (
    SELECT * FROM {{ source('bronze', 'dim_channel') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY channel_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    channel_key,
    channel_id,
    channel_name,
    channel_type,
    platform

FROM deduped
