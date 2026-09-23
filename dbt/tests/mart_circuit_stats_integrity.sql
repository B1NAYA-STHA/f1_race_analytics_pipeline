-- Circuit aggregates must remain physically and temporally consistent.
select *
from {{ ref('circuit_stats') }}
where total_wins > races_hosted
   or total_podiums > races_hosted * 3
   or first_season > last_season
   or latest_season < last_season