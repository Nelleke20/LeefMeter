"""Agenda view — shows all days with recorded activities."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.day import Day
from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_bar


class AgendaView:
    """Renders a scrollable list of days with their total points.

    Each row navigates to DayView on tap. A FAB opens ActivityForm
    for today's date.
    """

    def __init__(self, page: ft.Page, service: ActivityService) -> None:
        """Initialise with a Flet page and the activity service.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer providing aggregated day data.
        """
        self._page = page
        self._service = service

    def _on_day_tap(
        self, day_date: date
    ) -> Callable[[ft.ControlEvent], None]:
        """Return an async tap handler that navigates to the given date.

        Args:
            day_date: The date the user tapped.

        Returns:
            Async event handler for ft.ListTile.on_click.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/day/{day_date.isoformat()}")

        return handler

    def _on_add_tap(self, today: str) -> Callable[[ft.ControlEvent], None]:
        """Return an async tap handler that navigates to the add form.

        Args:
            today: ISO date string for today.

        Returns:
            Async event handler for the FAB on_click.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/add/{today}")

        return handler

    def _build_day_tile(self, day: Day) -> ft.ListTile:
        """Build a single list tile for a day summary.

        Args:
            day: The Day to render.

        Returns:
            A ListTile showing date, activity count, and total points.
        """
        label = day.date.strftime("%A, %d %B %Y")
        subtitle = (
            f"{len(day.activities)} activiteiten · {day.total_points} punten"
        )
        return ft.ListTile(
            title=ft.Text(label),
            subtitle=ft.Text(subtitle),
            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
            on_click=self._on_day_tap(day.date),
        )

    def _build_body(self) -> ft.Control:
        """Build the scrollable list or an empty-state message.

        Returns:
            A ListView with day tiles, or a placeholder Text.
        """
        days = self._service.get_all_days()
        if not days:
            return ft.Text("Nog geen activiteiten. Voeg er een toe!")
        return ft.ListView(
            controls=[self._build_day_tile(d) for d in days],
            expand=True,
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the agenda.

        Returns:
            A ft.View routed to "/".
        """
        today = date.today()
        return ft.View(
            route="/",
            controls=[
                ft.AppBar(
                    title=ft.Text("LeefMeter"),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                ),
                self._build_body(),
            ],
            navigation_bar=build_nav_bar(
                self._page,
                selected_index=0,
                year=today.year,
                month=today.month,
            ),
            floating_action_button=ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                on_click=self._on_add_tap(today.isoformat()),
            ),
        )
