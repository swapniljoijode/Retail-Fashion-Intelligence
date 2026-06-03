select
    store_key,
    store_id,
    store_name,
    region,
    city,
    country,
    store_type,
    square_footage,
    opening_date,

    -- Size band for space-to-sales analysis
    case
        when square_footage >= 3000 then 'large'
        when square_footage >= 1500 then 'medium'
        else 'small'
    end as size_band

from {{ ref('stg_bronze__dim_store') }}
