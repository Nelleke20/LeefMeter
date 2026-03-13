"""Point calculation strategies using the Strategy pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.activity import Activity

INTENSITY_MULTIPLIERS: dict[str, int] = {
    "rust": -1,
    "laag": 1,
    "gemiddeld": 2,
    "zwaar": 3,
}

MINUTES_PER_HALF_HOUR: int = 30


class PointCalculationStrategy(ABC):
    """Abstract base for point calculation algorithms.

    Concrete strategies are injected into ActivityService, allowing
    the scoring logic to be swapped without changing business logic.
    """

    @abstractmethod
    def calculate(self, activity: Activity) -> int:
        """Calculate the point value for a given activity.

        Args:
            activity: The activity to score.

        Returns:
            Integer point value (may be negative for rust activities).
        """


class IntensityPointStrategy(PointCalculationStrategy):
    """Awards points based on intensity level and duration.

    Uses the Strategy pattern. Points = multiplier × (duration / 30 min):
    - rust:     -1 per half hour
    - laag:     +1 per half hour
    - gemiddeld: +2 per half hour
    - zwaar:    +3 per half hour
    """

    def calculate(self, activity: Activity) -> int:
        """Return points based on intensity and duration.

        Args:
            activity: The activity to score.

        Returns:
            Points rounded to nearest integer. Can be negative for rust.
        """
        multiplier = INTENSITY_MULTIPLIERS.get(activity.category, 0)
        half_hours = activity.duration_minutes / MINUTES_PER_HALF_HOUR
        return round(multiplier * half_hours)
