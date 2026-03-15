"""Month view — calendar grid showing all days of a month."""

from __future__ import annotations

import calendar
from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.day import Day
from src.models.settings import AppSettings
from src.services.activity_service import ActivityService
from src.services.settings_service import SettingsService
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_JANUARY: int = 1
_DECEMBER: int = 12
_WEEKDAY_LABELS: list[str] = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]

_DUTCH_MONTHS: dict[int, str] = {
    1: "Januari",
    2: "Februari",
    3: "Maart",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Augustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "December",
}

_COLOR_EMPTY: str = ft.Colors.SURFACE_CONTAINER
_COLOR_NEGATIVE: str = ft.Colors.BLUE_100
_COLOR_BLUE: str = ft.Colors.BLUE_100
_COLOR_GREEN: str = ft.Colors.LIGHT_GREEN_200
_COLOR_ORANGE: str = ft.Colors.ORANGE_200
_COLOR_RED: str = ft.Colors.RED_200


def _prev_month(year: int, month: int) -> tuple[int, int]:
    """Return the month before the given one.

    Args:
        year: Current year.
        month: Current month (1-12).

    Returns:
        Tuple (year, month) of the previous month.
    """
    return (year - 1, _DECEMBER) if month == _JANUARY else (year, month - 1)


def _next_month(year: int, month: int) -> tuple[int, int]:
    """Return the month after the given one.

    Args:
        year: Current year.
        month: Current month (1-12).

    Returns:
        Tuple (year, month) of the next month.
    """
    return (year + 1, _JANUARY) if month == _DECEMBER else (year, month + 1)


def _cell_color(points: int, settings: AppSettings) -> str:
    """Return a background color for a calendar cell based on points and thresholds.

    Args:
        points: The day's total points.
        settings: User-defined color thresholds.

    Returns:
        A Flet color string.
    """
    if points <= 0:
        return _COLOR_BLUE
    if points >= settings.red_threshold:
        return _COLOR_RED
    if points >= settings.orange_threshold:
        return _COLOR_ORANGE
    if points >= settings.green_threshold:
        return _COLOR_GREEN
    return _COLOR_BLUE


