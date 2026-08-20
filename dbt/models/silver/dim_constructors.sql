{{ config(
    materialized='table',
    unique_key='constructor_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'constructors') }}
),
cleaned as (
    select
        "constructorId"::bigint as constructor_id,
        "constructorRef" as constructor_ref,
        name,
        nationality,
        url,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned