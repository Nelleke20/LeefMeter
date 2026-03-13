"""Day view — shows all activities for a single date."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.activity import Activity
from src.models.day import Day
from src.services.activity_service import ActivityService


class DayView:
    """Renders all activities for a specific calendar date.

    Displays each activity's name, category, duration, and points.
    Provides delete buttons per activity and a FAB to add new ones.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        day_date: date,
    ) -> None:
        """Initialise with a Flet page, service, and the target date.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer for activity retrieval and deletion.
            day_date: The date whose activities should be displayed.
        """
        self._page = page
        self._service = service
        self._date = day_date

    def _on_delete(self, activity_id: str) -> Callable[[ft.ControlEvent], None]:
        """Return a handler that deletes an activity and refreshes the view.

        Args:
            activity_id: UUID of the activity to delete.

        Returns:
            Event handler for the delete IconButton.
        """

        def handler(e: ft.ControlEvent) -> None:
            self._service.delete_activity(activity_id)
            self._page.go(f"/day/{self._date.isoformat()}")

        return handler

    def _build_activity_tile(self, activity: Activity) -> ft.ListTile:
        """Build a list tile for a single activity.

        Args:
            activity: The activity to render.

        Returns:
            A ListTile showing activity details and a delete button.
        """
        subtitle = (
            f"{activity.category} · {activity.duration_minutes} min"
            f" · {activity.points} punten"
        )
        return ft.ListTile(
            title=ft.Text(activity.name),
            subtitle=ft.Text(subtitle),
            trailing=ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE,
                on_click=self._on_delete(activity.id),
            ),
        )

    def _build_body(self, day: Day) -> list[ft.Control]:
        """Build the list of controls for the day's content area.

        Args:
            day: The Day containing activities to render.

        Returns:
            A list of controls — header plus one tile per activity.
        """
        header = ft.Text(
            f"Totaal: {day.total_points} punten",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        if not day.activities:
            return [header, ft.Text("Geen activiteiten op deze dag.")]
        tiles = [self._build_activity_tile(a) for a in day.activities]
        return [header, *tiles]

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the day.

        Returns:
            A ft.View routed to "/day/<date>".
        """
        day = self._service.get_activities_for_day(self._date)
        title = self._date.strftime("%A, %d %B %Y")
        return ft.View(
            route=f"/day/{self._date.isoformat()}",
            controls=[
                ft.AppBar(
                    title=ft.Text(title),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                ),
                ft.ListView(controls=self._build_body(day), expand=True),
            ],
            floating_action_button=ft.FloatingActionButton(
                icon=ft.icons.ADD,
                on_click=lambda _: self._page.go(
                    f"/add/{self._date.isoformat()}"
                ),
            ),
        )
