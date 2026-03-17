"""Home view — entry point landing screen for LeefMeter."""

from __future__ import annotations

from datetime import date

import flet as ft


class HomeView:
    """Renders the home/landing screen for LeefMeter.

    Shows the app logo, name, short description, and a button to navigate
    to the current month overview. No navigation drawer is shown on this view.
    """

    def __init__(self, page: ft.Page) -> None:
        """Initialise with the active Flet page.

        Args:
            page: The active Flet page used for navigation.
        """
        self._page = page

    def _on_go_to_month(self, e: ft.ControlEvent) -> None:
        """Navigate to the current month overview.

        Args:
            e: The click event from the button.
        """
        today = date.today()
        self._page.run_task(self._page.push_route, f"/month/{today.year}/{today.month}")

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the home screen.

        Returns:
            A ft.View routed to "/" with centered logo, title, description,
            and a navigation button.
        """
        content = ft.Column(
            controls=[
                ft.Image(
                    src="icon.png",
                    width=120,
                    height=120,
                    border_radius=16,
                ),
                ft.Text(
                    "Welkom bij de LeefMeter",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Jouw persoonlijke gids voor een gebalanceerde dag.",
                    size=16,
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.PRIMARY,
                ),
                ft.Divider(height=1, thickness=1),
                ft.Text(
                    "Registreer je activiteiten, houd je energiepunten bij "
                    "en ontdek hoe je je dag beter kunt verdelen. ",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.FilledButton(
                    "Ga naar maandoverzicht",
                    icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                    on_click=self._on_go_to_month,  # type: ignore[arg-type]
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            expand=True,
        )

        return ft.View(
            route="/",
            padding=ft.padding.all(32),
            controls=[content],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
