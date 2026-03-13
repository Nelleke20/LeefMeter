"""Abstract base repository using the Repository pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from src.models.activity import Activity


class ActivityRepository(ABC):
    """Abstract base for activity storage backends.

    Concrete implementations must provide all CRUD operations.
    This contract allows the ActivityService to remain decoupled
    from any specific storage technology.
    """

    @abstractmethod
    def save(self, activity: Activity) -> None:
        """Persist a new activity to storage.

        Args:
            activity: The activity to save.
        """

    @abstractmethod
    def get_by_id(self, activity_id: str) -> Activity | None:
        """Fetch a single activity by its unique identifier.

        Args:
            activity_id: The UUID of the activity.

        Returns:
            The matching Activity, or None if not found.
        """

    @abstractmethod
    def get_by_date(self, day: date) -> list[Activity]:
        """Return all activities recorded on a given date.

        Args:
            day: The calendar date to filter by.

        Returns:
            List of activities for that date, possibly empty.
        """

    @abstractmethod
    def get_all(self) -> list[Activity]:
        """Return every stored activity.

        Returns:
            All activities across all dates.
        """

    @abstractmethod
    def update(self, activity: Activity) -> None:
        """Replace an existing activity with updated data.

        Args:
            activity: Activity with updated fields. Matched by id.
        """

    @abstractmethod
    def delete(self, activity_id: str) -> None:
        """Remove an activity from storage.

        Args:
            activity_id: The UUID of the activity to remove.
        """
