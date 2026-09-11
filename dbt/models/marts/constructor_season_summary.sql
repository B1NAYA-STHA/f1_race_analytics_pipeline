{{ config(
    materialized='table',
    unique_key='constructor_id_season'
) }}

with race_results as (
    select
        constructor_id,
        race_id,
        driver_id,
        season,
        finish_position,
        points,
        sprint_points,
        is_podium,
        is_win,
        is_dnf,
        qualifying_position,
        fastest_lap_rank,
        source
    from {{ ref('race_results_detail') }}
),
constructor_info as (
    select
        constructor_id,
        name as constructor_name,
        nationality
    from {{ ref('dim_constructors') }}
),
one_two_finishes as (
    select
        constructor_id,
        season,
        count(distinct race_id) as one_two_count
    from (
        select
            constructor_id,
            season,
            race_id,
            min(finish_position) as min_pos,
            max(finish_position) as max_pos,
            count(*) as driver_count
        from race_results
        where finish_position <= 2
        group by constructor_id, season, race_id
        having count(*) = 2 and min(finish_position) = 1 and max(finish_position) = 2
    ) t
    group by constructor_id, season
),
agg as (
    select
        rr.constructor_id,
        rr.season,
        max(ci.constructor_name) as constructor_name,
        count(distinct rr.race_id) as races_entered,
        sum(case when rr.is_win then 1 else 0 end) as wins,
        sum(case when rr.is_podium then 1 else 0 end) as podiums,
        sum(rr.points + coalesce(rr.sprint_points, 0)) as points,
        coalesce(max(otf.one_two_count), 0) as one_two_finishes,
        sum(case when rr.qualifying_position = 1 then 1 else 0 end) as poles,
        sum(case when rr.fastest_lap_rank = 1 then 1 else 0 end) as fastest_laps,
        sum(case when rr.is_dnf then 1 else 0 end) as dnfs,
        max(rr.source) as source
    from race_results rr
    join constructor_info ci on rr.constructor_id = ci.constructor_id
    left join one_two_finishes otf on rr.constructor_id = otf.constructor_id and rr.season = otf.season
    group by rr.constructor_id, rr.season
),
championship as (
    select
        constructor_id,
        season,
        row_number() over (partition by season order by points desc, wins desc, podiums desc) as championship_position
    from agg
)
select
    a.constructor_id || '_' || a.season as constructor_id_season,
    a.constructor_id,
    a.season,
    a.constructor_name,
    a.races_entered,
    a.wins,
    a.podiums,
    a.points,
    a.one_two_finishes,
    a.poles,
    a.fastest_laps,
    a.dnfs,
    c.championship_position,
    a.source
from agg a
left join championship c on a.constructor_id = c.constructor_id and a.season = c.season