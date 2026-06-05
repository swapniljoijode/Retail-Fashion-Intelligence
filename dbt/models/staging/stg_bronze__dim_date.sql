WITH source AS (
    SELECT * FROM {{ source('bronze', 'dim_date') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number() OVER (PARTITION BY date_key ORDER BY _load_timestamp DESC)
        = 1
)

SELECT
    date_key,
    cast(date AS date) AS date,
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
    cast(trading_day_of_week AS integer) AS trading_day_of_week

FROM deduped
