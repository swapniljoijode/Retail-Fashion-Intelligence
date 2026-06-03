-- customer_id: nullable — ~30 % of sessions are anonymous.
-- product_id:  nullable — only populated when a product was viewed.

with source as (
    select * from {{ source('bronze', 'fact_web_events') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by event_key order by _load_timestamp desc) = 1
)

select
    event_key,
    session_id,
    event_date,
    customer_id,
    channel_id,
    device_type,
    session_duration_seconds,
    product_id,
    event_type

from deduped
