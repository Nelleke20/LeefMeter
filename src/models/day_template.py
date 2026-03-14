"""Day template model for LeefMeter."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class DayTemplateEntry:
    """A single activity entry within a day template.

    Attributes:
        activity_name: Name of the activity.
        category: Intensity level.
        start_time: Start time as "HH:MM".
        duration_minutes: Duration in minutes.
    """

    activity_name: str
    category: str
    start_time: str
    duration_minutes: int


@dataclass
class DayTemplate:
    """A reusable full-day schedule that can be applied to any date.

    Attributes:
        name: Human-readable name for the template (e.g. "Werkdag").
        entries: Ordered list of activity entries for the day.
        id: Unique identifier, auto-generated if not provided.
    """

    name: str
    entries: list[DayTemplateEntry]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
