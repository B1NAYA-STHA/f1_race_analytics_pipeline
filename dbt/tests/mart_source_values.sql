-- Source lineage is part of the warehouse contract.
select source
from {{ ref('race_results_detail') }}
where source not in ('historical', 'api')
   or source is null