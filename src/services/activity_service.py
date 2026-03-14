"""Activity business logic using the Repository and Strategy patterns."""

from __future__ import annotations

import calendar
from datetime import date

from src.models.activity import Activity
from src.models.day import Day
from src.repositories.base import ActivityRepository
from src.services.point_strategy import PointCalculationStrategy


class ActivityService:
    """Orchestrates activity CRUD and point scoring.

    Uses the Repository pattern for persistence and the Strategy pattern
    for point calculation. Neither the storage backend nor the scoring
    algorithm is hardcoded — both are injected at construction time.
    """

    def __init__(
        self,
        repository: ActivityRepository,
        strategy: PointCalculationStrategy,
    ) -> None:
        """Initialise the service with a repository and a scoring strategy.

        Args:
            repository: The storage backend to persist activities.
            strategy: The algorithm used to calculate activity points.
        """
        self._repository = repository
        self._strategy = strategy

    def add_activity(self, activity: Activity) -> Activity:
        """Score and persist a new activity.

        Args:
            activity: The activity to add. Points are calculated and set.

        Returns:
            The activity with its points field populated.
        """
        activity.points = self._strategy.calculate(activity)
        self._repository.save(activity)
        return activity

    def update_activity(self, activity: Activity) -> Activity:
        """Recalculate points and persist changes to an existing activity.

        Args:
            activity: Updated activity (matched by id).

        Returns:
            The activity with recalculated points.
        """
        activity.points = self._strategy.calculate(activity)
        self._repository.update(activity)
        return activity

    def delete_activity(self, activity_id: str) -> None:
        """Remove an activity from storage.

        Args:
            activity_id: The UUID of the activity to delete.
        """
        self._repository.delete(activity_id)

    def get_activities_for_day(self, day: date) -> Day:
        """Return a Day object aggregating all activities for a date.

        Args:
            day: The calendar date to retrieve activities for.

        Returns:
            Day instance containing activities and their total points.
        """
        activities = self._repository.get_by_date(day)
        return Day(date=day, activities=activities)

    def get_activity_by_id(self, activity_id: str) -> Activity | None:
        """Return a single activity by its UUID.

        Args:
            activity_id: The UUID of the activity to retrieve.

        Returns:
            The matching Activity, or None if not found.
        """
        return self._repository.get_by_id(activity_id)

    def get_month_summary(self, year: int, month: int) -> list[Day]:
        """Return one Day per calendar day in the given month.

        Days with no recorded activities are included with an empty list.
        Days are returned in ascending date order.

        Args:
            year: Four-digit calendar year.
            month: Calendar month, 1-12.

        Returns:
            list[Day] with one entry per calendar day of the month.
        """
        _, days_in_month = calendar.monthrange(year, month)
        return [
            self.get_activities_for_day(date(year, month, d))
            for d in range(1, days_in_month + 1)
        ]

    def get_all_days(self) -> list[Day]:
        """Return one Day per date that has at least one activity.

        Returns:
            Days sorted from most recent to oldest.
        """
        activities = self._repository.get_all()
        days_map: dict[date, list[Activity]] = {}
        for activity in activities:
            days_map.setdefault(activity.date, []).append(activity)
        return [
            Day(date=d, activities=acts)
            for d, acts in sorted(days_map.items(), reverse=True)
        ]
