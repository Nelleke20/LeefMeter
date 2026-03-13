"""Day view — shows all activities for a single date."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.activity import Activity
from src.models.day import Day
from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_bar

_POINTS_COLORS: dict[str, str] = {
    "positive": ft.Colors.PRIMARY,
    "zero": ft.Colors.OUTLINE,
    "negative": ft.Colors.ERROR,
}


def _points_color(points: int) -> str:
    """Return a color token based on the sign of a points value.

    Args:
        points: The point value to evaluate.

    Returns:
        A Flet color string.
    """
    if points > 0:
        return _POINTS_COLORS["positive"]
    if points < 0:
        return _POINTS_COLORS["negative"]
    return _POINTS_COLORS["zero"]


class DayView:
    """Renders all activities for a specific calendar date.

    Each activity has edit and delete buttons. Total points are pinned
    at the bottom above the navigation bar.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        day_date: date,
    ) -> None:
        """Initialise with a Flet page, service, and target date.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer for activity retrieval and mutation.
            day_date: The date whose activities should be displayed.
        """
        self._page = page
        self._service = service
        self._date = day_date

    def _refresh(self) -> None:
        """Rebuild and replace the current view in-place without routing."""
        self._page.views[-1] = DayView(
            self._page, self._service, self._date
        ).build()
        self._page.update()

    def _on_delete(self, activity_id: str) -> Callable[[ft.ControlEvent], None]:
        """Return a handler that deletes an activity and refreshes the view.

        Args:
            activity_id: UUID of the activity to delete.

        Returns:
            Async event handler for the delete IconButton.
        """

        async def handler(e: ft.ControlEvent) -> None:
            self._service.delete_activity(activity_id)
            self._refresh()

        return handler

    def _on_edit(self, activity: Activity) -> Callable[[ft.ControlEvent], None]:
        """Return a handler that navigates to the edit form.

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
        """Return a handler opening the add-activity form for this date.

        Returns:
            Async event handler for the FAB.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/add/{self._date.isoformat()}")

        return handler

    def _build_activity_tile(self, activity: Activity) -> ft.Card:
        """Build a card for a single activity with edit and delete actions.

        Args:
            activity: The activity to render.

        Returns:
            A Card showing activity details with edit and delete buttons.
        """
        subtitle = (
            f"{activity.category} · {activity.duration_minutes} min"
        )
        return ft.Card(
            content=ft.ListTile(
                leading=ft.Container(
                    content=ft.Text(
                        f"{activity.points:+d}",
                        weight=ft.FontWeight.BOLD,
                        color=_points_color(activity.points),
                        size=16,
                    ),
                    width=40,
                    alignment=ft.Alignment(0, 0),
                ),
                title=ft.Text(activity.name, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(subtitle),
                trailing=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=ft.Colors.PRIMARY,
                            on_click=self._on_edit(activity),
                            tooltip="Bewerken",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.ERROR,
                            on_click=self._on_delete(activity.id),
                            tooltip="Verwijderen",
                        ),
                    ],
                    tight=True,
                    spacing=0,
                ),
            ),
            margin=ft.margin.symmetric(horizontal=8, vertical=4),
        )

    def _build_body(self, day: Day) -> list[ft.Control]:
        """Build the scrollable activity list for the day.

        Args:
            day: The Day containing activities to render.

        Returns:
            One card per activity, or an empty-state container.
        """
        if not day.activities:
            return [
                ft.Container(
                    content=ft.Text(
                        "Geen activiteiten. Tik op + om toe te voegen.",
                        color=ft.Colors.OUTLINE,
                    ),
                    padding=16,
                )
            ]
        return [self._build_activity_tile(a) for a in day.activities]

    def _build_points_footer(self, day: Day) -> ft.Container:
        """Build the pinned points total footer.

        Args:
            day: The Day whose total points to display.

        Returns:
            A styled Container with the total points label.
        """
        color = _points_color(day.total_points)
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.STAR_OUTLINED, color=color),
                    ft.Text(
                        f"Totaal vandaag: {day.total_points} punten",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=color,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            padding=ft.padding.symmetric(vertical=12, horizontal=16),
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the day.

        Returns:
            A ft.View routed to "/day/<date>".
        """
        day = self._service.get_activities_for_day(self._date)
        title = self._date.strftime("%d %B %Y")
        return ft.View(
            route=f"/day/{self._date.isoformat()}",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.MENU,
                        on_click=lambda _: self._page.show_drawer() and None,
                    ),
                    leading_width=48,
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
