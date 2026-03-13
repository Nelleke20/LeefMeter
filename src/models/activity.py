"""Activity model for LeefMeter."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

VALID_CATEGORIES: frozenset[str] = frozenset(
    {"sport", "voeding", "mentaal", "sociaal", "rust"}
)


@dataclass
class Activity:
    """Represents a single tracked activity.

    Attributes:
        name: Human-readable name of the activity.
        category: One of the predefined VALID_CATEGORIES.
        duration_minutes: How long the activity lasted.
        date: The calendar date on which the activity took place.
        id: Unique identifier, auto-generated if not provided.
        points: Score assigned by the point calculation strategy.
    """

    name: str
    category: str
    duration_minutes: int
    date: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    points: int = 0
