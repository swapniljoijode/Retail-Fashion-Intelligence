-- Cleaning applied:
--   units_sold: TRY_CAST(VARCHAR → INTEGER) — ~3 % of rows stored as string
--               due to type-drift dirtiness injected in Phase 2.
--               Rows where cast fails (non-numeric strings) are excluded.
-- Deduplication: ~0.8 % duplicate rows injected; QUALIFY removes them.

WITH source AS (
    SELECT * FROM {{ source('bronze', 'fact_sales') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number() OVER (PARTITION BY sale_key ORDER BY _load_timestamp DESC)
        = 1
),

cleaned AS (
    SELECT
        sale_key,
        order_id,
        order_line_id,
        sale_date,
        product_id,
        store_id,
        customer_id,
        channel_id,
        promotion_id,
        unit_retail_price,
        gross_revenue,
        discount_amount,
        net_revenue,
        unit_cost,
        cogs,
        gross_margin,
        try_cast(units_sold AS integer) AS units_sold
    FROM deduped
    WHERE try_cast(units_sold AS integer) IS NOT null
)

SELECT * FROM cleaned
