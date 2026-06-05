SELECT
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
    CASE
        WHEN square_footage >= 3000 THEN 'large'
        WHEN square_footage >= 1500 THEN 'medium'
        ELSE 'small'
    END AS size_band

FROM {{ ref('stg_bronze__dim_store') }}
