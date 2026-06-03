-- Grain: one row per order line.
-- Surrogate keys are resolved via SCD Type 2 date-range joins so that
-- each line references the product price and customer segment that were
-- active at the time of sale.

with stg_sales as (
    select * from {{ ref('stg_bronze__fact_sales') }}
),

dim_product as (
    select product_key, product_id, effective_date, expiry_date
    from {{ ref('int_product__scd2_surrogate') }}
),

dim_customer as (
    select customer_key, customer_id, effective_date, expiry_date
    from {{ ref('int_customer__scd2_surrogate') }}
),

dim_store as (
    select store_key, store_id
    from {{ ref('stg_bronze__dim_store') }}
),

dim_channel as (
    select channel_key, channel_id
    from {{ ref('stg_bronze__dim_channel') }}
),

dim_promotion as (
    select promotion_key, promotion_id
    from {{ ref('stg_bronze__dim_promotion') }}
),

with_keys as (
    select
        s.sale_key,
        s.order_id,
        s.order_line_id,
        s.sale_date,

        -- Surrogate keys
        coalesce(p.product_key,  -1)    as product_key,
        coalesce(st.store_key,   -1)    as store_key,
        coalesce(c.customer_key, -1)    as customer_key,
        coalesce(ch.channel_key, -1)    as channel_key,
        coalesce(pr.promotion_key, -1)  as promotion_key,

        -- Natural keys retained for auditability
        s.product_id,
        s.store_id,
        s.customer_id,
        s.channel_id,
        s.promotion_id,

        -- Measures
        s.units_sold,
        s.unit_retail_price,
        s.gross_revenue,
        s.discount_amount,
        s.net_revenue,
        s.unit_cost,
        s.cogs,
        s.gross_margin

    from stg_sales s

    left join dim_product p
        on  s.product_id    = p.product_id
        and s.sale_date    >= p.effective_date
        and (s.sale_date   <= p.expiry_date or p.expiry_date is null)

    left join dim_store st
        on s.store_id = st.store_id

    left join dim_customer c
        on  s.customer_id   = c.customer_id
        and s.sale_date    >= c.effective_date
        and (s.sale_date   <= c.expiry_date or c.expiry_date is null)

    left join dim_channel ch
        on s.channel_id = ch.channel_id

    left join dim_promotion pr
        on s.promotion_id = pr.promotion_id
)

select * from with_keys
