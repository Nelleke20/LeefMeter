"""Day model for LeefMeter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date  # noqa: F401 — used in dataclass field annotation

from src.models.activity import Activity


@dataclass
class Day:
    """Aggregates all activities that belong to a single calendar date.

    Attributes:
        date: The calendar date this day represents.
        activities: All activities recorded on this date.
    """

    date: date
    activities: list[Activity]

    @property
    def total_points(self) -> int:
        """Return the sum of points across all activities.

        Returns:
            Total points for the day, or 0 if there are no activities.
        """
        return sum(activity.points for activity in self.activities)
