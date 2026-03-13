"""Tests for ActivityService."""

from __future__ import annotations

import unittest
from datetime import date

from src.models.activity import Activity
from src.repositories.in_memory_repository import InMemoryRepository
from src.services.activity_service import ActivityService
from src.services.point_strategy import CombinedPointStrategy


def _make_service() -> ActivityService:
    """Build an ActivityService backed by an in-memory repository.

    Returns:
        ActivityService ready for testing.
    """
    return ActivityService(
        repository=InMemoryRepository(),
        strategy=CombinedPointStrategy(),
    )


def _activity(
    name: str = "Hardlopen",
    category: str = "sport",
    duration: int = 30,
    activity_date: date | None = None,
) -> Activity:
    """Create a minimal test Activity.

    Args:
        name: Activity name.
        category: Activity category.
        duration: Duration in minutes.
        activity_date: Date for the activity. Defaults to 2024-01-15.

    Returns:
        A new Activity instance with zero points.
    """
    return Activity(
        name=name,
        category=category,
        duration_minutes=duration,
        date=activity_date or date(2024, 1, 15),
    )


class TestAddActivity(unittest.TestCase):
    """Tests for ActivityService.add_activity."""

    def setUp(self) -> None:
        """Prepare service under test."""
        self.service = _make_service()

    def test_add_activity_sets_points(self) -> None:
        """add_activity should populate the points field via the strategy."""
        activity = _activity(category="sport", duration=30)
        saved = self.service.add_activity(activity)
        self.assertGreater(saved.points, 0)

    def test_add_activity_persists_to_repository(self) -> None:
        """add_activity should make the activity retrievable from the repo."""
        activity = _activity()
        self.service.add_activity(activity)
        day = self.service.get_activities_for_day(activity.date)
        self.assertIn(activity, day.activities)


class TestUpdateActivity(unittest.TestCase):
    """Tests for ActivityService.update_activity."""

    def setUp(self) -> None:
        """Prepare service with one existing activity."""
        self.service = _make_service()
        self.activity = _activity(duration=10)
        self.service.add_activity(self.activity)

    def test_update_recalculates_points(self) -> None:
        """update_activity should recalculate points with the new data."""
        original_points = self.activity.points
        self.activity.duration_minutes = 60
        updated = self.service.update_activity(self.activity)
        self.assertGreater(updated.points, original_points)

    def test_update_persists_changes(self) -> None:
        """update_activity should save the new duration to the repository."""
        self.activity.duration_minutes = 60
        self.service.update_activity(self.activity)
        day = self.service.get_activities_for_day(self.activity.date)
        stored = next(a for a in day.activities if a.id == self.activity.id)
        self.assertEqual(stored.duration_minutes, 60)


class TestDeleteActivity(unittest.TestCase):
    """Tests for ActivityService.delete_activity."""

    def setUp(self) -> None:
        """Prepare service with one existing activity."""
        self.service = _make_service()
        self.activity = _activity()
        self.service.add_activity(self.activity)

    def test_delete_removes_activity_from_day(self) -> None:
        """After deletion the activity should not appear in its day."""
        self.service.delete_activity(self.activity.id)
        day = self.service.get_activities_for_day(self.activity.date)
        self.assertNotIn(self.activity, day.activities)


class TestGetActivitiesForDay(unittest.TestCase):
    """Tests for ActivityService.get_activities_for_day."""

    def setUp(self) -> None:
        """Prepare service with activities on two different dates."""
        self.service = _make_service()
        self.day_a = date(2024, 1, 15)
        self.day_b = date(2024, 1, 16)
        self.act_a = self.service.add_activity(_activity(activity_date=self.day_a))
        self.act_b = self.service.add_activity(_activity(activity_date=self.day_b))

    def test_returns_only_activities_for_requested_date(self) -> None:
        """Only activities on the requested date should be in the returned Day."""
        day = self.service.get_activities_for_day(self.day_a)
        self.assertIn(self.act_a, day.activities)
        self.assertNotIn(self.act_b, day.activities)

    def test_returns_day_with_correct_date(self) -> None:
        """The returned Day should carry the requested date."""
        day = self.service.get_activities_for_day(self.day_a)
        self.assertEqual(day.date, self.day_a)


class TestGetAllDays(unittest.TestCase):
    """Tests for ActivityService.get_all_days."""

    def setUp(self) -> None:
        """Prepare service with activities on two dates."""
        self.service = _make_service()
        self.day_old = date(2024, 1, 10)
        self.day_new = date(2024, 1, 20)
        self.service.add_activity(_activity(activity_date=self.day_old))
        self.service.add_activity(_activity(activity_date=self.day_new))

    def test_returns_one_day_per_date(self) -> None:
        """get_all_days should return exactly one Day per unique date."""
        days = self.service.get_all_days()
        self.assertEqual(len(days), 2)

    def test_days_are_sorted_newest_first(self) -> None:
        """get_all_days should return days in descending date order."""
        days = self.service.get_all_days()
        self.assertEqual(days[0].date, self.day_new)
        self.assertEqual(days[1].date, self.day_old)

    def test_empty_service_returns_no_days(self) -> None:
        """get_all_days on an empty service should return an empty list."""
        empty_service = _make_service()
        self.assertEqual(empty_service.get_all_days(), [])


if __name__ == "__main__":
    unittest.main()
