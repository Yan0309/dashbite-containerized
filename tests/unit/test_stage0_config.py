"""Unit tests for Stage 0 — config and paths."""

from __future__ import annotations

import os

import pytest

from pipeline.config import DEFAULT_CONFIG, Config, load_config
from pipeline.paths import DATA_SUBDIRS, PROJECT_ROOT, data_root, ensure_data_dirs, raw_dir


@pytest.mark.unit
def test_default_config_train_every_n_events():
    assert DEFAULT_CONFIG.train_every_n_events == 2000
    assert DEFAULT_CONFIG.batch_size == 50


@pytest.mark.unit
def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("TRAIN_EVERY_N_EVENTS", "10")
    monkeypatch.setenv("BATCH_SIZE", "5")
    cfg = load_config()
    assert cfg.train_every_n_events == 10
    assert cfg.batch_size == 5


@pytest.mark.unit
def test_required_data_dir_helpers(tmp_path):
    ensure_data_dirs(tmp_path)
    assert raw_dir(tmp_path).exists()
    assert raw_dir(tmp_path).name == "raw"


@pytest.mark.unit
def test_data_root_prefers_explicit_project_base_over_environment(tmp_path, monkeypatch):
    data_root_env = tmp_path / "environment-data"
    monkeypatch.setenv("DATA_ROOT", str(data_root_env))

    assert data_root(tmp_path / "project") == tmp_path / "project" / "data"


@pytest.mark.unit
def test_data_root_uses_environment_as_the_data_directory(tmp_path, monkeypatch):
    configured_root = tmp_path / "configured-data"
    monkeypatch.setenv("DATA_ROOT", str(configured_root))

    assert data_root() == configured_root


@pytest.mark.unit
def test_data_root_reads_environment_at_call_time(tmp_path, monkeypatch):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    monkeypatch.setenv("DATA_ROOT", str(first_root))
    assert data_root() == first_root

    monkeypatch.setenv("DATA_ROOT", str(second_root))
    assert data_root() == second_root


@pytest.mark.unit
def test_data_root_defaults_to_project_data(tmp_path, monkeypatch):
    monkeypatch.delenv("DATA_ROOT", raising=False)

    assert data_root() == PROJECT_ROOT / "data"
