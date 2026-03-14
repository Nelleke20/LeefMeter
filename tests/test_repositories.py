"""Tests for InMemoryRepository."""

from __future__ import annotations

import unittest
from datetime import date

from src.models.activity import Activity
from src.repositories.in_memory_repository import InMemoryRepository


def _activity(
    name: str = "Hardlopen",
    activity_date: date | None = None,
) -> Activity:
    """Create a minimal test Activity.

    Args:
        name: Activity name to distinguish instances in tests.
        activity_date: The date for the activity. Defaults to 2024-01-15.

    Returns:
        A new Activity instance.
    """
    return Activity(
        name=name,
        category="sport",
        duration_minutes=30,
        date=activity_date or date(2024, 1, 15),
    )


class TestInMemoryRepository(unittest.TestCase):
    """Tests for InMemoryRepository covering all CRUD operations."""

    def setUp(self) -> None:
        """Create a fresh repository for each test."""
        self.repo = InMemoryRepository()

    def test_save_and_get_by_id(self) -> None:
        """A saved activity should be retrievable by its ID."""
        activity = _activity()
        self.repo.save(activity)
        result = self.repo.get_by_id(activity.id)
        self.assertEqual(result, activity)

    def test_get_by_id_returns_none_for_missing(self) -> None:
        """get_by_id should return None for an unknown ID."""
        self.assertIsNone(self.repo.get_by_id("does-not-exist"))

    def test_get_by_date_returns_matching_activities(self) -> None:
        """Only activities on the requested date should be returned."""
        day_a = date(2024, 1, 15)
        day_b = date(2024, 1, 16)
        act_a = _activity("A", day_a)
        act_b = _activity("B", day_b)
        self.repo.save(act_a)
        self.repo.save(act_b)
        result = self.repo.get_by_date(day_a)
        self.assertEqual(result, [act_a])

    def test_get_by_date_returns_empty_for_unknown_date(self) -> None:
        """get_by_date should return an empty list for a date with no activities."""
        result = self.repo.get_by_date(date(2099, 1, 1))
        self.assertEqual(result, [])

    def test_get_all_returns_all_activities(self) -> None:
        """get_all should return every saved activity."""
        a1 = _activity("A")
        a2 = _activity("B")
        self.repo.save(a1)
        self.repo.save(a2)
        self.assertCountEqual(self.repo.get_all(), [a1, a2])

    def test_get_all_empty_repository(self) -> None:
        """get_all on an empty repository should return an empty list."""
        self.assertEqual(self.repo.get_all(), [])

    def test_update_replaces_existing_activity(self) -> None:
        """update should overwrite the stored activity with new data."""
        activity = _activity()
        self.repo.save(activity)
        activity.points = 99
        self.repo.update(activity)
        updated = self.repo.get_by_id(activity.id)
        self.assertEqual(updated.points, 99)  # type: ignore[union-attr]

    def test_delete_removes_activity(self) -> None:
        """delete should make the activity unretrievable."""
        activity = _activity()
        self.repo.save(activity)
        self.repo.delete(activity.id)
        self.assertIsNone(self.repo.get_by_id(activity.id))

    def test_delete_nonexistent_id_does_not_raise(self) -> None:
        """Deleting a non-existent ID should not raise an exception."""
        self.repo.delete("ghost-id")


if __name__ == "__main__":
    unittest.main()
