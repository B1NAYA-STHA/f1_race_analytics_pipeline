{{ config(
    materialized='table',
    schema='silver',
    unique_key='year'
) }}

with bronze as (
    select * from {{ source('bronze', 'seasons') }}
),
cleaned as (
    select
        year::int as year,
        url,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned