{{ config(
    materialized='table',
    unique_key='quali_race_key'
) }}

with quali_data as (
    select
        fq.qualify_id,
        fq.race_id,
        fq.driver_id,
        fq.constructor_id,
        fq.qualifying_position,
        fq.q1_time,
        fq.q2_time,
        fq.q3_time,
        fq.source
    from {{ ref('fact_qualifying') }} fq
),
race_data as (
    select
        fr.race_id,
        fr.driver_id,
        fr.constructor_id,
        fr.grid_position,
        fr.finish_position,
        fr.points,
        fr.laps_completed,
        fr.status_id,
        fr.fastest_lap_rank,
        fr.source
    from {{ ref('fact_results') }} fr
),
driver_dim as (
    select * from {{ ref('dim_drivers') }}
),
constructor_dim as (
    select * from {{ ref('dim_constructors') }}
),
race_dim as (
    select * from {{ ref('dim_races') }}
),
status_dim as (
    select * from {{ ref('dim_status') }}
),
base as (
    select
        qd.race_id,
        qd.driver_id,
        qd.constructor_id,
        qd.qualifying_position,
        qd.q1_time,
        qd.q2_time,
        qd.q3_time,
        rd.grid_position,
        rd.finish_position,
        rd.points,
        rd.laps_completed,
        rd.status_id,
        rd.fastest_lap_rank,
        qd.source,
        dd.forename || ' ' || dd.surname as driver_name,
        dd.nationality as driver_nationality,
        dd.code as driver_code,
        dc.name as constructor_name,
        dc.nationality as constructor_nationality,
        rr.year as season,
        rr.round,
        rr.name as race_name,
        rr.race_date,
        sd.status_category
    from quali_data qd
    join race_data rd on qd.race_id = rd.race_id and qd.driver_id = rd.driver_id
    join driver_dim dd on qd.driver_id = dd.driver_id
    join constructor_dim dc on qd.constructor_id = dc.constructor_id
    join race_dim rr on qd.race_id = rr.race_id
    join status_dim sd on rd.status_id = sd.status_id
)
select
    {{ dbt_utils.generate_surrogate_key(['race_id', 'driver_id']) }} as quali_race_key,
    race_id,
    driver_id,
    constructor_id,
    qualifying_position,
    grid_position,
    finish_position,
    (grid_position - finish_position) as positions_gained_lost,
    points,
    laps_completed,
    status_category,
    case when status_category != 'Finished' then true else false end as is_dnf,
    q1_time,
    q2_time,
    q3_time,
    fastest_lap_rank,
    case when qualifying_position = 1 then true else false end as is_pole,
    case when finish_position = 1 then true else false end as is_win,
    case when finish_position <= 3 then true else false end as is_podium,
    driver_name,
    driver_nationality,
    driver_code,
    constructor_name,
    constructor_nationality,
    season,
    round,
    race_name,
    race_date,
    source
from base