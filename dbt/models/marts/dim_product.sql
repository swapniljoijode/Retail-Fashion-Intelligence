select
    product_key,
    product_id,
    sku,
    product_name,
    category,
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
    expiry_date,

    -- How many SCD versions exist for this product_id
    count(*) over (partition by product_id)     as version_count,

    -- Price change indicator: more than one version means a price change occurred
    count(*) over (partition by product_id) > 1 as had_price_change

from {{ ref('stg_bronze__dim_product') }}
