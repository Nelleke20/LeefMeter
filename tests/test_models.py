"""Tests for Activity and Day models."""

from __future__ import annotations

import unittest
from datetime import date

from src.models.activity import Activity
from src.models.day import Day


class TestActivity(unittest.TestCase):
    """Tests for the Activity dataclass."""

    def test_default_points_is_zero(self) -> None:
        """A newly created activity should have zero points."""
        activity = Activity(
            name="Hardlopen",
            category="sport",
            duration_minutes=30,
            date=date(2024, 1, 15),
        )
        self.assertEqual(activity.points, 0)

    def test_id_is_auto_generated(self) -> None:
        """Two activities created without explicit IDs should have different IDs."""
        a1 = Activity("A", "sport", 10, date(2024, 1, 1))
        a2 = Activity("B", "sport", 10, date(2024, 1, 1))
        self.assertNotEqual(a1.id, a2.id)

    def test_explicit_id_is_preserved(self) -> None:
        """An explicitly set ID should not be overwritten."""
        activity = Activity("A", "sport", 10, date(2024, 1, 1), id="fixed-id")
        self.assertEqual(activity.id, "fixed-id")


class TestDay(unittest.TestCase):
    """Tests for the Day dataclass."""

    def _make_activity(self, points: int) -> Activity:
        a = Activity("X", "sport", 10, date(2024, 1, 1))
        a.points = points
        return a

    def test_total_points_sums_all_activities(self) -> None:
        """total_points should return the sum of all activity points."""
        day = Day(
            date=date(2024, 1, 1),
            activities=[
                self._make_activity(10),
                self._make_activity(5),
                self._make_activity(8),
            ],
        )
        self.assertEqual(day.total_points, 23)

    def test_total_points_empty_day_is_zero(self) -> None:
        """total_points should return 0 when there are no activities."""
        day = Day(date=date(2024, 1, 1), activities=[])
        self.assertEqual(day.total_points, 0)

    def test_total_points_single_activity(self) -> None:
        """total_points should equal the single activity's points."""
        day = Day(
            date=date(2024, 1, 1),
            activities=[self._make_activity(15)],
        )
        self.assertEqual(day.total_points, 15)


if __name__ == "__main__":
    unittest.main()
