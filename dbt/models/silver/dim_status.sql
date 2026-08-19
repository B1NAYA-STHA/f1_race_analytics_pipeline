{{ config(
    materialized='table',
    schema='silver',
    unique_key='status_id'
) }}

with bronze as (
    select * from {{ source('bronze', 'status') }}
),
cleaned as (
    select
        "statusId"::bigint as status_id,
        status,
        case
            when status ILIKE '%finished%' then 'Finished'
            when status ILIKE '%disqualified%' then 'Disqualified'
            when status ILIKE '%excluded%' then 'Excluded'
            when status ILIKE '%withdrawn%' then 'Withdrawn'
            when status ILIKE '%accident%' then 'Accident'
            when status ILIKE '%collision%' then 'Collision'
            when status ILIKE '%mechanical%' then 'Mechanical'
            when status ILIKE '%engine%' then 'Engine'
            when status ILIKE '%gearbox%' then 'Gearbox'
            when status ILIKE '%transmission%' then 'Transmission'
            when status ILIKE '%hydraulics%' then 'Hydraulics'
            when status ILIKE '%electrical%' then 'Electrical'
            when status ILIKE '%brakes%' then 'Brakes'
            when status ILIKE '%suspension%' then 'Suspension'
            when status ILIKE '%tyre%' or status ILIKE '%tire%' then 'Tyre'
            when status ILIKE '%wheel%' then 'Wheel'
            when status ILIKE '%fuel%' then 'Fuel'
            when status ILIKE '%oil%' then 'Oil'
            when status ILIKE '%overheating%' then 'Overheating'
            when status ILIKE '%fire%' then 'Fire'
            when status ILIKE '%not classified%' then 'Not Classified'
            when status ILIKE '%did not start%' or status ILIKE '%dns%' then 'Did Not Start'
            when status ILIKE '%did not qualify%' or status ILIKE '%dnq%' then 'Did Not Qualify'
            when status ILIKE '%did not pre-qualify%' or status ILIKE '%dnpq%' then 'Did Not Pre-Qualify'
            when status ILIKE '%107%' then '107% Rule'
            when status ILIKE '%suspended%' then 'Suspended'
            when status ILIKE '%red flag%' then 'Red Flag'
            else 'Other'
        end as status_category,
        source,
        current_timestamp as dbt_loaded_at
    from bronze
)
select * from cleaned