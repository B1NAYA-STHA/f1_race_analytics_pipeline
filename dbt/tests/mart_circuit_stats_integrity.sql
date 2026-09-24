-- Circuit aggregates must remain physically and temporally consistent.
select *
from {{ ref('circuit_stats') }}
where total_wins < 0
   or total_podiums < total_wins
   or total_podiums < 0
   or races_hosted < seasons_hosted
   or first_season > last_season
   or latest_season < last_season