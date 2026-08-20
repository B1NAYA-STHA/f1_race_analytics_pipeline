{{ config(
    materialized='table',
    unique_key='circuit_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'circuits') }}
),
cleaned as (
    select
        "circuitId"::bigint as circuit_id,
        "circuitRef" as circuit_ref,
        name,
        location,
        country,
        lat::double precision as latitude,
        lng::double precision as longitude,
        nullif(alt, '')::int as altitude,
        url,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned