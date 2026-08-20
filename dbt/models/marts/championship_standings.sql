{{ config(
    materialized='table',
    unique_key='driver_race_key'
) }}

with race_results as (
    select
        driver_id,
        race_id,
        constructor_id,
        season,
        round,
        finish_position,
        points,
        is_win,
        is_podium,
        source
    from {{ ref('race_results_detail') }}
),
driver_info as (
    select
        driver_id,
        forename || ' ' || surname as driver_name
    from {{ ref('dim_drivers') }}
),
constructor_info as (
    select
        constructor_id,
        name as constructor_name
    from {{ ref('dim_constructors') }}
),
points_base as (
    select
        rr.driver_id,
        rr.race_id,
        rr.season,
        rr.round,
        rr.points,
        rr.is_win,
        rr.is_podium,
        di.driver_name,
        ci.constructor_name as team,
        rr.source
    from race_results rr
    join driver_info di on rr.driver_id = di.driver_id
    join constructor_info ci on rr.constructor_id = ci.constructor_id
),
points_cumulative as (
    select
        pb.driver_id,
        pb.race_id,
        pb.season,
        pb.round,
        pb.driver_name,
        pb.team,
        sum(pb.points) over (partition by pb.driver_id, pb.season order by pb.round rows unbounded preceding) as cumulative_points,
        sum(case when pb.is_win then 1 else 0 end) over (partition by pb.driver_id, pb.season order by pb.round rows unbounded preceding) as wins_so_far,
        sum(case when pb.is_podium then 1 else 0 end) over (partition by pb.driver_id, pb.season order by pb.round rows unbounded preceding) as podiums_so_far,
        pb.source
    from points_base pb
),
ranked as (
    select
        pc.*,
        row_number() over (partition by pc.season, pc.round order by pc.cumulative_points desc, pc.wins_so_far desc, pc.podiums_so_far desc) as championship_position,
        first_value(pc.cumulative_points) over (partition by pc.season, pc.round order by pc.cumulative_points desc, pc.wins_so_far desc, pc.podiums_so_far desc) as leader_points
    from points_cumulative pc
)
select
    pc.driver_id || '_' || pc.race_id as driver_race_key,
    pc.driver_id,
    pc.race_id,
    pc.season,
    pc.round,
    pc.driver_name,
    pc.team,
    pc.cumulative_points,
    pc.championship_position,
    (pc.leader_points - pc.cumulative_points) as points_behind_leader,
    pc.wins_so_far,
    pc.podiums_so_far,
    pc.source
from ranked pc