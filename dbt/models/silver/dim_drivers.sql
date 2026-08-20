{{ config(
    materialized='table',
    unique_key='driver_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'drivers') }}
),
cleaned as (
    select
        "driverId"::bigint as driver_id,
        "driverRef" as driver_ref,
        nullif(number, '')::int as driver_number,
        code,
        forename,
        surname,
        dob::date as date_of_birth,
        nationality,
        url,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned