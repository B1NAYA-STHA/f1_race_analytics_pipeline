{{ config(
    materialized='table',
    schema='silver',
    unique_key='constructor_standings_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'constructor_standings') }}
),
cleaned as (
    select
        "constructorStandingsId"::bigint as constructor_standings_id,
        "raceId"::bigint as race_id,
        "constructorId"::bigint as constructor_id,
        points::numeric(5,2) as points,
        position::smallint as championship_position,
        "positionText" as position_text,
        wins::smallint as wins,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned