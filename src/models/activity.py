"""Activity model for LeefMeter."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date  # noqa: F401 — used in dataclass field annotation

INTENSITY_LEVELS: tuple[str, ...] = ("rust", "laag", "gemiddeld", "zwaar")


@dataclass
class Activity:
    """Represents a single tracked activity.

    Attributes:
        name: Human-readable name of the activity.
        category: Intensity level — one of INTENSITY_LEVELS.
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
    start_time: str | None = None  # "HH:MM", e.g. "08:30"
