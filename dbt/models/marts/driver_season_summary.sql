{{ config(
    materialized='table',
    unique_key='driver_id_season'
) }}

with race_results as (
    select
        driver_id,
        race_id,
        constructor_id,
        season,
        grid_position,
        finish_position,
        points,
        laps_completed,
        status_category,
        is_podium,
        is_win,
        is_dnf,
        qualifying_position,
        fastest_lap_rank,
        source
    from {{ ref('race_results_detail') }}
),
driver_info as (
    select
        driver_id,
        forename || ' ' || surname as driver_name,
        nationality
    from {{ ref('dim_drivers') }}
),
constructor_info as (
    select
        constructor_id,
        name as constructor_name
    from {{ ref('dim_constructors') }}
),
agg as (
    select
        rr.driver_id,
        rr.season,
        max(di.driver_name) as driver_name,
        max(ci.constructor_name) as team,
        count(distinct rr.race_id) as races_entered,
        sum(case when rr.is_win then 1 else 0 end) as wins,
        sum(case when rr.is_podium then 1 else 0 end) as podiums,
        sum(rr.points) as points,
        sum(case when rr.qualifying_position = 1 then 1 else 0 end) as poles,
        sum(case when rr.fastest_lap_rank = 1 then 1 else 0 end) as fastest_laps,
        sum(case when rr.is_dnf then 1 else 0 end) as dnfs,
        avg(rr.finish_position)::numeric(4,2) as avg_finish_position,
        max(case when rr.finish_position = 1 then rr.season else null end) as championship_win_season,
        max(rr.source) as source
    from race_results rr
    join driver_info di on rr.driver_id = di.driver_id
    join constructor_info ci on rr.constructor_id = ci.constructor_id
    group by rr.driver_id, rr.season
),
championship as (
    select
        driver_id,
        season,
        row_number() over (partition by season order by points desc, wins desc, podiums desc) as championship_position
    from agg
)
select
    a.driver_id || '_' || a.season as driver_id_season,
    a.driver_id,
    a.season,
    a.driver_name,
    a.team,
    a.races_entered,
    a.wins,
    a.podiums,
    a.points,
    a.poles,
    a.fastest_laps,
    a.dnfs,
    a.avg_finish_position,
    c.championship_position,
    a.source
from agg a
left join championship c on a.driver_id = c.driver_id and a.season = c.season