class MonthView:
    """Renders a 7-column calendar grid for a given month.

    Each cell shows the day number and total points, colored by thresholds
    defined in AppSettings. Prev/next buttons allow browsing other months.
    A gear button opens a settings dialog for threshold adjustment.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        year: int,
        month: int,
        settings_service: SettingsService,
    ) -> None:
        """Initialise with page, service, target month, and settings.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer providing month summary data.
            year: Four-digit calendar year.
            month: Calendar month (1-12).
            settings_service: Service for loading and saving user settings.
        """
        self._page = page
        self._service = service
        self._year = year
        self._month = month
        self._ss = settings_service
        self._settings = settings_service.load()

    def _on_day_tap(self, day_date: date) -> Callable[[ft.ControlEvent], None]:
        """Return a handler navigating to the given day.

        Args:
            day_date: The date to navigate to.

        Returns:
            Async event handler.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/day/{day_date.isoformat()}")

        return handler

    def _on_prev(self) -> Callable[[ft.ControlEvent], None]:
        """Return a handler navigating to the previous month.

        Returns:
            Async event handler.
        """

        async def handler(e: ft.ControlEvent) -> None:
            y, m = _prev_month(self._year, self._month)
            await self._page.push_route(f"/month/{y}/{m}")

        return handler

    def _on_next(self) -> Callable[[ft.ControlEvent], None]:
        """Return a handler navigating to the next month.

        Returns:
            Async event handler.
        """

        async def handler(e: ft.ControlEvent) -> None:
            y, m = _next_month(self._year, self._month)
            await self._page.push_route(f"/month/{y}/{m}")

        return handler

    def _open_settings(self, e: ft.ControlEvent) -> None:
        """Open a dialog for adjusting month-view color thresholds.

        Args:
            e: Click event from the settings button.
        """
        s = self._settings
        green_field = ft.TextField(
            label="Groen vanaf (punten)",
            value=str(s.green_threshold),
            border_radius=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=180,
        )
        orange_field = ft.TextField(
            label="Oranje vanaf (punten)",
            value=str(s.orange_threshold),
            border_radius=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=180,
        )
        red_field = ft.TextField(
            label="Rood vanaf (punten)",
            value=str(s.red_threshold),
            border_radius=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=180,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def on_save(ev: ft.ControlEvent) -> None:
            try:
                green = int(green_field.value or "0")
                orange = int(orange_field.value or "0")
                red = int(red_field.value or "0")
            except ValueError:
                error_text.value = "Voer geldige getallen in."
                self._page.update()
                return
            self._settings.green_threshold = green
            self._settings.orange_threshold = orange
            self._settings.red_threshold = red
            self._ss.save(self._settings)
            self._page.pop_dialog()
            self._page.run_task(
                self._page.push_route,
                f"/month/{self._year}/{self._month}",
            )

        def on_cancel(ev: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Kleur drempelwaarden"),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=16,
                                    height=16,
                                    bgcolor=_COLOR_GREEN,
                                    border_radius=4,
                                ),
                                green_field,
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=16,
                                    height=16,
                                    bgcolor=_COLOR_ORANGE,
                                    border_radius=4,
                                ),
                                orange_field,
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=16,
                                    height=16,
                                    bgcolor=_COLOR_RED,
                                    border_radius=4,
                                ),
                                red_field,
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        error_text,
                    ],
                    spacing=12,
                    tight=True,
                    width=280,
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=on_cancel),
                    ft.FilledButton("Opslaan", on_click=on_save),
                ],
            )
        )

    def _build_day_cell(self, day_num: int, day: Day | None) -> ft.Container:
        """Build a single calendar cell.

        Args:
            day_num: Day-of-month number (0 = empty cell outside month).
            day: Corresponding Day object, or None for empty cells.

        Returns:
            A styled Container cell.
        """
        if day_num == 0:
            return ft.Container(expand=1, height=52)
        points = day.total_points if day else 0
        today = date.today()
        is_today = day is not None and day.date == today
        border = ft.border.all(2, ft.Colors.PRIMARY) if is_today else None
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        str(day_num),
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        str(points),
                        size=10,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=1,
                tight=True,
            ),
            bgcolor=_cell_color(points, self._settings),
            border=border,
            border_radius=6,
            padding=ft.padding.symmetric(vertical=4, horizontal=2),
            expand=1,
            height=52,
            on_click=self._on_day_tap(date(self._year, self._month, day_num)),
        )

    def _build_week_row(self, week: list[int], days_by_num: dict[int, Day]) -> ft.Row:
        """Build a row of 7 calendar cells for one week.

        Args:
            week: List of 7 day numbers (0 = outside month).
            days_by_num: Mapping from day-of-month to Day.

        Returns:
            A Row with 7 cells.
        """
        return ft.Row(
            controls=[
                self._build_day_cell(d, days_by_num.get(d) if d else None) for d in week
            ],
            spacing=3,
        )

    def _build_calendar_grid(self, days: list[Day]) -> ft.Column:
        """Build the full calendar grid for the month.

        Args:
            days: All Day objects for the month.

        Returns:
            A Column containing the weekday header and week rows.
        """
        days_by_num = {d.date.day: d for d in days}
        header = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        label,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    expand=1,
                )
                for label in _WEEKDAY_LABELS
            ],
            spacing=3,
        )
        weeks = calendar.monthcalendar(self._year, self._month)
        rows = [self._build_week_row(week, days_by_num) for week in weeks]
        return ft.Column(controls=[header, *rows], spacing=3)

    def _build_month_header(self) -> ft.Row:
        """Build the prev/next navigation row with month title and settings button.

        Returns:
            A Row with chevron buttons, the month label, and a gear icon.
        """
        title = f"{_DUTCH_MONTHS[self._month]} {self._year}"
        return ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.MENU,
                    on_click=lambda _: open_nav_drawer(self._page),
                    icon_size=20,
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    on_click=self._on_prev(),
                ),
                ft.Text(
                    title,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    expand=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    tooltip="Kleuren instellen",
                    on_click=self._open_settings,
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    on_click=self._on_next(),
                ),
            ],
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the month.

        Returns:
            A ft.View routed to "/month/<year>/<month>".
        """
        days = self._service.get_month_summary(self._year, self._month)
        content_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self._build_month_header(),
                            ft.Container(height=4),
                            self._build_calendar_grid(days),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    expand=True,
                ),
            ],
            expand=True,
        )
        view = ft.View(
            route=f"/month/{self._year}/{self._month}",
            padding=0,
            controls=[content_column],
        )
        view.drawer = build_nav_drawer(
            self._page,
            selected_index=1,
            year=self._year,
            month=self._month,
        )
        return view
