-- Grain: one row per product × store × day.
-- Semi-additive measure: units_on_hand must be averaged (not summed) across
-- time. Sum across products or stores on a single day is valid.

with stg_inv as (
    select * from {{ ref('stg_bronze__fact_inventory_snapshot') }}
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
    i.inventory_key,
    i.snapshot_date,

    coalesce(p.product_key, -1)     as product_key,
    coalesce(st.store_key,  -1)     as store_key,

    i.product_id,
    i.store_id,

    i.units_on_hand,
    i.units_in_transit,
    i.units_on_order,
    i.reorder_point,
    i.is_stockout

from stg_inv i

left join dim_product p
    on  i.product_id     = p.product_id
    and i.snapshot_date >= p.effective_date
    and (i.snapshot_date <= p.expiry_date or p.expiry_date is null)

left join dim_store st
    on i.store_id = st.store_id
