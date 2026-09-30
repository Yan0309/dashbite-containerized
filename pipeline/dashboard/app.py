"""Streamlit dashboard: Model Pulse (ML monitoring)."""

from __future__ import annotations

import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from pipeline.dashboard.ml_metrics import (
    late_flag_rate_over_time,
    sample_volume,
    score_summary,
    volume_over_time,
)
from pipeline.dashboard.quality_metrics import (
    failures_ranked,
    field_failure_totals,
    throughput_summary,
)
from pipeline.paths import PROJECT_ROOT, features_dir, predictions_dir, quality_dir
from pipeline.preprocess import QUALITY_LOG

ACCENT = "#5B9BD5"
MUTED = "#6B7280"


def _load_csvs(directory: Path, pattern: str) -> pd.DataFrame:
    files = sorted(directory.glob(pattern))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(p) for p in files], ignore_index=True)


def load_features(base: Path | None = None) -> pd.DataFrame:
    return _load_csvs(features_dir(base), "features_*.csv")


def load_predictions(base: Path | None = None) -> pd.DataFrame:
    return _load_csvs(predictions_dir(base), "predictions_*.csv")


def load_quality_log(base: Path | None = None) -> pd.DataFrame:
    path = quality_dir(base) / QUALITY_LOG
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _volume_claim(volume_ts: pd.DataFrame) -> str:
    if volume_ts.empty or len(volume_ts) < 2:
        return "Order volume over the last hour"
    recent = volume_ts["orders"].tail(5).mean()
    prior = volume_ts["orders"].head(max(len(volume_ts) - 5, 1)).mean()
    if prior <= 0:
        return "Orders are arriving in the live window"
    if recent > prior * 1.15:
        return "Order volume is rising in the last hour"
    if recent < prior * 0.85:
        return "Order volume is cooling off in the last hour"
    return "Order volume is steady in the last hour"


def _late_flag_claim(flag_ts: pd.DataFrame, overall_rate: float) -> str:
    if flag_ts.empty:
        return "Late flags over time (waiting for predictions)"
    recent = float(flag_ts["late_flag_rate"].tail(5).mean())
    prior = float(flag_ts["late_flag_rate"].head(max(len(flag_ts) - 5, 1)).mean())
    if recent > prior + 0.08:
        return "We're flagging more orders as late this hour"
    if recent < prior - 0.08:
        return "We're flagging fewer orders as late this hour"
    return f"Late-flag rate is steady near {overall_rate:.0%} this hour"


def _failure_claim(ranked: pd.DataFrame) -> str:
    if ranked.empty:
        return "Field failures (none yet)"
    top = ranked.iloc[0]
    return f"{top['field']} causes the most preprocess failures"


def _volume_chart(volume_ts: pd.DataFrame) -> alt.Chart:
    data = volume_ts.reset_index(names="minute")
    return (
        alt.Chart(data)
        .mark_area(line={"color": ACCENT}, color=ACCENT, opacity=0.35)
        .encode(
            x=alt.X("minute:T", title=None),
            y=alt.Y("orders:Q", title="Orders / minute"),
            tooltip=[
                alt.Tooltip("minute:T", title="Minute"),
                alt.Tooltip("orders:Q", title="Orders"),
            ],
        )
        .properties(height=260)
        .configure_axis(labelColor=MUTED, titleColor=MUTED)
        .configure_view(strokeWidth=0)
    )


def _late_flag_chart(flag_ts: pd.DataFrame) -> alt.Chart:
    data = flag_ts.reset_index(names="minute")
    data["late_flag_pct"] = data["late_flag_rate"] * 100
    return (
        alt.Chart(data)
        .mark_line(color=ACCENT, interpolate="step-after", strokeWidth=2.5)
        .encode(
            x=alt.X("minute:T", title=None),
            y=alt.Y(
                "late_flag_pct:Q",
                title="% flagged late",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip("minute:T", title="Minute"),
                alt.Tooltip("late_flag_pct:Q", title="% flagged late", format=".0f"),
            ],
        )
        .properties(height=260)
        .configure_axis(labelColor=MUTED, titleColor=MUTED)
        .configure_view(strokeWidth=0)
    )


def _failure_chart(ranked: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(ranked)
        .mark_bar(color=ACCENT)
        .encode(
            x=alt.X("failed_rows:Q", title="Failed rows"),
            y=alt.Y("field:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("field:N", title="Field"),
                alt.Tooltip("failed_rows:Q", title="Failed rows"),
            ],
        )
        .properties(height=max(160, 36 * len(ranked)))
        .configure_axis(labelColor=MUTED, titleColor=MUTED)
        .configure_view(strokeWidth=0)
    )


def main() -> None:
    st.set_page_config(page_title="DashBite", layout="wide")
    st.title("DashBite")
    auto = st.sidebar.checkbox("Auto-refresh (15s)", value=True)

    base = PROJECT_ROOT
    features = load_features(base)
    predictions = load_predictions(base)
    quality = load_quality_log(base)
    throughput = throughput_summary(quality)
    failures = field_failure_totals(quality)
    summary = score_summary(predictions)

    st.header("Model Pulse")
    st.caption("Is the late-prediction system healthy?")

    c1, c2, c3 = st.columns(3)
    c1.metric("Samples scored", f"{sample_volume(features):,}")
    c2.metric("Drop rate", f"{throughput['drop_rate']:.0%}")
    c3.metric("Late flag rate", f"{summary['predicted_late_rate']:.0%}")

    volume_ts = volume_over_time(features, recent_minutes=60)
    st.subheader(_volume_claim(volume_ts))
    st.caption("Last 60 minutes of feature rows · orders per minute")
    if not volume_ts.empty:
        st.altair_chart(_volume_chart(volume_ts), width="stretch")
    else:
        st.info("No timestamped features yet — waiting for preprocess.")

    flag_ts = late_flag_rate_over_time(predictions, features, recent_minutes=60)
    st.subheader(_late_flag_claim(flag_ts, summary["predicted_late_rate"]))
    st.caption("Share of scored orders with predicted_late = 1 · step line by minute")
    if not flag_ts.empty:
        st.altair_chart(_late_flag_chart(flag_ts), width="stretch")
    else:
        st.info("No joinable predictions yet — waiting for infer.")

    ranked = failures_ranked(failures)
    st.subheader(_failure_claim(ranked))
    st.caption("Corrupt / invalid fields caught in preprocess")
    if not ranked.empty and ranked["failed_rows"].sum() > 0:
        st.altair_chart(_failure_chart(ranked), width="stretch")
    else:
        st.info("No field failures yet — waiting for preprocess.")

    if auto:
        time.sleep(15)
        st.rerun()


if __name__ == "__main__":
    main()
