-- Ephemeral model: extracts only the columns needed to resolve customer_id +
-- event_date → customer_key via an SCD Type 2 date-range join.
-- See int_product__scd2_surrogate for the join pattern.

SELECT
    customer_key,
    customer_id,
    effective_date,
    expiry_date

FROM {{ ref('stg_bronze__dim_customer') }}
