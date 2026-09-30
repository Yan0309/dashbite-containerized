"""Shared signal-to-event wiring for foreground pipeline workers."""

from __future__ import annotations

import signal
import threading


def install_shutdown_handlers() -> threading.Event:
    """Install SIGTERM/SIGINT handlers that only request worker shutdown."""
    stop_event = threading.Event()

    def request_shutdown(_signum: int, _frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    return stop_event