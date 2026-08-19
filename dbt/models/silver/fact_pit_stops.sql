{{ config(
    materialized='table',
    schema='silver'
) }}

with bronze as (
    select * from {{ source('bronze', 'pit_stops') }}
),
cleaned as (
    select
        "raceId"::bigint as race_id,
        "driverId"::bigint as driver_id,
        stop::smallint as stop_number,
        lap::smallint as lap_number,
        time as stop_time,
        duration as stop_duration,
        "milliseconds"::bigint as stop_milliseconds,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned