"""Shared helper for resolving the app's writable storage directory.

On Android and iOS, Flet sets FLET_APP_STORAGE_DATA to the app's private
sandboxed directory. On desktop the data lives in ~/.leefmeter.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_data_dir() -> Path:
    """Return the writable data directory for this platform.

    Returns:
        Path to the directory where LeefMeter stores its JSON files.
        Created automatically if it does not exist.
    """
    env = os.environ.get("FLET_APP_STORAGE_DATA")
    base = Path(env) if env else Path.home() / ".leefmeter"
    base.mkdir(parents=True, exist_ok=True)
    return base
