-- The NONE sentinel row (promotion_key = -1) is retained in staging.
-- Fact tables reference it when no promotion applied.

with source as (
    select * from {{ source('bronze', 'dim_promotion') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by promotion_key order by _load_timestamp desc) = 1
)

select
    promotion_key,
    promotion_id,
    promotion_name,
    promotion_type,
    discount_pct,
    try_cast(start_date as date)                as start_date,
    try_cast(end_date as date)                  as end_date,
    is_sitewide

from deduped
