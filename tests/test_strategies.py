"""Tests for point calculation strategies."""

from __future__ import annotations

import unittest
from datetime import date

from src.models.activity import Activity
from src.services.point_strategy import (
    INTENSITY_MULTIPLIERS,
    IntensityPointStrategy,
)


def _activity(category: str = "gemiddeld", duration: int = 30) -> Activity:
    """Create a test activity with given category and duration.

    Args:
        category: Intensity level string.
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


class TestIntensityPointStrategy(unittest.TestCase):
    """Tests for IntensityPointStrategy."""

    def setUp(self) -> None:
        """Initialise strategy under test."""
        self.strategy = IntensityPointStrategy()

    def test_rust_30_min_returns_minus_one(self) -> None:
        """30 min of rust should yield -1 point."""
        self.assertEqual(self.strategy.calculate(_activity("rust", 30)), -1)

    def test_laag_30_min_returns_one(self) -> None:
        """30 min of laag should yield +1 point."""
        self.assertEqual(self.strategy.calculate(_activity("laag", 30)), 1)

    def test_gemiddeld_30_min_returns_two(self) -> None:
        """30 min of gemiddeld should yield +2 points."""
        self.assertEqual(self.strategy.calculate(_activity("gemiddeld", 30)), 2)

    def test_zwaar_30_min_returns_three(self) -> None:
        """30 min of zwaar should yield +3 points."""
        self.assertEqual(self.strategy.calculate(_activity("zwaar", 30)), 3)

    def test_zwaar_60_min_returns_six(self) -> None:
        """60 min of zwaar should yield +6 points (2 × 30 min × 3)."""
        self.assertEqual(self.strategy.calculate(_activity("zwaar", 60)), 6)

    def test_rust_60_min_returns_minus_two(self) -> None:
        """60 min of rust should yield -2 points."""
        self.assertEqual(self.strategy.calculate(_activity("rust", 60)), -2)

    def test_gemiddeld_45_min_returns_three(self) -> None:
        """45 min of gemiddeld should yield +3 points (1.5 × 2 = 3.0)."""
        self.assertEqual(self.strategy.calculate(_activity("gemiddeld", 45)), 3)

    def test_unknown_category_returns_zero(self) -> None:
        """An unrecognised category should return zero points."""
        self.assertEqual(self.strategy.calculate(_activity("onbekend", 30)), 0)

    def test_all_known_categories_are_in_multipliers(self) -> None:
        """Every category in INTENSITY_MULTIPLIERS should produce a non-zero score."""
        for category in INTENSITY_MULTIPLIERS:
            with self.subTest(category=category):
                result = self.strategy.calculate(_activity(category, 30))
                self.assertNotEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
