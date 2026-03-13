"""Shared navigation drawer factory."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.services.activity_service import ActivityService

_ITEM_TODAY = 0
_ITEM_AGENDA = 1
_ITEM_MONTH = 2
_ITEM_TEMPLATES = 3
_ITEM_SEND = 4

_ROUTES: dict[int, str] = {
    _ITEM_AGENDA: "/",
    _ITEM_TEMPLATES: "/templates",
    _ITEM_SEND: "/export",
}


def build_drawer(page: ft.Page) -> ft.NavigationDrawer:
    """Build the app-wide navigation drawer.

    Args:
        page: The active Flet page used for navigation and closing the drawer.

    Returns:
        A configured ft.NavigationDrawer with all main destinations.
    """

    async def on_change(e: ft.ControlEvent) -> None:
        page.close_drawer()
        today = date.today()
        idx = e.control.selected_index
        if idx == _ITEM_TODAY:
            await page.push_route(f"/day/{today.isoformat()}")
        elif idx == _ITEM_MONTH:
            await page.push_route(f"/month/{today.year}/{today.month}")
        elif idx in _ROUTES:
            await page.push_route(_ROUTES[idx])

    return ft.NavigationDrawer(
        on_change=on_change,
        controls=[
            ft.Container(height=16),
            ft.Text(
                "LeefMeter",
                size=22,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.PRIMARY,
            ),
            ft.Container(height=8),
            ft.Divider(),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.TODAY_OUTLINED,
                selected_icon=ft.Icons.TODAY,
                label="Vandaag",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.LIST_ALT_OUTLINED,
                selected_icon=ft.Icons.LIST_ALT,
                label="Agenda",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_MONTH,
                label="Maand",
            ),
            ft.Divider(),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.BOOKMARK_BORDER,
                selected_icon=ft.Icons.BOOKMARK,
                label="Templates",
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.SEND_OUTLINED,
                selected_icon=ft.Icons.SEND,
                label="Versturen",
            ),
        ],
    )
