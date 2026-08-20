{{ config(
    materialized='table',
    unique_key='constructor_id'
) }}

with career as (
    select
        dc.constructor_id,
        dc.name as constructor_name,
        dc.nationality,
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
        count(distinct rrd.driver_id) as drivers_raced_for,
        string_agg(distinct dd.forename || ' ' || dd.surname, ', ' order by dd.forename || ' ' || dd.surname) as drivers,
        max(dc.source) as source
    from {{ ref('race_results_detail') }} rrd
    join {{ ref('dim_constructors') }} dc on rrd.constructor_id = dc.constructor_id
    join {{ ref('dim_drivers') }} dd on rrd.driver_id = dd.driver_id
    group by dc.constructor_id, dc.name, dc.nationality
),
championships as (
    select
        constructor_id,
        count(distinct season) as championships_won
    from (
        select
            constructor_id,
            season,
            row_number() over (partition by season order by points desc, wins desc, podiums desc) as pos
        from {{ ref('constructor_season_summary') }}
    ) t
    where pos = 1
    group by constructor_id
)
select
    c.constructor_id,
    c.constructor_name,
    c.nationality,
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
    c.drivers_raced_for,
    c.drivers,
    coalesce(ch.championships_won, 0) as championships_won,
    c.source
from career c
left join championships ch on c.constructor_id = ch.constructor_id