SELECT
    date_key,
    date,
    day_of_week,
    day_name,
    day_of_month,
    day_of_year,
    week_of_year,
    month_number,
    month_name,
    quarter_number,
    year,
    retail_season,
    calendar_season,
    is_weekend,
    is_public_holiday,
    holiday_name,
    trading_day_of_week,

    -- Derived convenience flags
    coalesce(is_weekend = false AND is_public_holiday = false,
    FALSE) AS is_trading_day,

    -- Composite period keys for pre-aggregated queries
    cast(year AS varchar) || '-Q'
    || cast(quarter_number AS varchar) AS year_quarter_label,
    year * 100 + quarter_number AS year_quarter_key,
    year * 100 + month_number AS year_month_key

FROM {{ ref('stg_bronze__dim_date') }}
