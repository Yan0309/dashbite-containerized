"""Stage 5 — ML monitoring helpers (sample volume + late-flag rate)."""

from __future__ import annotations

import pandas as pd


def sample_volume(features: pd.DataFrame) -> int:
    """Count of feature samples available."""
    if features is None or features.empty:
        return 0
    return int(len(features))


def volume_over_time(
    features: pd.DataFrame,
    freq: str = "min",
    recent_minutes: int | None = 60,
) -> pd.DataFrame:
    """Bucket feature rows by timestamp for a time-series volume chart.

    Returns a DataFrame indexed by time with a single ``orders`` column
    (orders per time bucket). Empty / missing timestamps yield an empty frame.
    When ``recent_minutes`` is set, only the trailing window is returned so
    long quiet stretches don't bury the live story.
    """
    empty = pd.DataFrame(columns=["orders"])
    if features is None or features.empty or "timestamp" not in features.columns:
        return empty
    ts = pd.to_datetime(features["timestamp"], utc=True, errors="coerce")
    valid = ts.dropna()
    if valid.empty:
        return empty
    series = valid.dt.floor(freq).value_counts().sort_index().rename("orders")
    if recent_minutes is not None and len(series) > 0:
        cutoff = series.index.max() - pd.Timedelta(minutes=recent_minutes)
        series = series.loc[series.index >= cutoff]
    return series.to_frame()


def late_flag_rate_over_time(
    predictions: pd.DataFrame,
    features: pd.DataFrame,
    freq: str = "min",
    recent_minutes: int | None = 60,
) -> pd.DataFrame:
    """Share of orders flagged ``predicted_late`` per time bucket.

    Joins predictions to feature timestamps via ``order_id``. Returns a
    DataFrame indexed by time with ``late_flag_rate`` in ``[0, 1]``.
    """
    empty = pd.DataFrame(columns=["late_flag_rate"])
    if (
        predictions is None
        or predictions.empty
        or features is None
        or features.empty
        or "predicted_late" not in predictions.columns
        or "order_id" not in predictions.columns
        or "order_id" not in features.columns
        or "timestamp" not in features.columns
    ):
        return empty

    preds = predictions.loc[:, ["order_id", "predicted_late"]].copy()
    feats = features.loc[:, ["order_id", "timestamp"]].copy()
    preds["order_id"] = preds["order_id"].astype(str)
    feats["order_id"] = feats["order_id"].astype(str)
    merged = preds.merge(feats, on="order_id", how="inner")
    if merged.empty:
        return empty

    ts = pd.to_datetime(merged["timestamp"], utc=True, errors="coerce")
    merged = merged.loc[ts.notna()].copy()
    if merged.empty:
        return empty
    merged["_minute"] = ts.dropna().dt.floor(freq)
    merged["predicted_late"] = merged["predicted_late"].astype(int)
    rates = merged.groupby("_minute", sort=True)["predicted_late"].mean().rename(
        "late_flag_rate"
    )
    if recent_minutes is not None and len(rates) > 0:
        cutoff = rates.index.max() - pd.Timedelta(minutes=recent_minutes)
        rates = rates.loc[rates.index >= cutoff]
    return rates.to_frame()


def score_summary(predictions: pd.DataFrame) -> dict:
    """Simple summary of late_probability / predicted_late outputs."""
    if predictions is None or predictions.empty or "late_probability" not in predictions.columns:
        return {
            "count": 0,
            "mean_probability": 0.0,
            "min_probability": 0.0,
            "max_probability": 0.0,
            "predicted_late_rate": 0.0,
        }
    probs = predictions["late_probability"].astype(float)
    pred_late = (
        predictions["predicted_late"].astype(int).mean()
        if "predicted_late" in predictions.columns
        else 0.0
    )
    return {
        "count": int(len(predictions)),
        "mean_probability": float(probs.mean()),
        "min_probability": float(probs.min()),
        "max_probability": float(probs.max()),
        "predicted_late_rate": float(pred_late),
    }
