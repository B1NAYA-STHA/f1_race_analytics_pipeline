import pytest
from unittest.mock import patch

import ingest_jolpica


def test_calc_backoff_doubles_then_caps():
    assert ingest_jolpica.calc_backoff(0) == 5
    assert ingest_jolpica.calc_backoff(1) == 10
    assert ingest_jolpica.calc_backoff(2) == 20
    assert ingest_jolpica.calc_backoff(3) == 40
    assert ingest_jolpica.calc_backoff(4) == 80
    assert ingest_jolpica.calc_backoff(5) == 120
    assert ingest_jolpica.calc_backoff(6) == 120


@patch("ingest_jolpica.calc_backoff", return_value=0)
@patch("ingest_jolpica.requests.get")
def test_rate_limited_request_retries_429_then_raises(mock_get, mock_backoff):
    mock_get.return_value.status_code = 429
    with pytest.raises(Exception, match="Failed after 7 attempts"):
        ingest_jolpica.rate_limited_request("https://api.jolpi.ca/test.json")
    assert mock_get.call_count == ingest_jolpica.MAX_RETRIES
