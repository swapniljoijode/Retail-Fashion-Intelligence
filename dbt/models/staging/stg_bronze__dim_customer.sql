-- Intentional nulls retained:
--   region: ~5 % null (dirtiness module)
--   city:   ~4 % null (dirtiness module)
-- These represent customers with unknown geography and are valid silver data.

with source as (
    select * from {{ source('bronze', 'dim_customer') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by customer_key order by _load_timestamp desc) = 1
)

select
    customer_key,
    customer_id,
    customer_segment,
    loyalty_tier,
    region,
    city,
    acquisition_channel,
    cast(first_purchase_date as date)           as first_purchase_date,
    is_current,
    cast(effective_date as date)                as effective_date,
    try_cast(expiry_date as date)               as expiry_date

from deduped
