-- The central mart must not contain orphaned dimension keys.
select rrd.race_driver_key
from {{ ref('race_results_detail') }} rrd
left join {{ ref('dim_drivers') }} drivers on rrd.driver_id = drivers.driver_id
left join {{ ref('dim_constructors') }} constructors on rrd.constructor_id = constructors.constructor_id
left join {{ ref('dim_circuits') }} circuits on rrd.circuit_id = circuits.circuit_id
left join {{ ref('dim_races') }} races on rrd.race_id = races.race_id
where drivers.driver_id is null
   or constructors.constructor_id is null
   or circuits.circuit_id is null
   or races.race_id is null