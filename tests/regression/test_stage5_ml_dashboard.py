"""Regression tests for Stage 5 — expected ML KPI numbers from fixtures."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.dashboard.ml_metrics import (
    late_flag_rate_over_time,
    sample_volume,
    score_summary,
    volume_over_time,
)
from tests.conftest import FIXTURES


@pytest.mark.regression
def test_ml_kpis_from_fixtures():
    features = pd.read_csv(FIXTURES / "features_golden.csv")
    preds = pd.read_csv(FIXTURES / "predictions_sample.csv")
    assert sample_volume(features) == 5
    volume_ts = volume_over_time(features, recent_minutes=None)
    assert list(volume_ts.columns) == ["orders"]
    assert int(volume_ts["orders"].sum()) == 5
    assert len(volume_ts) == 1  # golden fixture is within one minute

    # predictions_sample ids don't overlap golden features — empty join is expected
    assert late_flag_rate_over_time(preds, features).empty

    # joinable synthetic pair for the late-flag series
    joined_features = pd.DataFrame(
        {
            "order_id": ["ord-a", "ord-b", "ord-c"],
            "timestamp": [
                "2024-06-15T12:00:00+00:00",
                "2024-06-15T12:00:30+00:00",
                "2024-06-15T12:01:00+00:00",
            ],
        }
    )
    rates = late_flag_rate_over_time(preds, joined_features, recent_minutes=None)
    assert list(rates.columns) == ["late_flag_rate"]
    assert len(rates) == 2
    assert rates.iloc[0]["late_flag_rate"] == pytest.approx(0.5)  # ord-a, ord-b
    assert rates.iloc[1]["late_flag_rate"] == pytest.approx(1.0)  # ord-c

    summary = score_summary(preds)
    assert summary["count"] == 3
    assert summary["mean_probability"] == pytest.approx(0.5333333333)
    assert summary["min_probability"] == pytest.approx(0.2)
    assert summary["max_probability"] == pytest.approx(0.8)
    assert summary["predicted_late_rate"] == pytest.approx(2 / 3)
