"""In-memory repository implementation — intended for testing."""

from __future__ import annotations

from datetime import date

from src.models.activity import Activity
from src.repositories.base import ActivityRepository


class InMemoryRepository(ActivityRepository):
    """Stores activities in a plain Python dict.

    Uses the Repository pattern. This implementation is not persistent
    and is designed for use in unit tests and local development.
    """

    def __init__(self) -> None:
        """Initialise with an empty in-memory store."""
        self._store: dict[str, Activity] = {}

    def save(self, activity: Activity) -> None:
        """Persist an activity to the in-memory store.

        Args:
            activity: The activity to save.
        """
        self._store[activity.id] = activity

    def get_by_id(self, activity_id: str) -> Activity | None:
        """Fetch an activity by ID.

        Args:
            activity_id: The UUID of the activity.

        Returns:
            The matching Activity, or None if not found.
        """
        return self._store.get(activity_id)

    def get_by_date(self, day: date) -> list[Activity]:
        """Return all activities on a given date.

        Args:
            day: The calendar date to filter by.

        Returns:
            All activities whose date matches the given day.
        """
        return [a for a in self._store.values() if a.date == day]

    def get_all(self) -> list[Activity]:
        """Return all stored activities.

        Returns:
            All activities in insertion order.
        """
        return list(self._store.values())

    def update(self, activity: Activity) -> None:
        """Replace an existing activity with updated data.

        Args:
            activity: Updated activity matched by id.
        """
        self._store[activity.id] = activity

    def delete(self, activity_id: str) -> None:
        """Remove an activity from the store.

        Args:
            activity_id: The UUID of the activity to remove.
        """
        self._store.pop(activity_id, None)
