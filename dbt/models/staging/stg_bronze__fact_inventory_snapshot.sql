-- Cleaning applied:
--   units_on_hand: TRY_CAST(VARCHAR → INTEGER) — ~2 % type-drift dirtiness.

with source as (
    select * from {{ source('bronze', 'fact_inventory_snapshot') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by inventory_key order by _load_timestamp desc) = 1
),

cleaned as (
    select
        inventory_key,
        snapshot_date,
        product_id,
        store_id,
        try_cast(units_on_hand as integer)  as units_on_hand,
        units_in_transit,
        units_on_order,
        reorder_point,
        is_stockout
    from deduped
    where try_cast(units_on_hand as integer) is not null
)

select * from cleaned
