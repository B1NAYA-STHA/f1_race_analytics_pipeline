{{ config(
    materialized='table',
    schema='silver',
    unique_key='driver_standings_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'driver_standings') }}
),
cleaned as (
    select
        "driverStandingsId"::bigint as driver_standings_id,
        "raceId"::bigint as race_id,
        "driverId"::bigint as driver_id,
        points::numeric(5,2) as points,
        position::smallint as championship_position,
        "positionText" as position_text,
        wins::smallint as wins,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned