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
    expiry_date,

    count(*) over (partition by customer_id)     as version_count,
    count(*) over (partition by customer_id) > 1 as had_segment_change

from {{ ref('stg_bronze__dim_customer') }}
