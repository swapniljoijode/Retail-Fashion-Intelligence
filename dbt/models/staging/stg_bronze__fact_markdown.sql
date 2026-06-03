-- Only populated for clearance months: January (AW), July and August (SS).
-- Empty for periods outside those windows.

with source as (
    select * from {{ source('bronze', 'fact_markdown') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by markdown_key order by _load_timestamp desc) = 1
)

select
    markdown_key,
    week_start_date,
    product_id,
    store_id,
    regular_price,
    markdown_price,
    markdown_depth_pct,
    units_sold_on_markdown,
    revenue_on_markdown

from deduped
