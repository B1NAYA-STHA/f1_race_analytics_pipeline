{{ config(
    materialized='table',
    unique_key='driver_id'
) }}

with career as (
    select
        dd.driver_id,
        dd.forename || ' ' || dd.surname as driver_name,
        dd.code as driver_code,
        dd.nationality,
        dd.date_of_birth,
        min(rrd.season) as first_season,
        max(rrd.season) as last_season,
        count(distinct rrd.season) as seasons,
        count(distinct rrd.race_id) as races_entered,
        sum(case when rrd.is_win then 1 else 0 end) as wins,
        sum(case when rrd.is_podium then 1 else 0 end) as podiums,
        sum(case when rrd.qualifying_position = 1 then 1 else 0 end) as poles,
        sum(case when rrd.fastest_lap_rank = 1 then 1 else 0 end) as fastest_laps,
        sum(rrd.points) as total_points,
        sum(case when rrd.is_dnf then 1 else 0 end) as dnfs,
        count(distinct rrd.constructor_id) as teams_raced_for,
        string_agg(distinct dc.name, ', ' order by dc.name) as teams,
        max(dd.source) as source
    from {{ ref('race_results_detail') }} rrd
    join {{ ref('dim_drivers') }} dd on rrd.driver_id = dd.driver_id
    join {{ ref('dim_constructors') }} dc on rrd.constructor_id = dc.constructor_id
    group by dd.driver_id, dd.forename, dd.surname, dd.code, dd.nationality, dd.date_of_birth
),
championships as (
    select
        driver_id,
        count(distinct season) as championships_won
    from (
        select
            driver_id,
            season,
            row_number() over (partition by season order by points desc, wins desc, podiums desc) as pos
        from {{ ref('driver_season_summary') }}
    ) t
    where pos = 1
    group by driver_id
)
select
    c.driver_id,
    c.driver_name,
    c.driver_code,
    c.nationality,
    c.date_of_birth,
    c.first_season,
    c.last_season,
    c.seasons,
    c.races_entered,
    c.wins,
    c.podiums,
    c.poles,
    c.fastest_laps,
    c.total_points,
    c.dnfs,
    c.teams_raced_for,
    c.teams,
    coalesce(ch.championships_won, 0) as championships_won,
    c.source
from career c
left join championships ch on c.driver_id = ch.driver_id