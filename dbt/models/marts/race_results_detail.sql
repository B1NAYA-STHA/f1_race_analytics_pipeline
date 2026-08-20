{{ config(
    materialized='table',
    unique_key='race_driver_key'
) }}

with race_facts_raw as (
    select * from {{ ref('fact_results') }}
),
race_facts as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by race_id, driver_id
                order by points desc,
                    case when finish_position is null then 999 else finish_position end asc,
                    laps_completed desc
            ) as rn
        from race_facts_raw
    ) t
    where rn = 1
),
qualifying_facts as (
    select
        qualify_id,
        race_id,
        driver_id,
        qualifying_position,
        q1_time,
        q2_time,
        q3_time
    from {{ ref('fact_qualifying') }}
),
sprint_facts as (
    select
        sprint_result_id,
        race_id,
        driver_id,
        grid_position as sprint_grid,
        finish_position as sprint_finish,
        points as sprint_points
    from {{ ref('fact_sprint_results') }}
),
pit_facts as (
    select
        race_id,
        driver_id,
        count(*) as pit_stop_count,
        sum(stop_milliseconds)::bigint as total_pit_ms,
        min(stop_milliseconds)::bigint as best_pit_ms,
        max(stop_milliseconds)::bigint as worst_pit_ms
    from {{ ref('fact_pit_stops') }}
    group by 1, 2
),
lap_facts as (
    select
        race_id,
        driver_id,
        min(lap_milliseconds)::bigint as best_lap_ms,
        avg(lap_milliseconds)::numeric as avg_lap_ms,
        count(*)::int as total_laps
    from {{ ref('fact_lap_times') }}
    group by 1, 2
),
driver_dim as (
    select * from {{ ref('dim_drivers') }}
),
constructor_dim as (
    select * from {{ ref('dim_constructors') }}
),
circuit_dim as (
    select * from {{ ref('dim_circuits') }}
),
race_dim as (
    select * from {{ ref('dim_races') }}
),
status_dim as (
    select * from {{ ref('dim_status') }}
),
season_dim as (
    select * from {{ ref('dim_seasons') }}
),
base as (
    select
        -- Original IDs (for joining in downstream marts)
        rf.race_id,
        rf.driver_id,
        rf.constructor_id,
        rf.status_id,
        rd.circuit_id,

        -- Surrogate keys using dbt_utils
        {{ dbt_utils.generate_surrogate_key(['rf.race_id', 'rf.driver_id']) }} as race_driver_key,
        {{ dbt_utils.generate_surrogate_key(['rf.driver_id']) }} as driver_key,
        {{ dbt_utils.generate_surrogate_key(['rf.constructor_id']) }} as constructor_key,
        {{ dbt_utils.generate_surrogate_key(['rd.circuit_id']) }} as circuit_key,
        {{ dbt_utils.generate_surrogate_key(['rf.status_id']) }} as status_key,

        -- Race identifiers
        rd.year as season,
        rd.round,
        rd.name as race_name,
        rd.race_date,

        -- Driver attributes
        dd.forename || ' ' || dd.surname as driver_name,
        dd.nationality as driver_nationality,
        dd.code as driver_code,
        dd.driver_number,

        -- Constructor attributes
        dc.name as constructor_name,
        dc.nationality as constructor_nationality,

        -- Circuit attributes
        cc.name as circuit_name,
        cc.country as circuit_country,
        cc.location as circuit_location,

        -- Result facts
        rf.grid_position,
        rf.finish_position,
        (rf.grid_position - rf.finish_position) as position_change,
        rf.points,
        rf.laps_completed,

        -- Qualifying
        qf.qualifying_position,

        -- Sprint
        sf.sprint_grid,
        sf.sprint_finish,
        sf.sprint_points,

        -- Pit stops
        pf.pit_stop_count,
        pf.total_pit_ms,
        pf.best_pit_ms,
        pf.worst_pit_ms,

        -- Lap times
        lf.best_lap_ms,
        lf.avg_lap_ms,
        lf.total_laps,

        -- Status
        sd.status_category,
        case when sd.status_category != 'Finished' then true else false end as is_dnf,
        case when rf.points > 0 then true else false end as is_points_finish,
        case when rf.finish_position <= 3 then true else false end as is_podium,
        case when rf.finish_position = 1 then true else false end as is_win,

        -- Fastest lap
        rf.fastest_lap_number,
        rf.fastest_lap_rank,
        rf.fastest_lap_time,

        -- Source lineage
        rf.source

    from race_facts rf
    join race_dim rd on rf.race_id = rd.race_id
    join driver_dim dd on rf.driver_id = dd.driver_id
    join constructor_dim dc on rf.constructor_id = dc.constructor_id
    join circuit_dim cc on rd.circuit_id = cc.circuit_id
    join status_dim sd on rf.status_id = sd.status_id
    left join qualifying_facts qf on rf.race_id = qf.race_id and rf.driver_id = qf.driver_id
    left join sprint_facts sf on rf.race_id = sf.race_id and rf.driver_id = sf.driver_id
    left join pit_facts pf on rf.race_id = pf.race_id and rf.driver_id = pf.driver_id
    left join lap_facts lf on rf.race_id = lf.race_id and rf.driver_id = lf.driver_id
)
select * from base