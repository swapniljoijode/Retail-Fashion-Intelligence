-- Cleaning applied:
--   units_sold: TRY_CAST(VARCHAR → INTEGER) — ~3 % of rows stored as string
--               due to type-drift dirtiness injected in Phase 2.
--               Rows where cast fails (non-numeric strings) are excluded.
-- Deduplication: ~0.8 % duplicate rows injected; QUALIFY removes them.

with source as (
    select * from {{ source('bronze', 'fact_sales') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by sale_key order by _load_timestamp desc) = 1
),

cleaned as (
    select
        sale_key,
        order_id,
        order_line_id,
        sale_date,
        product_id,
        store_id,
        customer_id,
        channel_id,
        promotion_id,
        try_cast(units_sold as integer)     as units_sold,
        unit_retail_price,
        gross_revenue,
        discount_amount,
        net_revenue,
        unit_cost,
        cogs,
        gross_margin
    from deduped
    where try_cast(units_sold as integer) is not null
)

select * from cleaned
