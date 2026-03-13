"""Tests for point calculation strategies."""

from __future__ import annotations

import unittest
from datetime import date

from src.models.activity import Activity
from src.services.point_strategy import (
    CATEGORY_BASE_POINTS,
    CategoryPointStrategy,
    CombinedPointStrategy,
    DurationPointStrategy,
)


def _activity(category: str = "sport", duration: int = 30) -> Activity:
    """Create a test activity with given category and duration.

    Args:
        category: Activity category string.
        duration: Duration in minutes.

    Returns:
        A minimal Activity instance.
    """
    return Activity(
        name="Test",
        category=category,
        duration_minutes=duration,
        date=date(2024, 1, 1),
    )


class TestCategoryPointStrategy(unittest.TestCase):
    """Tests for CategoryPointStrategy."""

    def setUp(self) -> None:
        """Initialise strategy under test."""
        self.strategy = CategoryPointStrategy()

    def test_known_category_returns_correct_points(self) -> None:
        """Each known category should return its defined base points."""
        for category, expected in CATEGORY_BASE_POINTS.items():
            with self.subTest(category=category):
                self.assertEqual(
                    self.strategy.calculate(_activity(category=category)),
                    expected,
                )

    def test_unknown_category_returns_zero(self) -> None:
        """An unrecognised category should return zero points."""
        self.assertEqual(
            self.strategy.calculate(_activity(category="onbekend")), 0
        )


class TestDurationPointStrategy(unittest.TestCase):
    """Tests for DurationPointStrategy."""

    def setUp(self) -> None:
        """Initialise strategy under test."""
        self.strategy = DurationPointStrategy()

    def test_thirty_minutes_returns_three_points(self) -> None:
        """30 minutes should yield 3 points (3 × 10 min)."""
        self.assertEqual(self.strategy.calculate(_activity(duration=30)), 3)

    def test_less_than_ten_minutes_returns_zero(self) -> None:
        """Fewer than 10 minutes should yield zero points."""
        self.assertEqual(self.strategy.calculate(_activity(duration=9)), 0)

    def test_sixty_minutes_returns_six_points(self) -> None:
        """60 minutes should yield 6 points."""
        self.assertEqual(self.strategy.calculate(_activity(duration=60)), 6)

    def test_zero_duration_returns_zero(self) -> None:
        """Zero duration should yield zero points."""
        self.assertEqual(self.strategy.calculate(_activity(duration=0)), 0)


class TestCombinedPointStrategy(unittest.TestCase):
    """Tests for CombinedPointStrategy."""

    def setUp(self) -> None:
        """Initialise strategy under test."""
        self.strategy = CombinedPointStrategy()

    def test_combines_category_and_duration(self) -> None:
        """Points should equal category base plus duration bonus."""
        activity = _activity(category="sport", duration=30)
        expected = CATEGORY_BASE_POINTS["sport"] + 3  # 10 + 3
        self.assertEqual(self.strategy.calculate(activity), expected)

    def test_unknown_category_only_duration_points(self) -> None:
        """Unknown category adds no base points, only duration points."""
        activity = _activity(category="onbekend", duration=20)
        self.assertEqual(self.strategy.calculate(activity), 2)


if __name__ == "__main__":
    unittest.main()
