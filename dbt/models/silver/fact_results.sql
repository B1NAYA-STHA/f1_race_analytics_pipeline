{{ config(
    materialized='table',
    schema='silver',
    unique_key='result_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'results') }}
),
cleaned as (
    select
        "resultId"::bigint as result_id,
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
        time as race_time,
        "milliseconds"::bigint as race_milliseconds,
        nullif("fastestLap", '')::smallint as fastest_lap_number,
        nullif(rank, '')::smallint as fastest_lap_rank,
        "fastestLapTime" as fastest_lap_time,
        "fastestLapSpeed" as fastest_lap_speed,
        "statusId"::bigint as status_id,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned