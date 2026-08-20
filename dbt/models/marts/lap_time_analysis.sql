{{ config(
    materialized='table',
    unique_key='lap_analysis_key'
) }}

with lap_data as (
    select
        fl.race_id,
        fl.driver_id,
        fl.lap_number,
        fl.lap_position,
        fl.lap_time,
        fl.lap_milliseconds as lap_ms,
        fl.source as source,
        rd.year as season,
        rd.round,
        rd.name as race_name,
        rd.race_date,
        cc.circuit_id,
        cc.name as circuit_name,
        cc.country as circuit_country,
        cc.location as circuit_location,
        dd.forename || ' ' || dd.surname as driver_name,
        dd.code as driver_code,
        fr.constructor_id
    from {{ ref('fact_lap_times') }} fl
    join {{ ref('dim_races') }} rd on fl.race_id = rd.race_id
    join {{ ref('dim_drivers') }} dd on fl.driver_id = dd.driver_id
    join {{ ref('fact_results') }} fr on fl.race_id = fr.race_id and fl.driver_id = fr.driver_id
    join {{ ref('dim_circuits') }} cc on rd.circuit_id = cc.circuit_id
),
laps_with_leader as (
    select
        *,
        min(lap_ms) over (partition by race_id, lap_number) as leader_lap_ms,
        min(lap_ms) over (partition by race_id) as race_best_lap_ms,
        avg(lap_ms) over (partition by race_id, lap_number) as lap_avg_ms,
        max(lap_ms) over (partition by race_id, lap_number) as lap_max_ms,
        count(*) over (partition by race_id, lap_number) as drivers_on_lap,
        row_number() over (partition by race_id, driver_id order by lap_number) as lap_seq,
        row_number() over (partition by race_id, driver_id order by lap_ms) as driver_lap_rank
    from lap_data
),
stint_analysis as (
    select
        race_id,
        driver_id,
        lap_number,
        lap_position,
        lap_time,
        lap_ms,
        source,
        season,
        round,
        race_name,
        race_date,
        circuit_id,
        circuit_name,
        circuit_country,
        circuit_location,
        driver_name,
        driver_code,
        constructor_id,
        leader_lap_ms,
        race_best_lap_ms,
        lap_avg_ms,
        lap_max_ms,
        drivers_on_lap,
        lap_seq,
        driver_lap_rank,
        case
            when lag(lap_ms) over (partition by race_id, driver_id order by lap_number) is not null
                 and lap_ms - lag(lap_ms) over (partition by race_id, driver_id order by lap_number) > 5000
            then 1 else 0
        end as potential_pit_lap
    from laps_with_leader
),
final as (
    select
        {{ dbt_utils.generate_surrogate_key(['race_id', 'driver_id', 'lap_number']) }} as lap_analysis_key,
        race_id,
        driver_id,
        lap_number,
        lap_position,
        lap_time,
        lap_ms,
        lap_ms - leader_lap_ms as delta_to_leader_ms,
        lap_ms - race_best_lap_ms as delta_to_race_best_ms,
        case when lap_ms = race_best_lap_ms then true else false end as is_race_fastest_lap,
        case when lap_ms = leader_lap_ms then true else false end as is_lap_fastest,
        lap_ms - lap_avg_ms as delta_to_lap_avg_ms,
        drivers_on_lap,
        lap_seq,
        driver_lap_rank,
        potential_pit_lap,
        season,
        round,
        race_name,
        race_date,
        circuit_id,
        circuit_name,
        circuit_country,
        driver_name,
        driver_code,
        dc.name as constructor_name,
        dc.nationality as constructor_nationality,
        stint_analysis.source
    from stint_analysis
    left join {{ ref('dim_constructors') }} dc on stint_analysis.constructor_id = dc.constructor_id
)
select * from final