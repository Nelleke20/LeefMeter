"""App-wide user settings model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppSettings:
    """Persisted user preferences for LeefMeter.

    Attributes:
        day_start_hour: First hour shown in the day time grid (0-23).
        day_end_hour: Last hour (exclusive) shown in the day time grid (1-24).
        green_threshold: Points >= this value give a green cell in month view.
        orange_threshold: Points >= this value give an orange cell in month view.
        red_threshold: Points >= this value give a red cell in month view.
    """

    day_start_hour: int = 6
    day_end_hour: int = 22
    green_threshold: int = 5
    orange_threshold: int = 10
    red_threshold: int = 20
