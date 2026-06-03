select
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
    case when is_weekend = false and is_public_holiday = false
        then true else false
    end                                         as is_trading_day,

    -- Composite period keys for pre-aggregated queries
    cast(year as varchar) || '-Q'
        || cast(quarter_number as varchar)      as year_quarter_label,
    year * 100 + quarter_number                 as year_quarter_key,
    year * 100 + month_number                   as year_month_key

from {{ ref('stg_bronze__dim_date') }}
