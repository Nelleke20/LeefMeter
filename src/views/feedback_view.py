"""Feedback view — lets the user send feedback via email."""

from __future__ import annotations

import urllib.parse
from datetime import date

import flet as ft

from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_FEEDBACK_EMAIL: str = "nelleke_s@hotmail.com"
_FEEDBACK_SUBJECT: str = "Feedback LeefMeter"
_FEEDBACK_INDEX: int = -1


class FeedbackView:
    """Renders a simple feedback form that opens the device email app.

    Uses page.launch_url() with a mailto: URI on all platforms. This goes
    through Flutter's url_launcher plugin which correctly triggers the Android
    Intent system inside the app's Activity context.
    """

    def __init__(self, page: ft.Page) -> None:
        """Initialise with page.

        Args:
            page: The active Flet page.
        """
        self._page = page
        self._text_field = ft.TextField(
            label="Jouw bericht",
            multiline=True,
            min_lines=5,
            max_lines=10,
            expand=True,
        )
        self._status_text = ft.Text(value="", color=ft.Colors.PRIMARY, size=12)

    async def _on_send(self, e: ft.ControlEvent) -> None:
        """Open the default email app with the typed message pre-filled.

        Uses UrlLauncher to open a mailto URI on all platforms.

        Args:
            e: Click event from the send button.
        """
        body = self._text_field.value or ""
        mailto = (
            f"mailto:{_FEEDBACK_EMAIL}"
            f"?subject={urllib.parse.quote(_FEEDBACK_SUBJECT, safe='')}"
            f"&body={urllib.parse.quote(body, safe='')}"
        )
        try:
            await self._page.launch_url(mailto)  # type: ignore[misc]
            self._status_text.value = "E-mailapp wordt geopend..."
            self._status_text.color = ft.Colors.PRIMARY
        except Exception as exc:
            self._status_text.value = f"Fout: {exc}"
            self._status_text.color = ft.Colors.ERROR
        self._page.update()

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the feedback screen.

        Returns:
            A ft.View routed to \"/feedback\".
        """
        today = date.today()
        content_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.MENU,
                                        on_click=lambda _: open_nav_drawer(self._page),
                                        icon_size=20,
                                    ),
                                    ft.Text(
                                        "Feedback",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                "Typ je bericht en tik op 'Verstuur'.",
                                size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            self._text_field,
                            ft.FilledButton(
                                "Verstuur via e-mail",
                                icon=ft.Icons.SEND_OUTLINED,
                                on_click=self._on_send,  # type: ignore[arg-type]
                            ),
                            self._status_text,
                        ],
                        spacing=16,
                        expand=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    expand=True,
                ),
            ],
            expand=True,
        )
        view = ft.View(
            route="/feedback",
            padding=0,
            controls=[content_column],
        )
        view.drawer = build_nav_drawer(
            self._page,
            selected_index=_FEEDBACK_INDEX,
            year=today.year,
            month=today.month,
        )
        return view
