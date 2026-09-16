{{ config(
    materialized='table',
    unique_key='circuit_id'
) }}

with circuit_races as (
    select
        rrd.circuit_id,
        rrd.race_id,
        rrd.season,
        rrd.round,
        rrd.race_name,
        rrd.race_date,
        rrd.driver_id,
        rrd.constructor_id,
        rrd.grid_position,
        rrd.finish_position,
        rrd.points,
        rrd.is_win,
        rrd.is_podium,
        rrd.is_dnf,
        rrd.laps_completed,
        rrd.status_category,
        rrd.pit_stop_count,
        rrd.total_pit_ms,
        rrd.source
    from {{ ref('race_results_detail') }} rrd
),
circuit_agg as (
    select
        cr.circuit_id,
        max(cc.name) as circuit_name,
        max(cc.country) as circuit_country,
        max(cc.location) as circuit_location,
        max(cc.latitude) as latitude,
        max(cc.longitude) as longitude,
        max(cc.altitude) as altitude,
        count(distinct cr.season) as seasons_hosted,
        count(distinct cr.race_id) as races_hosted,
        min(cr.season) as first_season,
        max(cr.season) as last_season,
        count(distinct cr.driver_id) as unique_drivers,
        count(distinct cr.constructor_id) as unique_constructors,
        sum(case when cr.is_win then 1 else 0 end) as total_wins,
        sum(case when cr.is_podium then 1 else 0 end) as total_podiums,
        sum(case when cr.is_dnf then 1 else 0 end) as total_dnfs,
        avg(cr.laps_completed)::numeric(6,2) as avg_laps_completed,
        avg(cr.pit_stop_count)::numeric(6,2) as avg_pit_stops_per_driver,
        avg(cr.total_pit_ms)::numeric(10,2) as avg_total_pit_ms,
        max(cr.source) as source
    from circuit_races cr
    join {{ ref('dim_circuits') }} cc on cr.circuit_id = cc.circuit_id
    group by cr.circuit_id
),
most_wins as (
    select
        circuit_id,
        max(driver_name) as most_wins_driver
    from (
        select
            cr.circuit_id,
            cr.driver_id,
            dd.forename || ' ' || dd.surname as driver_name,
            count(*) as win_count,
            row_number() over (
                partition by cr.circuit_id
                order by count(*) desc, cr.driver_id
            ) as record_rank
        from circuit_races cr
        join {{ ref('dim_drivers') }} dd on cr.driver_id = dd.driver_id
        where cr.is_win
        group by cr.circuit_id, cr.driver_id, dd.forename, dd.surname
    ) ranked
    where record_rank = 1
    group by circuit_id
),
most_podiums as (
    select
        circuit_id,
        max(driver_name) as most_podiums_driver
    from (
        select
            cr.circuit_id,
            cr.driver_id,
            dd.forename || ' ' || dd.surname as driver_name,
            count(*) as podium_count,
            row_number() over (
                partition by cr.circuit_id
                order by count(*) desc, cr.driver_id
            ) as record_rank
        from circuit_races cr
        join {{ ref('dim_drivers') }} dd on cr.driver_id = dd.driver_id
        where cr.is_podium
        group by cr.circuit_id, cr.driver_id, dd.forename, dd.surname
    ) ranked
    where record_rank = 1
    group by circuit_id
),
best_qualifying as (
    select
        circuit_id,
        max(driver_name) as most_poles_driver
    from (
        select
            cr.circuit_id,
            cr.driver_id,
            dd.forename || ' ' || dd.surname as driver_name,
            count(*) as pole_count,
            row_number() over (
                partition by cr.circuit_id
                order by count(*) desc, cr.driver_id
            ) as record_rank
        from circuit_races cr
        join {{ ref('fact_qualifying') }} fq on cr.race_id = fq.race_id and cr.driver_id = fq.driver_id
        join {{ ref('dim_drivers') }} dd on cr.driver_id = dd.driver_id
        where fq.qualifying_position = 1
        group by cr.circuit_id, cr.driver_id, dd.forename, dd.surname
    ) ranked
    where record_rank = 1
    group by circuit_id
),
latest_race as (
    select distinct on (circuit_id)
        circuit_id,
        season as latest_season,
        race_name as latest_race_name,
        race_date as latest_race_date
    from circuit_races
    order by circuit_id, season desc, round desc, race_date desc
),
latest_winner as (
    select distinct on (cr.circuit_id)
        cr.circuit_id,
        dd.forename || ' ' || dd.surname as latest_winner
    from circuit_races cr
    join {{ ref('dim_drivers') }} dd on cr.driver_id = dd.driver_id
    where cr.is_win
    order by cr.circuit_id, cr.season desc, cr.round desc, cr.race_date desc
)
select
    ca.circuit_id,
    ca.circuit_name,
    ca.circuit_country,
    ca.circuit_location,
    ca.latitude,
    ca.longitude,
    ca.altitude,
    ca.seasons_hosted,
    ca.races_hosted,
    ca.first_season,
    ca.last_season,
    ca.unique_drivers,
    ca.unique_constructors,
    ca.total_wins,
    ca.total_podiums,
    ca.total_dnfs,
    ca.avg_laps_completed,
    ca.avg_pit_stops_per_driver,
    ca.avg_total_pit_ms,
    mw.most_wins_driver,
    mp.most_podiums_driver,
    bp.most_poles_driver,
    lr.latest_season,
    lr.latest_race_name,
    lr.latest_race_date,
    lw.latest_winner,
    ca.source
from circuit_agg ca
left join most_wins mw on ca.circuit_id = mw.circuit_id
left join most_podiums mp on ca.circuit_id = mp.circuit_id
left join best_qualifying bp on ca.circuit_id = bp.circuit_id
left join latest_race lr on ca.circuit_id = lr.circuit_id
left join latest_winner lw on ca.circuit_id = lw.circuit_id