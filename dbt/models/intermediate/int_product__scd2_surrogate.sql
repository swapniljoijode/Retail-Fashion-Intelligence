-- Ephemeral model: extracts only the columns needed to resolve product_id +
-- event_date → product_key via an SCD Type 2 date-range join.
--
-- The join condition in consuming fact models is:
--   fact.product_id = dim.product_id
--   AND fact.event_date >= dim.effective_date
--   AND (fact.event_date <= dim.expiry_date OR dim.expiry_date IS NULL)
--
-- This works because:
--   - Non-SCD products have one row with expiry_date = NULL.
--   - SCD products have an expired row (expiry_date set) and a current row
--     (expiry_date = NULL), so exactly one row matches any given date.

select
    product_key,
    product_id,
    effective_date,
    expiry_date

from {{ ref('stg_bronze__dim_product') }}
