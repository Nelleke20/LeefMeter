"""Agenda view — shows all days with recorded activities."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.day import Day
from src.services.activity_service import ActivityService


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

    def _on_day_tap(self, day_date: date) -> Callable[[ft.ControlEvent], None]:
        """Return a tap handler that navigates to the given date.

        Args:
            day_date: The date the user tapped.

        Returns:
            Event handler for ft.ListTile.on_click.
        """

        def handler(e: ft.ControlEvent) -> None:
            self._page.go(f"/day/{day_date.isoformat()}")

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
            trailing=ft.Icon(ft.icons.CHEVRON_RIGHT),
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
        today = date.today().isoformat()
        return ft.View(
            route="/",
            controls=[
                ft.AppBar(
                    title=ft.Text("LeefMeter"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                ),
                self._build_body(),
            ],
            floating_action_button=ft.FloatingActionButton(
                icon=ft.icons.ADD,
                on_click=lambda _: self._page.go(f"/add/{today}"),
            ),
        )
