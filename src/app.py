"""LeefMeter Flet application entry point."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.repositories.day_template_repository import DayTemplateRepository
from src.repositories.json_repository import JsonRepository
from src.repositories.template_repository import TemplateRepository
from src.services.activity_service import ActivityService
from src.services.day_template_service import DayTemplateService
from src.services.export_service import ExportService
from src.services.point_strategy import IntensityPointStrategy
from src.services.settings_service import SettingsService
from src.services.template_service import TemplateService
from src.views.chart_view import ChartView
from src.views.feedback_view import FeedbackView
from src.views.manage_activities_view import ManageActivitiesView
from src.views.day_template_edit_view import DayTemplateEditView
from src.views.day_templates_view import DayTemplatesView
from src.views.day_view import DayView
from src.views.export_view import ExportView
from src.views.home_view import HomeView
from src.views.month_view import MonthView


def _build_services() -> tuple[
    ActivityService,
    TemplateService,
    DayTemplateService,
    ExportService,
    SettingsService,
]:
    """Construct all application services with their dependencies.

    Returns:
        Tuple of (ActivityService, TemplateService, DayTemplateService,
        ExportService, SettingsService).
    """
    activity_repo = JsonRepository()
    template_repo = TemplateRepository()
    day_template_repo = DayTemplateRepository()
    activity_service = ActivityService(
        repository=activity_repo,
        strategy=IntensityPointStrategy(),
    )
    template_service = TemplateService(repository=template_repo)
    day_template_service = DayTemplateService(repository=day_template_repo)
    export_service = ExportService(
        repository=activity_repo, template_service=template_service
    )
    settings_service = SettingsService()
    return (
        activity_service,
        template_service,
        day_template_service,
        export_service,
        settings_service,
    )


def _with_safe_area(view: ft.View) -> ft.View:
    """Wrap a view's controls in SafeArea so content avoids system UI on mobile.

    Args:
        view: The view whose controls should be wrapped.

    Returns:
        The same view with SafeArea applied around each top-level control.
    """
    view.controls = [
        ft.SafeArea(
            content=ctrl,  # type: ignore[arg-type]
            expand=True,
            maintain_bottom_view_padding=True,
        )
        for ctrl in view.controls
    ]
    return view


def _resolve_view(
    route: str,
    page: ft.Page,
    activity_service: ActivityService,
    template_service: TemplateService,
    day_template_service: DayTemplateService,
    export_service: ExportService,
    settings_service: SettingsService,
) -> ft.View:
    """Map a route string to the corresponding Flet View.

    Args:
        route: The current page route.
        page: The active Flet page.
        activity_service: Shared activity service.
        template_service: Shared activity-definition template service.
        day_template_service: Shared day template service.
        export_service: Shared export service.
        settings_service: Shared settings service.

    Returns:
        The matching View, falling back to the current month view.
    """
    if route == "/":
        return _with_safe_area(HomeView(page).build())
    if route.startswith("/day/"):
        day_date = date.fromisoformat(route.split("/day/")[1])
        return _with_safe_area(
            DayView(
                page, activity_service, template_service, day_date, settings_service
            ).build()
        )
    if route.startswith("/month/"):
        parts = route.split("/")
        return _with_safe_area(
            MonthView(
                page, activity_service, int(parts[2]), int(parts[3]), settings_service
            ).build()
        )
    if route == "/day-templates":
        return _with_safe_area(
            DayTemplatesView(page, day_template_service, activity_service).build()
        )
    if route.startswith("/day-templates/edit/"):
        template_id = route.split("/day-templates/edit/")[1]
        template = day_template_service.get_by_id(template_id)
        if template is not None:
            return _with_safe_area(
                DayTemplateEditView(
                    page,
                    template,
                    day_template_service,
                    template_service,
                    settings_service,
                ).build()
            )
    if route == "/chart":
        return _with_safe_area(
            ChartView(page, activity_service, settings_service).build()
        )
    if route == "/export":
        return _with_safe_area(ExportView(page, export_service).build())
    if route == "/feedback":
        return _with_safe_area(FeedbackView(page).build())
    if route == "/manage-activities":
        return _with_safe_area(ManageActivitiesView(page, template_service).build())
    return _with_safe_area(HomeView(page).build())


async def main(page: ft.Page) -> None:
    """Configure the Flet page, theme, and routing.

    Args:
        page: The root Flet page provided by the framework.
    """
    page.title = "LeefMeter"
    page.theme = ft.Theme(color_scheme_seed="indigo", use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed="indigo", use_material3=True)
    page.theme_mode = ft.ThemeMode.SYSTEM

    (
        activity_service,
        template_service,
        day_template_service,
        export_service,
        settings_service,
    ) = _build_services()

    async def on_route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        page.views.append(
            _resolve_view(
                page.route,
                page,
                activity_service,
                template_service,
                day_template_service,
                export_service,
                settings_service,
            )
        )
        page.update()

    def on_view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        if page.views:
            page.run_task(page.push_route, page.views[-1].route)

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop

    initial_route = "/"
    page.views.clear()
    page.views.append(
        _resolve_view(
            initial_route,
            page,
            activity_service,
            template_service,
            day_template_service,
            export_service,
            settings_service,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
