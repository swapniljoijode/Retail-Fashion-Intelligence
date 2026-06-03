-- Grain: one row per product × store × week (clearance weeks only).
-- markdown_depth_pct increases toward end-of-season to clear residual stock.

with stg_md as (
    select * from {{ ref('stg_bronze__fact_markdown') }}
),

dim_product as (
    select product_key, product_id, effective_date, expiry_date
    from {{ ref('int_product__scd2_surrogate') }}
),

dim_store as (
    select store_key, store_id
    from {{ ref('stg_bronze__dim_store') }}
)

select
    m.markdown_key,
    m.week_start_date,

    coalesce(p.product_key, -1)     as product_key,
    coalesce(st.store_key,  -1)     as store_key,

    m.product_id,
    m.store_id,
    m.regular_price,
    m.markdown_price,
    m.markdown_depth_pct,
    m.units_sold_on_markdown,
    m.revenue_on_markdown

from stg_md m

left join dim_product p
    on  m.product_id        = p.product_id
    and m.week_start_date  >= p.effective_date
    and (m.week_start_date <= p.expiry_date or p.expiry_date is null)

left join dim_store st
    on m.store_id = st.store_id
