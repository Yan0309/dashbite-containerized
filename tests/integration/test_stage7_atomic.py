"""Stage 7: publish complete pipeline outputs without exposing temporary files."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline import atomic
from pipeline.infer import run_once
from pipeline.paths import features_dir, models_dir, predictions_dir, quality_dir, raw_dir
from pipeline.preprocess import QUALITY_LOG, process_new_raw_files
from pipeline.simulator import generate_batch, write_batch
from pipeline.train import save_state, train_model, write_checkpoint
from tests.conftest import FIXTURES


@pytest.mark.unit
def test_atomic_write_keeps_final_glob_invisible_until_replace(tmp_path):
    destination = raw_dir(tmp_path) / "orders_partial.csv"
    observed = []

    def write_csv(temporary):
        observed.append(temporary)
        temporary.write_text("partial")
        assert not destination.exists()
        assert list(destination.parent.glob("orders_*.csv")) == []
        assert temporary == destination.with_name("orders_partial.csv.tmp")
        temporary.write_text("complete")

    atomic.atomic_write(destination, write_csv)

    assert observed == [destination.with_name("orders_partial.csv.tmp")]
    assert list(destination.parent.glob("orders_*.csv")) == [destination]
    assert destination.read_text() == "complete"
    assert not observed[0].exists()


@pytest.mark.integration
def test_all_whole_file_writers_use_shared_atomic_publication(tmp_path, monkeypatch):
    published = []
    original_atomic_write = atomic.atomic_write

    def record_publication(destination, writer):
        published.append(destination)
        return original_atomic_write(destination, writer)

    monkeypatch.setattr(atomic, "atomic_write", record_publication)

    raw_file = write_batch(generate_batch(6, seed=13), raw_dir(tmp_path))
    feature_files = process_new_raw_files(base=tmp_path)
    assert len(feature_files) == 1

    training_rows = pd.read_csv(FIXTURES / "features_train.csv")
    model, metrics = train_model(training_rows, seed=42)
    checkpoint = write_checkpoint(
        model, metrics, base=tmp_path, stamp="20240101_000000"
    )
    save_state(
        {"labeled_rows_at_last_train": len(training_rows), "last_checkpoint": checkpoint.name},
        base=tmp_path,
    )
    prediction_file = run_once(base=tmp_path)
    assert prediction_file is not None

    expected_files = {
        raw_file,
        feature_files[0],
        checkpoint,
        models_dir(tmp_path) / "metrics_20240101_000000.json",
        models_dir(tmp_path) / "train_state.json",
        prediction_file,
    }
    assert set(published) == expected_files
    assert (quality_dir(tmp_path) / QUALITY_LOG).exists()
    assert quality_dir(tmp_path) / QUALITY_LOG not in published
    assert not list(tmp_path.rglob("*.tmp"))
    assert raw_file.parent == raw_dir(tmp_path)
    assert feature_files[0].parent == features_dir(tmp_path)
    assert prediction_file.parent == predictions_dir(tmp_path)
    assert checkpoint.parent == models_dir(tmp_path)