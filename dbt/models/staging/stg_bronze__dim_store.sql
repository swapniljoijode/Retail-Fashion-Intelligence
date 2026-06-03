with source as (
    select * from {{ source('bronze', 'dim_store') }}
),

deduped as (
    select *
    from source
    qualify row_number() over (partition by store_key order by _load_timestamp desc) = 1
)

select
    store_key,
    store_id,
    store_name,
    region,
    city,
    country,
    store_type,
    square_footage,
    opening_date

from deduped
