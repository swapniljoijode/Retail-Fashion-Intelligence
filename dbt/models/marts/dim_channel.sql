SELECT
    channel_key,
    channel_id,
    channel_name,
    channel_type,
    platform,
    channel_type IN ('digital', 'marketplace') AS is_digital

FROM {{ ref('stg_bronze__dim_channel') }}
