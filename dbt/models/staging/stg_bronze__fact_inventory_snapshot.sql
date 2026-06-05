-- Cleaning applied:
--   units_on_hand: TRY_CAST(VARCHAR → INTEGER) — ~2 % type-drift dirtiness.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'fact_inventory_snapshot') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY inventory_key ORDER BY _load_timestamp DESC)
        = 1
),

cleaned AS (
    SELECT
        inventory_key,
        snapshot_date,
        product_id,
        store_id,
        units_in_transit,
        units_on_order,
        reorder_point,
        is_stockout,
        try_cast(units_on_hand AS integer) AS units_on_hand
    FROM deduped
    WHERE try_cast(units_on_hand AS integer) IS NOT null
)

SELECT * FROM cleaned
