with source as (
    select * from {{ source('bronze', 'dim_channel') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by channel_key order by _load_timestamp desc) = 1
)

select
    channel_key,
    channel_id,
    channel_name,
    channel_type,
    platform

from deduped
