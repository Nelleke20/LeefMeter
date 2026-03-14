"""Settings service — reads and writes user preferences to a local JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from src.models.settings import AppSettings

_DEFAULT_PATH: Path = Path.home() / ".leefmeter" / "settings.json"


class SettingsService:
    """Persists AppSettings to a local JSON file.

    Uses the Repository pattern internally with a single JSON file.
    """

    def __init__(self, file_path: Path = _DEFAULT_PATH) -> None:
        """Initialise with an optional custom file path.

        Args:
            file_path: Path to the settings JSON file.
        """
        self._path = file_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppSettings:
        """Load settings from disk, returning defaults if the file does not exist.

        Returns:
            The stored AppSettings, or a default instance.
        """
        if not self._path.exists():
            return AppSettings()
        try:
            data: dict = json.loads(self._path.read_text(encoding="utf-8"))
            return AppSettings(
                day_start_hour=int(data.get("day_start_hour", 6)),
                day_end_hour=int(data.get("day_end_hour", 22)),
                green_threshold=int(data.get("green_threshold", 5)),
                orange_threshold=int(data.get("orange_threshold", 10)),
                red_threshold=int(data.get("red_threshold", 20)),
            )
        except (json.JSONDecodeError, ValueError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """Persist settings to disk.

        Args:
            settings: The AppSettings instance to save.
        """
        self._path.write_text(
            json.dumps(
                {
                    "day_start_hour": settings.day_start_hour,
                    "day_end_hour": settings.day_end_hour,
                    "green_threshold": settings.green_threshold,
                    "orange_threshold": settings.orange_threshold,
                    "red_threshold": settings.red_threshold,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
