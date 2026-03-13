"""LeefMeter Flet application entry point."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.repositories.json_repository import JsonRepository
from src.repositories.template_repository import TemplateRepository
from src.services.activity_service import ActivityService
from src.services.export_service import ExportService
from src.services.point_strategy import IntensityPointStrategy
from src.services.template_service import TemplateService
from src.views.activity_form import ActivityForm
from src.views.agenda_view import AgendaView
from src.views.day_view import DayView
from src.views.drawer import build_drawer
from src.views.export_view import ExportView
from src.views.month_view import MonthView
from src.views.templates_view import TemplatesView

_DEFAULT_ROUTE = "/"


def _build_services() -> tuple[ActivityService, TemplateService, ExportService]:
    """Construct all application services with their dependencies.

    Returns:
        Tuple of (ActivityService, TemplateService, ExportService).
    """
    activity_repo = JsonRepository()
    template_repo = TemplateRepository()
    activity_service = ActivityService(
        repository=activity_repo,
        strategy=IntensityPointStrategy(),
    )
    template_service = TemplateService(repository=template_repo)
    export_service = ExportService(repository=activity_repo)
    return activity_service, template_service, export_service


def _resolve_view(
    route: str,
    page: ft.Page,
    activity_service: ActivityService,
    template_service: TemplateService,
    export_service: ExportService,
) -> ft.View:
    """Map a route string to the corresponding Flet View.

    Args:
        route: The current page route.
        page: The active Flet page.
        activity_service: Shared activity service.
        template_service: Shared template service.
        export_service: Shared export service.

    Returns:
        The matching View, falling back to AgendaView.
    """
    if route.startswith("/day/"):
        day_date = date.fromisoformat(route.split("/day/")[1])
        return DayView(page, activity_service, day_date).build()
    if route.startswith("/add/"):
        day_date = date.fromisoformat(route.split("/add/")[1])
        return ActivityForm(page, activity_service, day_date).build()
    if route.startswith("/edit/"):
        parts = route.split("/")
        day_date = date.fromisoformat(parts[2])
        activity_id = parts[3]
        activity = activity_service.get_activity_by_id(activity_id)
        return ActivityForm(page, activity_service, day_date, activity).build()
    if route.startswith("/month/"):
        parts = route.split("/")
        return MonthView(page, activity_service, int(parts[2]), int(parts[3])).build()
    if route == "/templates":
        return TemplatesView(page, template_service, activity_service).build()
    if route == "/export":
        return ExportView(page, export_service).build()
    return AgendaView(page, activity_service).build()


async def main(page: ft.Page) -> None:
    """Configure the Flet page, theme, drawer and routing.

    Args:
        page: The root Flet page provided by the framework.
    """
    page.title = "LeefMeter"
    page.theme = ft.Theme(color_scheme_seed="teal", use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed="teal", use_material3=True)
    page.theme_mode = ft.ThemeMode.SYSTEM

    activity_service, template_service, export_service = _build_services()
    page.drawer = build_drawer(page)

    async def on_route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        page.views.append(
            _resolve_view(
                page.route, page,
                activity_service, template_service, export_service,
            )
        )
        page.update()

    async def on_view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        top = page.views[-1]
        await page.push_route(top.route)  # type: ignore[arg-type]

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop
    page.views.clear()
    page.views.append(
        _resolve_view(
            _DEFAULT_ROUTE, page,
            activity_service, template_service, export_service,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
