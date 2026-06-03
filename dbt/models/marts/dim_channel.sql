select
    channel_key,
    channel_id,
    channel_name,
    channel_type,
    platform,
    channel_type in ('digital', 'marketplace') as is_digital

from {{ ref('stg_bronze__dim_channel') }}
