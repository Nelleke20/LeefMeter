"""Point calculation strategies using the Strategy pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.activity import Activity

CATEGORY_BASE_POINTS: dict[str, int] = {
    "sport": 10,
    "voeding": 5,
    "mentaal": 8,
    "sociaal": 6,
    "rust": 4,
}

POINTS_PER_TEN_MINUTES: int = 1


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
            Integer point value, always >= 0.
        """


class CategoryPointStrategy(PointCalculationStrategy):
    """Awards a fixed number of points based on activity category.

    Uses the Strategy pattern. Points are defined in CATEGORY_BASE_POINTS.
    Unknown categories receive zero points.
    """

    def calculate(self, activity: Activity) -> int:
        """Return the category base points for the activity.

        Args:
            activity: The activity to score.

        Returns:
            Points defined for the category, or 0 if unknown.
        """
        return CATEGORY_BASE_POINTS.get(activity.category, 0)


class DurationPointStrategy(PointCalculationStrategy):
    """Awards one point for every ten minutes of activity duration.

    Uses the Strategy pattern. Short activities below 10 minutes
    receive zero points.
    """

    def calculate(self, activity: Activity) -> int:
        """Return points based on activity duration.

        Args:
            activity: The activity to score.

        Returns:
            Points equal to duration_minutes // 10.
        """
        return (activity.duration_minutes // 10) * POINTS_PER_TEN_MINUTES


class CombinedPointStrategy(PointCalculationStrategy):
    """Combines category base points with duration bonus points.

    Uses the Strategy pattern. Delegates to CategoryPointStrategy and
    DurationPointStrategy and sums their results.
    """

    def __init__(self) -> None:
        """Initialise with both sub-strategies."""
        self._category = CategoryPointStrategy()
        self._duration = DurationPointStrategy()

    def calculate(self, activity: Activity) -> int:
        """Return base category points plus duration bonus.

        Args:
            activity: The activity to score.

        Returns:
            Sum of category and duration points.
        """
        return self._category.calculate(activity) + self._duration.calculate(
            activity
        )
