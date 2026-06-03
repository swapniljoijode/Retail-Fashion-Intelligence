with source as (
    select * from {{ source('bronze', 'dim_date') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by date_key order by _load_timestamp desc) = 1
)

select
    date_key,
    cast(date as date)                          as date,
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
    -- pandas .where() with other=None produces float64 (NaN for non-trading days).
    -- CAST converts NaN → NULL which is the correct representation.
    cast(trading_day_of_week as integer)        as trading_day_of_week

from deduped
