"""JSON file-based repository for local persistent storage."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from src.models.activity import Activity
from src.repositories.base import ActivityRepository

_DEFAULT_PATH: Path = Path.home() / ".leefmeter" / "activities.json"


class JsonRepository(ActivityRepository):
    """Stores activities in a local JSON file.

    Uses the Repository pattern. Data is persisted across app restarts.
    The storage file is created automatically on first use.
    """

    def __init__(self, file_path: Path = _DEFAULT_PATH) -> None:
        """Initialise with a file path, creating the file if needed.

        Args:
            file_path: Path to the JSON storage file.
        """
        self._path = file_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict[str, Any]]:
        """Read and parse the JSON file.

        Returns:
            List of raw activity dicts.
        """
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _dump(self, data: list[dict[str, Any]]) -> None:
        """Serialise and write the activity list to disk.

        Args:
            data: List of raw activity dicts to persist.
        """
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def save(self, activity: Activity) -> None:
        """Append a new activity to storage.

        Args:
            activity: The activity to save.
        """
        data = self._load()
        data.append(self._to_dict(activity))
        self._dump(data)

    def get_by_id(self, activity_id: str) -> Activity | None:
        """Fetch a single activity by its UUID.

        Args:
            activity_id: The UUID of the activity.

        Returns:
            The matching Activity, or None if not found.
        """
        for raw in self._load():
            if raw["id"] == activity_id:
                return self._from_dict(raw)
        return None

    def get_by_date(self, day: date) -> list[Activity]:
        """Return all activities recorded on a given date.

        Args:
            day: The calendar date to filter by.

        Returns:
            All activities whose date matches the given day.
        """
        return [
            self._from_dict(r) for r in self._load() if r["date"] == day.isoformat()
        ]

    def get_all(self) -> list[Activity]:
        """Return all stored activities.

        Returns:
            All activities in storage order.
        """
        return [self._from_dict(r) for r in self._load()]

    def update(self, activity: Activity) -> None:
        """Replace an existing activity with updated data.

        Args:
            activity: Updated activity matched by id.
        """
        data = self._load()
        self._dump(
            [self._to_dict(activity) if r["id"] == activity.id else r for r in data]
        )

    def delete(self, activity_id: str) -> None:
        """Remove an activity from storage.

        Args:
            activity_id: The UUID of the activity to remove.
        """
        data = [r for r in self._load() if r["id"] != activity_id]
        self._dump(data)

    @staticmethod
    def _to_dict(activity: Activity) -> dict[str, Any]:
        """Serialise an Activity to a JSON-compatible dict.

        Args:
            activity: The activity to serialise.

        Returns:
            Dictionary representation of the activity.
        """
        return {
            "id": activity.id,
            "name": activity.name,
            "category": activity.category,
            "duration_minutes": activity.duration_minutes,
            "date": activity.date.isoformat(),
            "points": activity.points,
            "start_time": activity.start_time,
        }

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> Activity:
        """Deserialise a raw dict back into an Activity.

        Args:
            data: Raw dict from JSON storage.

        Returns:
            Reconstructed Activity instance.
        """
        return Activity(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            duration_minutes=data["duration_minutes"],
            date=date.fromisoformat(data["date"]),
            points=data["points"],
            start_time=data.get("start_time"),
        )
