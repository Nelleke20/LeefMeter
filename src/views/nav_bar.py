"""Shared navigation drawer factory."""

from __future__ import annotations

from datetime import date

import flet as ft

_TODAY_INDEX: int = 0
_MONTH_INDEX: int = 1
_MANAGE_INDEX: int = 2
_DAY_TEMPLATES_INDEX: int = 3
_CHART_INDEX: int = 4
_EXPORT_INDEX: int = 5


def open_nav_drawer(page: ft.Page) -> None:
    """Open the navigation drawer of the top-most view.

    Args:
        page: The active Flet page.
    """
    if page.views:
        page.run_task(page.views[-1].show_drawer)


def build_nav_drawer(
    page: ft.Page,
    selected_index: int,
    year: int,
    month: int,
) -> ft.NavigationDrawer:
    """Build a NavigationDrawer pre-wired to the top-level routes.

    Args:
        page: The active Flet page used for navigation.
        selected_index: Active tab (0=Dag, 1=Maand, 2=Grafiek,
            3=Activiteiten, 4=Exporteren, 5=Templates).
        year: Year for the /month route.
        month: Month (1-12) for the /month route.

    Returns:
        A configured ft.NavigationDrawer with six destinations and a
        feedback button pinned at the bottom.
    """

    def on_change(e: ft.ControlEvent) -> None:
        if page.views:
            page.run_task(page.views[-1].close_drawer)
        idx = int(e.data)  # type: ignore[arg-type]
        if idx == _TODAY_INDEX:
            today = date.today()
            page.run_task(page.push_route, f"/day/{today.isoformat()}")
        elif idx == _MONTH_INDEX:
            page.run_task(page.push_route, f"/month/{year}/{month}")
        elif idx == _MANAGE_INDEX:
            page.run_task(page.push_route, "/manage-activities")
        elif idx == _DAY_TEMPLATES_INDEX:
            page.run_task(page.push_route, "/day-templates")
        elif idx == _CHART_INDEX:
            page.run_task(page.push_route, "/chart")
        else:
            page.run_task(page.push_route, "/export")

    def on_header_click(e: ft.ControlEvent) -> None:
        if page.views:
            page.run_task(page.views[-1].close_drawer)
        page.run_task(page.push_route, "/")

    def on_feedback_click(e: ft.ControlEvent) -> None:
        if page.views:
            page.run_task(page.views[-1].close_drawer)
        page.run_task(page.push_route, "/feedback")

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Image(src="icon.png", width=36, height=36, border_radius=8),
                ft.Text(
                    "LeefMeter",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=16, top=20, right=16, bottom=12),
        on_click=on_header_click,  # type: ignore[arg-type]
        ink=True,
    )

    return ft.NavigationDrawer(
        selected_index=selected_index,
        on_change=on_change,  # type: ignore[arg-type]
        controls=[
            header,
            ft.Divider(height=1),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.TODAY_OUTLINED,
                selected_icon=ft.Icons.TODAY,
                label="Dag",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_MONTH,
                label="Maand",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.LIST_OUTLINED,
                selected_icon=ft.Icons.LIST,
                label="Activiteiten",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.VIEW_DAY_OUTLINED,
                selected_icon=ft.Icons.VIEW_DAY,
                label="Templates",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.SHOW_CHART_OUTLINED,
                selected_icon=ft.Icons.SHOW_CHART,
                label="Punten",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.DOWNLOAD_OUTLINED,
                selected_icon=ft.Icons.DOWNLOAD,
                label="Exporteren",
            ),
            ft.Divider(height=1),
            ft.Container(height=40),
            ft.Divider(height=1),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.FEEDBACK_OUTLINED,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            size=22,
                        ),
                        ft.Text(
                            "Feedback",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            size=14,
                        ),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=28, top=14, right=16, bottom=14),
                on_click=on_feedback_click,  # type: ignore[arg-type]
                ink=True,
            ),
        ],
    )
