"""Excel export service for LeefMeter activity data."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from src.models.activity import Activity
from src.repositories.base import ActivityRepository

_HEADER_FILL = PatternFill(start_color="1A7F6F", end_color="1A7F6F", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_TOTAL_FONT = Font(bold=True)
_DAY_COLUMNS: list[str] = ["Tijd", "Naam", "Intensiteit", "Duur (min)", "Punten"]
_DEFAULT_EXPORT_PATH: Path = Path.home() / "Downloads" / "leefmeter_export.xlsx"


def _set_col_widths(ws: Worksheet) -> None:
    """Adjust column widths of a worksheet to fit content.

    Args:
        ws: The openpyxl worksheet to adjust.
    """
    for col_idx, col in enumerate(ws.columns, start=1):
        max_len = max((len(str(c.value or "")) for c in col), default=8)
        ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 4


class ExportService:
    """Creates Excel exports of activity data.

    One worksheet is created per day, with a bold total row at the bottom.
    A separate "Categorieën" worksheet lists unique activity names per category.
    """

    def __init__(self, repository: ActivityRepository) -> None:
        """Initialise with an activity repository.

        Args:
            repository: Source of activity data to export.
        """
        self._repository = repository

    def export(
        self,
        output_path: Path = _DEFAULT_EXPORT_PATH,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> Path:
        """Export activities to an Excel file.

        Each day gets its own worksheet. A "Categorieën" sheet lists unique
        activity names grouped by category.

        Args:
            output_path: Where to save the Excel file.
            from_date: Include activities on or after this date.
            to_date: Include activities on or before this date.

        Returns:
            Path to the saved Excel file.
        """
        activities = sorted(
            self._repository.get_all(), key=lambda a: (a.date, a.start_time or "")
        )
        if from_date:
            activities = [a for a in activities if a.date >= from_date]
        if to_date:
            activities = [a for a in activities if a.date <= to_date]

        wb = Workbook()
        ws: Worksheet = wb.active  # type: ignore[assignment]
        ws.title = "Activiteiten"

        # Group activities by date
        by_day: dict[date, list[Activity]] = defaultdict(list)
        for act in activities:
            by_day[act.date].append(act)

        current_row = 1
        for day_date in sorted(by_day.keys()):
            day_activities = by_day[day_date]

            # Date header
            date_cell = ws.cell(
                row=current_row, column=1, value=day_date.strftime("%d-%m-%Y")
            )
            date_cell.font = Font(bold=True, size=12)
            current_row += 1

            # Column headers
            self._write_day_headers(ws, current_row)
            current_row += 1

            # Activity rows
            for act in day_activities:
                ws.cell(row=current_row, column=1, value=act.start_time or "")
                ws.cell(row=current_row, column=2, value=act.name)
                ws.cell(row=current_row, column=3, value=act.category)
                ws.cell(row=current_row, column=4, value=act.duration_minutes)
                ws.cell(row=current_row, column=5, value=act.points)
                current_row += 1

            # Total row
            total_points = sum(a.points for a in day_activities)
            total_cell = ws.cell(row=current_row, column=2, value="Totaal")
            total_cell.font = _TOTAL_FONT
            pts_cell = ws.cell(row=current_row, column=5, value=total_points)
            pts_cell.font = _TOTAL_FONT
            current_row += 2  # blank separator row

        _set_col_widths(ws)

        # Categories sheet
        cat_ws = wb.create_sheet(title="Categorieën")
        self._write_categories_sheet(cat_ws, activities)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        return output_path

    @staticmethod
    def _write_day_headers(ws: Worksheet, start_row: int = 1) -> None:
        """Write and style the header row for a day section.

        Args:
            ws: The openpyxl worksheet to write headers to.
            start_row: Row index to write the header into.
        """
        for col_idx, label in enumerate(_DAY_COLUMNS, start=1):
            cell = ws.cell(row=start_row, column=col_idx, value=label)
            cell.font = _HEADER_FONT
            cell.fill = _HEADER_FILL
            cell.alignment = Alignment(horizontal="center")

    @staticmethod
    def _write_categories_sheet(ws: Worksheet, activities: list[Activity]) -> None:
        """Write a categories overview sheet with unique activity names per category.

        Args:
            ws: The openpyxl worksheet to write to.
            activities: All exported activities.
        """
        # Header row
        for col_idx, label in enumerate(["Categorie", "Activiteit"], start=1):
            cell = ws.cell(row=1, column=col_idx, value=label)
            cell.font = _HEADER_FONT
            cell.fill = _HEADER_FILL
            cell.alignment = Alignment(horizontal="center")

        # Collect unique (category, name) pairs, preserving category order
        seen: set[tuple[str, str]] = set()
        pairs: list[tuple[str, str]] = []
        for act in activities:
            key = (act.category, act.name)
            if key not in seen:
                seen.add(key)
                pairs.append(key)
        pairs.sort(key=lambda p: (p[0], p[1]))

        for row_idx, (category, name) in enumerate(pairs, start=2):
            ws.cell(row=row_idx, column=1, value=category)
            ws.cell(row=row_idx, column=2, value=name)

        _set_col_widths(ws)
