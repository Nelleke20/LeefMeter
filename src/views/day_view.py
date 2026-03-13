"""Day view — shows all activities for a single date."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.activity import Activity
from src.models.day import Day
from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_bar


class DayView:
    """Renders all activities for a specific calendar date.

    Displays each activity's name, category, duration, and points.
    Provides edit and delete buttons per activity and a FAB to add new ones.
    Total points are pinned at the bottom above the navigation bar.
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

    def _on_delete(
        self, activity_id: str
    ) -> Callable[[ft.ControlEvent], None]:
        """Return an async handler that deletes an activity and refreshes.

        Args:
            activity_id: UUID of the activity to delete.

        Returns:
            Async event handler for the delete IconButton.
        """

        async def handler(e: ft.ControlEvent) -> None:
            self._service.delete_activity(activity_id)
            await self._page.push_route(f"/day/{self._date.isoformat()}")

        return handler

    def _on_edit(self, activity: Activity) -> Callable[[ft.ControlEvent], None]:
        """Return an async handler that navigates to the edit form.

        Args:
            activity: The activity to edit.

        Returns:
            Async event handler for the edit IconButton.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(
                f"/edit/{self._date.isoformat()}/{activity.id}"
            )

        return handler

    def _on_add_tap(self) -> Callable[[ft.ControlEvent], None]:
        """Return an async tap handler that opens the add form for this date.

        Returns:
            Async event handler for the FAB on_click.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/add/{self._date.isoformat()}")

        return handler

    def _build_activity_tile(self, activity: Activity) -> ft.ListTile:
        """Build a list tile for a single activity with edit and delete actions.

        Args:
            activity: The activity to render.

        Returns:
            A ListTile showing activity details with edit and delete buttons.
        """
        subtitle = (
            f"{activity.category} · {activity.duration_minutes} min"
            f" · {activity.points} punten"
        )
        return ft.ListTile(
            title=ft.Text(activity.name),
            subtitle=ft.Text(subtitle),
            trailing=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        on_click=self._on_edit(activity),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=self._on_delete(activity.id),
                    ),
                ],
                tight=True,
            ),
        )

    def _build_body(self, day: Day) -> list[ft.Control]:
        """Build the scrollable activity list for the day.

        Args:
            day: The Day containing activities to render.

        Returns:
            One tile per activity, or an empty-state text control.
        """
        if not day.activities:
            return [ft.Text("Geen activiteiten op deze dag.")]
        return [self._build_activity_tile(a) for a in day.activities]

    def _build_points_footer(self, day: Day) -> ft.Container:
        """Build the pinned points total footer.

        Args:
            day: The Day whose total points to display.

        Returns:
            A Container with the total points label.
        """
        return ft.Container(
            content=ft.Text(
                f"Totaal: {day.total_points} punten",
                size=16,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            padding=12,
        )

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
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                ),
                ft.Column(
                    controls=[
                        ft.ListView(
                            controls=self._build_body(day),
                            expand=True,
                        ),
                        self._build_points_footer(day),
                    ],
                    expand=True,
                ),
            ],
            navigation_bar=build_nav_bar(
                self._page,
                selected_index=0,
                year=self._date.year,
                month=self._date.month,
            ),
            floating_action_button=ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                on_click=self._on_add_tap(),
            ),
        )
