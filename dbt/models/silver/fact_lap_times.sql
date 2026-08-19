{{ config(
    materialized='table',
    schema='silver'
) }}

with bronze as (
    select * from {{ source('bronze', 'lap_times') }}
),
cleaned as (
    select
        "raceId"::bigint as race_id,
        "driverId"::bigint as driver_id,
        lap::smallint as lap_number,
        position::smallint as lap_position,
        time as lap_time,
        "milliseconds"::bigint as lap_milliseconds,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned