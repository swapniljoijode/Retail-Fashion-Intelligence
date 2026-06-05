-- Cleaning applied:
--   category: INITCAP(LOWER(...)) — normalises the ~8 % uppercase casing
--             injected by the dirtiness module back to Title Case.
--   color:    kept as-is; ~2 % nulls are intentional and valid for silver.
-- Deduplication: picks the latest bronze load version per product_key (surrogate).

WITH source AS (
    SELECT * FROM {{ source('bronze', 'dim_product') }}
),

deduped AS (
    SELECT *
    FROM source
    QUALIFY
        row_number()
            OVER (PARTITION BY product_key ORDER BY _load_timestamp DESC)
        = 1
),

cleaned AS (
    SELECT
        product_key,
        product_id,
        sku,
        product_name,
        subcategory,
        brand,
        color,
        size,
        season,
        cost_price,
        retail_price,
        margin_pct,
        is_current,
        cast(effective_date AS date) AS effective_date,
        -- Pyarrow stores all-null date columns as `null` type; DuckDB then reads
        -- them as INTEGER.  Explicit CASTs make the type DATE regardless of volume.
        upper(left(lower(category), 1))
        || lower(substring(category, 2)) AS category,
        try_cast(expiry_date AS date) AS expiry_date
    FROM deduped
)

SELECT * FROM cleaned
