"""Stage 7: worker subprocesses stop cleanly on SIGTERM."""

from __future__ import annotations

import os
import select
import signal
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKERS = [
    "pipeline.simulator",
    "pipeline.preprocess",
    "pipeline.train",
    "pipeline.infer",
]


@pytest.mark.integration
@pytest.mark.parametrize("module", WORKERS)
@pytest.mark.parametrize("stop_signal", [signal.SIGTERM, signal.SIGINT])
def test_worker_signal_exits_cleanly_and_uses_temporary_data_root(
    tmp_path, module, stop_signal
):
    isolated_project = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "pipeline", isolated_project / "pipeline")
    data_root = tmp_path / module.rsplit(".", 1)[-1]
    env = os.environ.copy()
    env.update(
        {
            "DATA_ROOT": str(data_root),
            "POLL_INTERVAL_SECONDS": "0.1",
            "PYTHONPATH": str(isolated_project),
            "PYTHONUNBUFFERED": "1",
        }
    )
    process = subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=isolated_project,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        assert process.stdout is not None
        ready, _, _ = select.select([process.stdout], [], [], 10)
        assert ready, f"{module} did not emit startup output"
        process.stdout.readline()
        process.send_signal(stop_signal)
        output, _ = process.communicate(timeout=3)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)

    assert process.returncode == 0, output
    assert "shutting down" in output
    assert data_root.is_dir()