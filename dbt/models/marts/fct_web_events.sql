-- Grain: one row per session event.
-- customer_key is nullable (anonymous sessions).
-- product_key is nullable (page_view events have no product context).

with stg_web as (
    select * from {{ ref('stg_bronze__fact_web_events') }}
),

dim_customer as (
    select customer_key, customer_id, effective_date, expiry_date
    from {{ ref('int_customer__scd2_surrogate') }}
),

dim_channel as (
    select channel_key, channel_id
    from {{ ref('stg_bronze__dim_channel') }}
),

dim_product as (
    select product_key, product_id, effective_date, expiry_date
    from {{ ref('int_product__scd2_surrogate') }}
)

select
    w.event_key,
    w.session_id,
    w.event_date,

    -- Nullable surrogate keys
    c.customer_key,
    coalesce(ch.channel_key, -1)    as channel_key,
    p.product_key,

    w.customer_id,
    w.channel_id,
    w.device_type,
    w.session_duration_seconds,
    w.product_id,
    w.event_type

from stg_web w

left join dim_customer c
    on  w.customer_id  = c.customer_id
    and w.event_date  >= c.effective_date
    and (w.event_date <= c.expiry_date or c.expiry_date is null)

left join dim_channel ch
    on w.channel_id = ch.channel_id

left join dim_product p
    on  w.product_id  = p.product_id
    and w.event_date >= p.effective_date
    and (w.event_date <= p.expiry_date or p.expiry_date is null)
