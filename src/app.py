"""LeefMeter Flet application entry point."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.repositories.in_memory_repository import InMemoryRepository
from src.services.activity_service import ActivityService
from src.services.point_strategy import CombinedPointStrategy
from src.views.activity_form import ActivityForm
from src.views.agenda_view import AgendaView
from src.views.day_view import DayView

_DEFAULT_ROUTE = "/"


def _build_service() -> ActivityService:
    """Construct the ActivityService with default dependencies.

    Returns:
        ActivityService backed by InMemoryRepository and CombinedPointStrategy.

    Note:
        Swap InMemoryRepository for FirebaseRepository in production.
    """
    return ActivityService(
        repository=InMemoryRepository(),
        strategy=CombinedPointStrategy(),
    )


def _resolve_view(
    route: str,
    page: ft.Page,
    service: ActivityService,
) -> ft.View:
    """Map a route string to the corresponding Flet View.

    Args:
        route: The current page route (e.g. "/day/2024-01-15").
        page: The active Flet page.
        service: Shared ActivityService instance.

    Returns:
        The View matching the route, falling back to AgendaView.
    """
    if route.startswith("/day/"):
        day_date = date.fromisoformat(route.split("/day/")[1])
        return DayView(page, service, day_date).build()
    if route.startswith("/add/"):
        day_date = date.fromisoformat(route.split("/add/")[1])
        return ActivityForm(page, service, day_date).build()
    return AgendaView(page, service).build()


def main(page: ft.Page) -> None:
    """Configure the Flet page and wire up routing.

    Args:
        page: The root Flet page provided by the framework.
    """
    page.title = "LeefMeter"
    service = _build_service()

    def on_route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        page.views.append(_resolve_view(page.route, page, service))
        page.update()

    def on_view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        top = page.views[-1]
        page.go(top.route)  # type: ignore[arg-type]

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop
    page.go(_DEFAULT_ROUTE)


if __name__ == "__main__":
    ft.app(target=main)
