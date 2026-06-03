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
    first_purchase_date,
    is_current,
    effective_date,
    expiry_date

from deduped
