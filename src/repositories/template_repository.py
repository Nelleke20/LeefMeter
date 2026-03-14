"""JSON file-based repository for template storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.template import Template

_DEFAULT_PATH: Path = Path.home() / ".leefmeter" / "templates.json"


class TemplateRepository:
    """Stores templates in a local JSON file.

    Data persists across app restarts. The file is created automatically.
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
            List of raw template dicts.
        """
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _dump(self, data: list[dict[str, Any]]) -> None:
        """Write the template list to disk.

        Args:
            data: List of raw template dicts to persist.
        """
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def save(self, template: Template) -> None:
        """Append a new template to storage.

        Args:
            template: The template to save.
        """
        data = self._load()
        data.append(self._to_dict(template))
        self._dump(data)

    def get_all(self) -> list[Template]:
        """Return all stored templates.

        Returns:
            All templates in storage order.
        """
        return [self._from_dict(r) for r in self._load()]

    def delete(self, template_id: str) -> None:
        """Remove a template from storage.

        Args:
            template_id: The UUID of the template to remove.
        """
        data = [r for r in self._load() if r["id"] != template_id]
        self._dump(data)

    @staticmethod
    def _to_dict(template: Template) -> dict[str, Any]:
        """Serialise a Template to a JSON-compatible dict.

        Args:
            template: The template to serialise.

        Returns:
            Dictionary representation of the template.
        """
        return {
            "id": template.id,
            "name": template.name,
            "category": template.category,
            "duration_minutes": template.duration_minutes,
        }

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> Template:
        """Deserialise a raw dict back into a Template.

        Args:
            data: Raw dict from JSON storage.

        Returns:
            Reconstructed Template instance.
        """
        return Template(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            duration_minutes=data["duration_minutes"],
        )
