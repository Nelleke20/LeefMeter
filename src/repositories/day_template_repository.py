"""JSON file-based repository for day templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.day_template import DayTemplate, DayTemplateEntry
from src.storage import get_data_dir

_DEFAULT_PATH: Path = get_data_dir() / "day_templates.json"


class DayTemplateRepository:
    """Persists day templates as a local JSON file.

    Uses the Repository pattern to decouple storage from business logic.
    """

    def __init__(self, file_path: Path = _DEFAULT_PATH) -> None:
        """Initialise, creating the file if it does not exist.

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
            List of raw day-template dicts.
        """
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _dump(self, data: list[dict[str, Any]]) -> None:
        """Serialise and write the template list to disk.

        Args:
            data: List of raw day-template dicts.
        """
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def get_by_id(self, template_id: str) -> DayTemplate | None:
        """Return a single template by its UUID, or None if not found.

        Args:
            template_id: UUID to look up.

        Returns:
            Matching DayTemplate, or None.
        """
        for raw in self._load():
            if raw["id"] == template_id:
                return self._from_dict(raw)
        return None

    def get_all(self) -> list[DayTemplate]:
        """Return all stored day templates.

        Returns:
            All day templates in storage order.
        """
        return [self._from_dict(r) for r in self._load()]

    def save(self, template: DayTemplate) -> None:
        """Append a new day template to storage.

        Args:
            template: The day template to persist.
        """
        data = self._load()
        data.append(self._to_dict(template))
        self._dump(data)

    def update(self, template: DayTemplate) -> None:
        """Replace an existing day template with updated data.

        Args:
            template: Updated template matched by id.
        """
        data = self._load()
        self._dump(
            [self._to_dict(template) if r["id"] == template.id else r for r in data]
        )

    def delete(self, template_id: str) -> None:
        """Remove a day template by id.

        Args:
            template_id: UUID of the template to remove.
        """
        self._dump([r for r in self._load() if r["id"] != template_id])

    @staticmethod
    def _to_dict(template: DayTemplate) -> dict[str, Any]:
        """Serialise a DayTemplate to a JSON-compatible dict.

        Args:
            template: The template to serialise.

        Returns:
            Dictionary representation.
        """
        return {
            "id": template.id,
            "name": template.name,
            "entries": [
                {
                    "activity_name": e.activity_name,
                    "category": e.category,
                    "start_time": e.start_time,
                    "duration_minutes": e.duration_minutes,
                }
                for e in template.entries
            ],
        }

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> DayTemplate:
        """Deserialise a raw dict into a DayTemplate.

        Args:
            data: Raw dict from JSON storage.

        Returns:
            Reconstructed DayTemplate.
        """
        entries = [
            DayTemplateEntry(
                activity_name=e["activity_name"],
                category=e["category"],
                start_time=e["start_time"],
                duration_minutes=e["duration_minutes"],
            )
            for e in data.get("entries", [])
        ]
        return DayTemplate(id=data["id"], name=data["name"], entries=entries)
