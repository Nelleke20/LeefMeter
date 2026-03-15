"""Excel export service for LeefMeter activity data.

Uses the Repository pattern to access activity data and writes two sheets:
- "Weekschema": a time-grid view with one column per day and 30-min slots.
- "Per categorie": activities grouped and sorted by category.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Sequence

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from src.models.activity import Activity
from src.repositories.base import ActivityRepository
from src.storage import get_data_dir

_HEADER_FILL = PatternFill(start_color="1A7F6F", end_color="1A7F6F", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_TOTAL_FONT = Font(bold=True)


def get_export_path() -> Path:
    """Return the platform-appropriate path for the Excel export file.

    On Android/iOS uses the app's private writable storage.
    On desktop saves to ~/Downloads.

    Returns:
        Path to leefmeter_export.xlsx.
    """
    import os

    if os.environ.get("FLET_APP_STORAGE_DATA"):
        return get_data_dir() / "leefmeter_export.xlsx"
    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    return downloads / "leefmeter_export.xlsx"


_CAT_FILL = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
_CAT_FONT = Font(bold=True, color="000000")
# Resolved at call time to support Android; see get_export_path()

_DUTCH_WEEKDAYS: tuple[str, ...] = ("ma", "di", "wo", "do", "vr", "za", "zo")

# Time-grid constants
_SLOT_START_HOUR: int = 6  # 06:00
_SLOT_END_HOUR: int = 22  # up to and including 22:00
_SLOT_MINUTES: int = 30


def _slot_label(slot_index: int) -> str:
    """Return the time string for a 30-min slot index starting at 06:00.

    Args:
        slot_index: Zero-based slot index (0 → "06:00", 1 → "06:30", …).

    Returns:
        Time string formatted as "HH:MM".
    """
    total_minutes = _SLOT_START_HOUR * 60 + slot_index * _SLOT_MINUTES
    h, m = divmod(total_minutes, 60)
    return f"{h:02d}:{m:02d}"


def _all_slots() -> list[str]:
    """Return all 30-min time slot labels from 06:00 to 22:00 inclusive.

    Returns:
        List of "HH:MM" strings, e.g. ["06:00", "06:30", …, "22:00"].
    """
    slots: list[str] = []
    idx = 0
    while True:
        label = _slot_label(idx)
        slots.append(label)
        h, m = (int(p) for p in label.split(":"))
        if h == _SLOT_END_HOUR and m == 0:
            break
        idx += 1
    return slots


def _day_column_header(d: date) -> str:
    """Format a date as a Dutch weekday-abbreviated column header.

    Args:
        d: The date to format.

    Returns:
        String like "ma 15-03".
    """
    weekday_abbr = _DUTCH_WEEKDAYS[d.weekday()]
    return f"{weekday_abbr} {d.strftime('%d-%m')}"


def _slots_for_activity(activity: Activity) -> list[str]:
    """Return all 30-min slot labels occupied by an activity.

    The activity occupies the slot at start_time and every subsequent
    30-min slot until start_time + duration_minutes (exclusive of end
    slot unless it aligns exactly).

    Args:
        activity: The activity to calculate slots for.

    Returns:
        List of "HH:MM" slot labels the activity occupies, or empty list
        if start_time is not set.
    """
    if not activity.start_time:
        return []
    try:
        start_dt = datetime.strptime(activity.start_time, "%H:%M")
    except ValueError:
        return []
    occupied: list[str] = []
    current = start_dt
    end_dt = start_dt + timedelta(minutes=activity.duration_minutes)
    while current < end_dt:
        label = current.strftime("%H:%M")
        occupied.append(label)
        current += timedelta(minutes=_SLOT_MINUTES)
    return occupied


class ExportService:
    """Creates Excel exports of LeefMeter activity data.

    Produces two worksheets:
    - "Weekschema": time-grid with days as columns and 30-min rows.
    - "Per categorie": activity details grouped alphabetically by category.
    """

    def __init__(self, repository: ActivityRepository) -> None:
        """Initialise with an activity repository.

        Args:
            repository: Source of activity data to export.
        """
        self._repository = repository

    def export(
        self,
        output_path: Path | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> Path:
        """Export activities to an Excel file with two sheets.

        Sheet 1 "Weekschema": time-grid with one column per day.
        Sheet 2 "Per categorie": activities grouped by category.

        Args:
            output_path: Where to save the Excel file. Defaults to a
                platform-appropriate path (app storage on Android, ~/Downloads
                on desktop).
            from_date: Include activities on or after this date.
            to_date: Include activities on or before this date.

        Returns:
            Path to the saved Excel file.
        """
        resolved_path = output_path if output_path is not None else get_export_path()
        activities = sorted(
            self._repository.get_all(), key=lambda a: (a.date, a.start_time or "")
        )
        if from_date:
            activities = [a for a in activities if a.date >= from_date]
        if to_date:
            activities = [a for a in activities if a.date <= to_date]

        wb = Workbook()
        week_ws: Worksheet = wb.active  # type: ignore[assignment]
        week_ws.title = "Weekschema"
        self._write_weekschema_sheet(week_ws, activities)

        cat_ws: Worksheet = wb.create_sheet(title="Per categorie")
        self._write_per_categorie_sheet(cat_ws, activities)

        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(resolved_path)
        return resolved_path

    @staticmethod
    def _write_weekschema_sheet(ws: Worksheet, activities: Sequence[Activity]) -> None:
        """Write the Weekschema sheet to the given worksheet.

        Row 1 has "Tijd" in column A and one column per unique date.
        Rows 2..N have one 30-min slot per row from 06:00 to 22:00.
        The final row shows totals per day.

        Args:
            ws: The openpyxl worksheet to write to.
            activities: Activities to render, pre-sorted by date.
        """
        sorted_dates = sorted({a.date for a in activities})

        # --- Header row (row 1) ---
        tijd_cell = ws.cell(row=1, column=1, value="Tijd")
        tijd_cell.font = _HEADER_FONT
        tijd_cell.fill = _HEADER_FILL
        tijd_cell.alignment = Alignment(horizontal="center")

        for col_idx, d in enumerate(sorted_dates, start=2):
            cell = ws.cell(row=1, column=col_idx, value=_day_column_header(d))
            cell.font = _HEADER_FONT
            cell.fill = _HEADER_FILL
            cell.alignment = Alignment(horizontal="center")

        # Build lookup: (date, slot_label) → activity name
        slot_map: dict[tuple[date, str], str] = {}
        for act in activities:
            for slot in _slots_for_activity(act):
                key = (act.date, slot)
                if key not in slot_map:
                    slot_map[key] = act.name

        # --- Slot rows ---
        slots = _all_slots()
        for row_offset, slot_label in enumerate(slots, start=2):
            ws.cell(row=row_offset, column=1, value=slot_label).alignment = Alignment(
                horizontal="center"
            )
            for col_idx, d in enumerate(sorted_dates, start=2):
                value = slot_map.get((d, slot_label), "")
                if value:
                    ws.cell(row=row_offset, column=col_idx, value=value)

        # --- Totals row ---
        total_row = len(slots) + 2
        totals_label = ws.cell(row=total_row, column=1, value="Totaal")
        totals_label.font = _TOTAL_FONT

        points_by_date: dict[date, int] = defaultdict(int)
        for act in activities:
            points_by_date[act.date] += act.points

        for col_idx, d in enumerate(sorted_dates, start=2):
            cell = ws.cell(row=total_row, column=col_idx, value=points_by_date[d])
            cell.font = _TOTAL_FONT
            cell.alignment = Alignment(horizontal="center")

        # --- Column widths ---
        ws.column_dimensions["A"].width = 8
        for col_idx in range(2, len(sorted_dates) + 2):
            ws.column_dimensions[get_column_letter(col_idx)].width = 18

    @staticmethod
    def _write_per_categorie_sheet(
        ws: Worksheet, activities: Sequence[Activity]
    ) -> None:
        """Write the Per-categorie sheet with one section per category.

        Each section has a category header row, a column header row,
        activity detail rows sorted by date then start_time, and a blank
        separator row.

        Args:
            ws: The openpyxl worksheet to write to.
            activities: Activities to render.
        """
        col_headers = ["Datum", "Tijd", "Activiteit", "Duur (min)", "Punten"]

        by_category: dict[str, list[Activity]] = defaultdict(list)
        for act in activities:
            by_category[act.category].append(act)

        current_row = 1
        for category in sorted(by_category.keys()):
            cat_activities = sorted(
                by_category[category], key=lambda a: (a.date, a.start_time or "")
            )

            # Category header row (spans cols A-E)
            cat_cell = ws.cell(
                row=current_row, column=1, value=f"Categorie: {category}"
            )
            cat_cell.font = _CAT_FONT
            cat_cell.fill = _CAT_FILL
            ws.merge_cells(
                start_row=current_row,
                start_column=1,
                end_row=current_row,
                end_column=len(col_headers),
            )
            current_row += 1

            # Column header row
            for col_idx, label in enumerate(col_headers, start=1):
                cell = ws.cell(row=current_row, column=col_idx, value=label)
                cell.font = _HEADER_FONT
                cell.fill = _HEADER_FILL
                cell.alignment = Alignment(horizontal="center")
            current_row += 1

            # Activity rows
            for act in cat_activities:
                ws.cell(
                    row=current_row,
                    column=1,
                    value=act.date.strftime("%d-%m-%Y"),
                )
                ws.cell(row=current_row, column=2, value=act.start_time or "")
                ws.cell(row=current_row, column=3, value=act.name)
                ws.cell(row=current_row, column=4, value=act.duration_minutes)
                ws.cell(row=current_row, column=5, value=act.points)
                current_row += 1

            # Blank separator row
            current_row += 1

        # Column widths
        col_widths = [12, 8, 28, 12, 10]
        for col_idx, width in enumerate(col_widths, start=1):
            ws.column_dimensions[get_column_letter(col_idx)].width = width
