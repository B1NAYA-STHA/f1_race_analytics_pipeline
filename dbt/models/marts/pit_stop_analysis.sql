{{ config(
    materialized='table',
    unique_key='pit_analysis_key'
) }}

with pit_data as (
    select
        fp.race_id,
        fp.driver_id,
        fp.stop_number,
        fp.lap_number,
        fp.stop_time,
        fp.stop_duration,
        fp.stop_milliseconds as stop_ms,
        fp.source,
        rd.year as season,
        rd.round,
        rd.name as race_name,
        rd.race_date,
        cc.name as circuit_name,
        cc.country as circuit_country,
        dd.forename || ' ' || dd.surname as driver_name,
        dd.code as driver_code,
        fr.constructor_id,
        dc.name as constructor_name,
        dc.nationality as constructor_nationality,
        fr.grid_position,
        fr.finish_position,
        fr.status_id
    from {{ ref('fact_pit_stops') }} fp
    join {{ ref('dim_races') }} rd on fp.race_id = rd.race_id
    join {{ ref('dim_drivers') }} dd on fp.driver_id = dd.driver_id
    join {{ ref('fact_results') }} fr on fp.race_id = fr.race_id and fp.driver_id = fr.driver_id
    join {{ ref('dim_constructors') }} dc on fr.constructor_id = dc.constructor_id
    join {{ ref('dim_circuits') }} cc on rd.circuit_id = cc.circuit_id
),
pit_with_stats as (
    select
        *,
        avg(stop_ms) over (partition by race_id, stop_number) as avg_stop_ms_by_stop,
        min(stop_ms) over (partition by race_id, stop_number) as best_stop_ms_by_stop,
        max(stop_ms) over (partition by race_id, stop_number) as worst_stop_ms_by_stop,
        sum(stop_ms) over (partition by race_id, driver_id) as total_pit_ms,
        count(*) over (partition by race_id, driver_id) as total_stops,
        row_number() over (partition by race_id, driver_id order by stop_number) as stop_seq,
        lag(stop_ms) over (partition by race_id, driver_id order by stop_number) as prev_stop_ms
    from pit_data
),
final as (
    select
        {{ dbt_utils.generate_surrogate_key(['race_id', 'driver_id', 'stop_number']) }} as pit_analysis_key,
        race_id,
        driver_id,
        stop_number,
        lap_number,
        stop_time,
        stop_duration,
        stop_ms,
        stop_ms - avg_stop_ms_by_stop as delta_to_avg_stop_ms,
        case when stop_ms = best_stop_ms_by_stop then true else false end as is_fastest_stop_in_race,
        case when stop_ms = worst_stop_ms_by_stop then true else false end as is_slowest_stop_in_race,
        total_pit_ms,
        total_stops,
        stop_seq,
        stop_ms - coalesce(prev_stop_ms, 0) as stop_delta_from_prev,
        case when prev_stop_ms is not null and stop_ms - prev_stop_ms > 3000 then true else false end as is_slow_stop,
        season,
        round,
        race_name,
        race_date,
        circuit_name,
        circuit_country,
        driver_name,
        driver_code,
        constructor_name,
        constructor_nationality,
        grid_position,
        finish_position,
        source
    from pit_with_stats
)
select * from final