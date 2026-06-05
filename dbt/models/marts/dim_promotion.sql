SELECT
    promotion_key,
    promotion_id,
    promotion_name,
    promotion_type,
    discount_pct,
    start_date,
    end_date,
    is_sitewide,

    promotion_id = 'NONE' AS is_no_promotion,

    -- Duration in days; NULL for the NONE sentinel
    CASE
        WHEN start_date IS NOT null AND end_date IS NOT null
            THEN datediff('day', start_date, end_date) + 1
    END AS duration_days

FROM {{ ref('stg_bronze__dim_promotion') }}
