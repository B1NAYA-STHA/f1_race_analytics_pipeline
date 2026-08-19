{{ config(
    materialized='table',
    schema='silver',
    unique_key='race_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'races') }}
),
cleaned as (
    select
        "raceId"::bigint as race_id,
        year::int as year,
        round::int as round,
        "circuitId"::bigint as circuit_id,
        name,
        date::date as race_date,
        time::time as race_time,
        url,
        "fp1_date"::date as fp1_date,
        "fp1_time"::time as fp1_time,
        "fp2_date"::date as fp2_date,
        "fp2_time"::time as fp2_time,
        "fp3_date"::date as fp3_date,
        "fp3_time"::time as fp3_time,
        "quali_date"::date as quali_date,
        "quali_time"::time as quali_time,
        "sprint_date"::date as sprint_date,
        "sprint_time"::time as sprint_time,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned