from unittest.mock import patch

import numpy as np

import db


def test_query_converts_numpy_scalar_parameters_before_execution():
    fake_connection = object()
    with (
        patch.object(db, "get_engine") as get_engine,
        patch.object(db.pd, "read_sql") as read_sql,
    ):
        get_engine.return_value.connect.return_value.__enter__.return_value = fake_connection

        db.query("SELECT 1 WHERE id = :id", {"id": np.int64(1169)})

    read_sql.assert_called_once()
    assert read_sql.call_args.kwargs["params"] == {"id": 1169}