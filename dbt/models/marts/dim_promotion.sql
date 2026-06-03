select
    promotion_key,
    promotion_id,
    promotion_name,
    promotion_type,
    discount_pct,
    start_date,
    end_date,
    is_sitewide,

    promotion_id = 'NONE'   as is_no_promotion,

    -- Duration in days; NULL for the NONE sentinel
    case
        when start_date is not null and end_date is not null
            then datediff('day', start_date, end_date) + 1
        else null
    end                     as duration_days

from {{ ref('stg_bronze__dim_promotion') }}
