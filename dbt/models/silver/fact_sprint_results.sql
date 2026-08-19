{{ config(
    materialized='table',
    schema='silver',
    unique_key='sprint_result_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'sprint_results') }}
),
cleaned as (
    select
        "sprintResultId"::bigint as sprint_result_id,
        "raceId"::bigint as race_id,
        "driverId"::bigint as driver_id,
        "constructorId"::bigint as constructor_id,
        nullif(number, '')::int as driver_number,
        "grid"::smallint as grid_position,
        nullif(position, '')::smallint as finish_position,
        "positionText" as position_text,
        "positionOrder"::smallint as position_order,
        points::numeric(5,2) as points,
        laps::smallint as laps_completed,
        time as sprint_time,
        "milliseconds"::bigint as sprint_milliseconds,
        nullif("fastestLap", '')::smallint as fastest_lap_number,
        "fastestLapTime" as fastest_lap_time,
        "statusId"::bigint as status_id,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned