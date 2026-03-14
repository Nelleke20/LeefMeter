"""Shared left-side navigation rail factory."""

from __future__ import annotations

from datetime import date

import flet as ft

_TODAY_INDEX: int = 0
_MONTH_INDEX: int = 1
_DAY_TEMPLATES_INDEX: int = 2
_EXPORT_INDEX: int = 3
_CHART_INDEX: int = 4


def build_nav_rail(
    page: ft.Page,
    selected_index: int,
    year: int,
    month: int,
) -> ft.NavigationRail:
    """Build a NavigationRail pre-wired to the top-level routes.

    Args:
        page: The active Flet page used for navigation.
        selected_index: Active tab (0=Dag, 1=Maand, 2=Templates, 3=Exporteren, 4=Grafiek).
        year: Year for the /month route.
        month: Month (1-12) for the /month route.

    Returns:
        A configured ft.NavigationRail with five destinations.
    """

    def on_change(e: ft.ControlEvent) -> None:
        idx = int(e.data)
        if idx == _TODAY_INDEX:
            today = date.today()
            page.run_task(page.push_route, f"/day/{today.isoformat()}")
        elif idx == _MONTH_INDEX:
            page.run_task(page.push_route, f"/month/{year}/{month}")
        elif idx == _DAY_TEMPLATES_INDEX:
            page.run_task(page.push_route, "/day-templates")
        elif idx == _EXPORT_INDEX:
            page.run_task(page.push_route, "/export")
        else:
            page.run_task(page.push_route, "/chart")

    return ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        on_change=on_change,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.TODAY_OUTLINED,
                selected_icon=ft.Icons.TODAY,
                label="Dag",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_MONTH,
                label="Maand",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.VIEW_DAY_OUTLINED,
                selected_icon=ft.Icons.VIEW_DAY,
                label="Templates",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DOWNLOAD_OUTLINED,
                selected_icon=ft.Icons.DOWNLOAD,
                label="Exporteren",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SHOW_CHART_OUTLINED,
                selected_icon=ft.Icons.SHOW_CHART,
                label="Grafiek",
            ),
        ],
    )
