"""Month view — shows all calendar days of a month with their points."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.day import Day
from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_bar

_JANUARY: int = 1
_DECEMBER: int = 12

_DUTCH_MONTHS: dict[int, str] = {
    1: "Januari", 2: "Februari", 3: "Maart", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Augustus",
    9: "September", 10: "Oktober", 11: "November", 12: "December",
}


def _prev_month(year: int, month: int) -> tuple[int, int]:
    """Return the year and month preceding the given month.

    Args:
        year: Current year.
        month: Current month (1-12).

    Returns:
        Tuple of (year, month) for the previous month.
    """
    if month == _JANUARY:
        return year - 1, _DECEMBER
    return year, month - 1


def _next_month(year: int, month: int) -> tuple[int, int]:
    """Return the year and month following the given month.

    Args:
        year: Current year.
        month: Current month (1-12).

    Returns:
        Tuple of (year, month) for the next month.
    """
    if month == _DECEMBER:
        return year + 1, _JANUARY
    return year, month + 1


class MonthView:
    """Renders all calendar days of a month in a scrollable list.

    Each day shows its date and total points. Tapping a day navigates
    to DayView. Prev/next buttons allow browsing other months.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        year: int,
        month: int,
    ) -> None:
        """Initialise with a Flet page, service, and target month.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer providing month summary data.
            year: Four-digit calendar year to display.
            month: Calendar month to display (1-12).
        """
        self._page = page
        self._service = service
        self._year = year
        self._month = month

    def _on_day_tap(self, day_date: date) -> Callable[[ft.ControlEvent], None]:
        """Return an async tap handler navigating to the given day.

        Args:
            day_date: The date to navigate to.

        Returns:
            Async event handler for ft.ListTile.on_click.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/day/{day_date.isoformat()}")

        return handler

    def _on_prev(self) -> Callable[[ft.ControlEvent], None]:
        """Return an async handler navigating to the previous month.

        Returns:
            Async event handler for the prev IconButton.
        """

        async def handler(e: ft.ControlEvent) -> None:
            y, m = _prev_month(self._year, self._month)
            await self._page.push_route(f"/month/{y}/{m}")

        return handler

    def _on_next(self) -> Callable[[ft.ControlEvent], None]:
        """Return an async handler navigating to the next month.

        Returns:
            Async event handler for the next IconButton.
        """

        async def handler(e: ft.ControlEvent) -> None:
            y, m = _next_month(self._year, self._month)
            await self._page.push_route(f"/month/{y}/{m}")

        return handler

    def _build_day_tile(self, day: Day) -> ft.ListTile:
        """Build a list tile for a single calendar day.

        Args:
            day: The Day to render.

        Returns:
            A ListTile showing the date, activity count, and points.
        """
        weekday = day.date.strftime("%a")
        subtitle = (
            f"{len(day.activities)} activiteiten"
            if day.activities
            else "Geen activiteiten"
        )
        return ft.ListTile(
            leading=ft.Text(
                str(day.date.day),
                size=20,
                weight=ft.FontWeight.BOLD,
            ),
            title=ft.Text(f"{weekday} {day.date.day} {_DUTCH_MONTHS[self._month][:3]}"),
            subtitle=ft.Text(subtitle),
            trailing=ft.Text(
                f"{day.total_points} pnt",
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.PRIMARY if day.total_points > 0 else ft.Colors.OUTLINE,
            ),
            on_click=self._on_day_tap(day.date),
        )

    def _build_month_header(self) -> ft.Row:
        """Build the prev/next navigation row with the month title.

        Returns:
            A Row with chevron buttons and a centred month label.
        """
        title = f"{_DUTCH_MONTHS[self._month]} {self._year}"
        return ft.Row(
            controls=[
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
        return ft.View(
            route=f"/month/{self._year}/{self._month}",
            controls=[
                ft.AppBar(
                    title=ft.Text("LeefMeter"),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                ),
                ft.Column(
                    controls=[
                        self._build_month_header(),
                        ft.ListView(
                            controls=[self._build_day_tile(d) for d in days],
                            expand=True,
                        ),
                    ],
                    expand=True,
                ),
            ],
            navigation_bar=build_nav_bar(
                self._page,
                selected_index=1,
                year=self._year,
                month=self._month,
            ),
        )
