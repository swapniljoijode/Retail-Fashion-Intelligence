-- Grain: one row per product × store × day.
-- Semi-additive measure: units_on_hand must be averaged (not summed) across
-- time. Sum across products or stores on a single day is valid.

WITH stg_inv AS (
    SELECT * FROM {{ ref('stg_bronze__fact_inventory_snapshot') }}
),

dim_product AS (
    SELECT
        product_key,
        product_id,
        effective_date,
        expiry_date
    FROM {{ ref('int_product__scd2_surrogate') }}
),

dim_store AS (
    SELECT
        store_key,
        store_id
    FROM {{ ref('stg_bronze__dim_store') }}
)

SELECT
    i.inventory_key,
    i.snapshot_date,

    i.product_id,
    i.store_id,

    i.units_on_hand,
    i.units_in_transit,

    i.units_on_order,
    i.reorder_point,
    i.is_stockout,
    coalesce(p.product_key, -1) AS product_key,
    coalesce(st.store_key, -1) AS store_key

FROM stg_inv AS i

LEFT JOIN dim_product AS p
    ON
        i.product_id = p.product_id
        AND i.snapshot_date >= p.effective_date
        AND (i.snapshot_date <= p.expiry_date OR p.expiry_date IS null)

LEFT JOIN dim_store AS st
    ON i.store_id = st.store_id
