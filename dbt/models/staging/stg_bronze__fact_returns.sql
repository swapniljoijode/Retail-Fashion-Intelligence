-- Deduplication: ~0.5 % duplicate rows injected by dirtiness module.

with source as (
    select * from {{ source('bronze', 'fact_returns') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by return_key order by _load_timestamp desc) = 1
)

select
    return_key,
    return_id,
    return_line_id,
    original_order_id,
    return_date,
    original_sale_date,
    product_id,
    store_id,
    customer_id,
    channel_id,
    units_returned,
    refund_value,
    return_reason

from deduped
