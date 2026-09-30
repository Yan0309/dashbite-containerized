"""Helpers for publishing complete files to shared pipeline directories."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path


def atomic_write(destination: Path, writer: Callable[[Path], object]) -> None:
    """Write beside the destination, then publish the complete file atomically."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.name}.tmp")
    try:
        writer(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)