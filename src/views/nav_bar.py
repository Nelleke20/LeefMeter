"""Shared bottom navigation bar factory."""

from __future__ import annotations

import flet as ft

_AGENDA_INDEX: int = 0
_MONTH_INDEX: int = 1


def build_nav_bar(
    page: ft.Page,
    selected_index: int,
    year: int,
    month: int,
) -> ft.NavigationBar:
    """Build a NavigationBar pre-wired to the top-level routes.

    Args:
        page: The active Flet page used for navigation.
        selected_index: Which tab is currently active (0=Agenda, 1=Maand).
        year: Year to use when building the /month route.
        month: Month (1-12) to use when building the /month route.

    Returns:
        A configured ft.NavigationBar with Agenda and Maand destinations.
    """

    async def on_change(e: ft.ControlEvent) -> None:
        idx = int(e.data)
        if idx == _AGENDA_INDEX:
            await page.push_route("/")
        else:
            await page.push_route(f"/month/{year}/{month}")

    return ft.NavigationBar(
        selected_index=selected_index,
        on_change=on_change,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.LIST_ALT_OUTLINED,
                selected_icon=ft.Icons.LIST_ALT,
                label="Agenda",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                selected_icon=ft.Icons.CALENDAR_MONTH,
                label="Maand",
            ),
        ],
    )
