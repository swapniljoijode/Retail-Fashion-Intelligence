-- Cleaning applied:
--   category: INITCAP(LOWER(...)) — normalises the ~8 % uppercase casing
--             injected by the dirtiness module back to Title Case.
--   color:    kept as-is; ~2 % nulls are intentional and valid for silver.
-- Deduplication: picks the latest bronze load version per product_key (surrogate).

with source as (
    select * from {{ source('bronze', 'dim_product') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by product_key order by _load_timestamp desc) = 1
),

cleaned as (
    select
        product_key,
        product_id,
        sku,
        product_name,
        upper(left(lower(category), 1)) || lower(substring(category, 2)) as category,
        subcategory,
        brand,
        color,
        size,
        season,
        cost_price,
        retail_price,
        margin_pct,
        is_current,
        effective_date,
        expiry_date
    from deduped
)

select * from cleaned
