"""Firebase Firestore repository implementation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

from src.models.activity import Activity
from src.repositories.base import ActivityRepository

_COLLECTION = "activities"
_DEFAULT_CREDENTIALS_PATH = "firebase_credentials.json"


class FirebaseRepository(ActivityRepository):
    """Stores activities in Firebase Firestore.

    Uses the Repository pattern. Initialises the Firebase Admin SDK
    on first instantiation. Requires a service-account credentials
    file (see README for setup instructions).
    """

    def __init__(
        self, credentials_path: str = _DEFAULT_CREDENTIALS_PATH
    ) -> None:
        """Initialise Firebase app and Firestore client.

        Args:
            credentials_path: Path to the Firebase service-account JSON file.
        """
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        self._col = firestore.client().collection(_COLLECTION)

    def save(self, activity: Activity) -> None:
        """Persist an activity to Firestore.

        Args:
            activity: The activity to save.
        """
        self._col.document(activity.id).set(self._to_dict(activity))

    def get_by_id(self, activity_id: str) -> Activity | None:
        """Fetch an activity by ID from Firestore.

        Args:
            activity_id: The UUID of the activity.

        Returns:
            The matching Activity, or None if not found.
        """
        doc = self._col.document(activity_id).get()
        if not doc.exists:
            return None
        return self._from_dict(doc.to_dict())

    def get_by_date(self, day: date) -> list[Activity]:
        """Return all activities on a given date from Firestore.

        Args:
            day: The calendar date to filter by.

        Returns:
            All activities whose date matches the given day.
        """
        docs = self._col.where("date", "==", day.isoformat()).stream()
        return [self._from_dict(d.to_dict()) for d in docs]

    def get_all(self) -> list[Activity]:
        """Return all activities from Firestore.

        Returns:
            All activities stored in the collection.
        """
        return [self._from_dict(d.to_dict()) for d in self._col.stream()]

    def update(self, activity: Activity) -> None:
        """Replace an existing Firestore document with updated data.

        Args:
            activity: Updated activity matched by id.
        """
        self._col.document(activity.id).set(self._to_dict(activity))

    def delete(self, activity_id: str) -> None:
        """Delete an activity document from Firestore.

        Args:
            activity_id: The UUID of the activity to remove.
        """
        self._col.document(activity_id).delete()

    @staticmethod
    def _to_dict(activity: Activity) -> dict[str, Any]:
        """Serialise an Activity to a Firestore-compatible dict.

        Args:
            activity: The activity to serialise.

        Returns:
            Dictionary representation suitable for Firestore storage.
        """
        return {
            "id": activity.id,
            "name": activity.name,
            "category": activity.category,
            "duration_minutes": activity.duration_minutes,
            "date": activity.date.isoformat(),
            "points": activity.points,
        }

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> Activity:
        """Deserialise a Firestore dict back into an Activity.

        Args:
            data: Raw dict from Firestore.

        Returns:
            Reconstructed Activity instance.
        """
        return Activity(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            duration_minutes=data["duration_minutes"],
            date=date.fromisoformat(data["date"]),
            points=data["points"],
        )
