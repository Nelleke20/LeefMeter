"""Template model for LeefMeter."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Template:
    """A reusable activity template that can be applied to any day.

    Attributes:
        name: Human-readable name of the template.
        category: Intensity level — one of INTENSITY_LEVELS.
        duration_minutes: Default duration for this activity.
        id: Unique identifier, auto-generated if not provided.
    """

    name: str
    category: str
    duration_minutes: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
