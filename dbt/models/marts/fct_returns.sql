-- Grain: one row per return line.
-- Resolves product and customer surrogate keys at the return_date.

with stg_ret as (
    select * from {{ ref('stg_bronze__fact_returns') }}
),

dim_product as (
    select product_key, product_id, effective_date, expiry_date
    from {{ ref('int_product__scd2_surrogate') }}
),

dim_customer as (
    select customer_key, customer_id, effective_date, expiry_date
    from {{ ref('int_customer__scd2_surrogate') }}
),

dim_store as (
    select store_key, store_id
    from {{ ref('stg_bronze__dim_store') }}
),

dim_channel as (
    select channel_key, channel_id
    from {{ ref('stg_bronze__dim_channel') }}
)

select
    r.return_key,
    r.return_id,
    r.return_line_id,
    r.original_order_id,
    r.return_date,
    r.original_sale_date,

    coalesce(p.product_key,  -1)    as product_key,
    coalesce(st.store_key,   -1)    as store_key,
    coalesce(c.customer_key, -1)    as customer_key,
    coalesce(ch.channel_key, -1)    as channel_key,

    r.product_id,
    r.store_id,
    r.customer_id,
    r.channel_id,

    r.units_returned,
    r.refund_value,
    r.return_reason

from stg_ret r

left join dim_product p
    on  r.product_id    = p.product_id
    and r.return_date  >= p.effective_date
    and (r.return_date <= p.expiry_date or p.expiry_date is null)

left join dim_store st
    on r.store_id = st.store_id

left join dim_customer c
    on  r.customer_id   = c.customer_id
    and r.return_date  >= c.effective_date
    and (r.return_date <= c.expiry_date or c.expiry_date is null)

left join dim_channel ch
    on r.channel_id = ch.channel_id
