"""Unit tests for Stage 5 — ML dashboard helpers."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.dashboard.ml_metrics import (
    late_flag_rate_over_time,
    sample_volume,
    score_summary,
    volume_over_time,
)


@pytest.mark.unit
def test_sample_volume_and_score_summary():
    features = pd.DataFrame({"order_id": ["a", "b", "c"]})
    assert sample_volume(features) == 3
    assert sample_volume(pd.DataFrame()) == 0

    preds = pd.DataFrame(
        {
            "late_probability": [0.1, 0.9, 0.5],
            "predicted_late": [0, 1, 1],
        }
    )
    summary = score_summary(preds)
    assert summary["count"] == 3
    assert summary["mean_probability"] == pytest.approx(0.5)
    assert summary["min_probability"] == pytest.approx(0.1)
    assert summary["max_probability"] == pytest.approx(0.9)
    assert summary["predicted_late_rate"] == pytest.approx(2 / 3)


@pytest.mark.unit
def test_volume_over_time_buckets_by_minute():
    features = pd.DataFrame(
        {
            "timestamp": [
                "2024-06-15T12:00:10+00:00",
                "2024-06-15T12:00:50+00:00",
                "2024-06-15T12:01:05+00:00",
                "not-a-time",
            ]
        }
    )
    chart = volume_over_time(features, recent_minutes=None)
    assert list(chart.columns) == ["orders"]
    assert chart["orders"].sum() == 3
    assert len(chart) == 2
    assert volume_over_time(pd.DataFrame()).empty
    assert volume_over_time(pd.DataFrame({"order_id": [1]})).empty


@pytest.mark.unit
def test_late_flag_rate_over_time_by_minute():
    features = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "timestamp": [
                "2024-06-15T12:00:10+00:00",
                "2024-06-15T12:00:50+00:00",
                "2024-06-15T12:01:05+00:00",
                "2024-06-15T12:01:40+00:00",
            ],
        }
    )
    preds = pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "predicted_late": [1, 0, 1, 1],
        }
    )
    rates = late_flag_rate_over_time(preds, features, recent_minutes=None)
    assert list(rates.columns) == ["late_flag_rate"]
    assert len(rates) == 2
    assert rates.iloc[0]["late_flag_rate"] == pytest.approx(0.5)  # a=1, b=0
    assert rates.iloc[1]["late_flag_rate"] == pytest.approx(1.0)  # c=1, d=1
    assert late_flag_rate_over_time(pd.DataFrame(), features).empty
    assert late_flag_rate_over_time(preds, pd.DataFrame()).empty
