"""Excel export service for LeefMeter activity data."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from src.repositories.base import ActivityRepository

_HEADER_FILL = PatternFill(start_color="1A7F6F", end_color="1A7F6F", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_COLUMNS: list[str] = ["Datum", "Naam", "Intensiteit", "Duur (min)", "Punten"]
_DEFAULT_EXPORT_PATH: Path = Path.home() / "Downloads" / "leefmeter_export.xlsx"


class ExportService:
    """Creates Excel exports of activity data.

    Exports can be filtered by date range or include all activities.
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

        Args:
            output_path: Where to save the Excel file.
            from_date: Include activities on or after this date.
            to_date: Include activities on or before this date.

        Returns:
            Path to the saved Excel file.
        """
        activities = sorted(self._repository.get_all(), key=lambda a: a.date)
        if from_date:
            activities = [a for a in activities if a.date >= from_date]
        if to_date:
            activities = [a for a in activities if a.date <= to_date]
        wb = Workbook()
        ws = wb.active
        ws.title = "Activiteiten"  # type: ignore[union-attr]
        self._write_headers(ws)  # type: ignore[arg-type]
        for row_idx, activity in enumerate(activities, start=2):
            ws.cell(row=row_idx, column=1, value=str(activity.date))  # type: ignore[union-attr]
            ws.cell(row=row_idx, column=2, value=activity.name)  # type: ignore[union-attr]
            ws.cell(row=row_idx, column=3, value=activity.category)  # type: ignore[union-attr]
            ws.cell(row=row_idx, column=4, value=activity.duration_minutes)  # type: ignore[union-attr]
            ws.cell(row=row_idx, column=5, value=activity.points)  # type: ignore[union-attr]
        self._auto_width(ws)  # type: ignore[arg-type]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        return output_path

    @staticmethod
    def _write_headers(ws: object) -> None:
        """Write and style the header row.

        Args:
            ws: The openpyxl worksheet to write headers to.
        """
        for col_idx, label in enumerate(_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=label)  # type: ignore[union-attr]
            cell.font = _HEADER_FONT
            cell.fill = _HEADER_FILL
            cell.alignment = Alignment(horizontal="center")

    @staticmethod
    def _auto_width(ws: object) -> None:
        """Set column widths based on content.

        Args:
            ws: The openpyxl worksheet to adjust.
        """
        for col in ws.columns:  # type: ignore[union-attr]
            max_len = max((len(str(cell.value or "")) for cell in col), default=8)
            ws.column_dimensions[col[0].column_letter].width = max_len + 4  # type: ignore[union-attr]
