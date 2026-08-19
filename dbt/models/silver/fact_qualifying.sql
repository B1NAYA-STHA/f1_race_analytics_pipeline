{{ config(
    materialized='table',
    schema='silver',
    unique_key='qualify_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'qualifying') }}
),
cleaned as (
    select
        "qualifyId"::bigint as qualify_id,
        "raceId"::bigint as race_id,
        "driverId"::bigint as driver_id,
        "constructorId"::bigint as constructor_id,
        nullif(number, '')::int as driver_number,
        position::smallint as qualifying_position,
        q1 as q1_time,
        q2 as q2_time,
        q3 as q3_time,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned