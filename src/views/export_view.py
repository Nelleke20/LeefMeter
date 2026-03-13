"""Export / Versturen view — export activities to Excel and email."""

from __future__ import annotations

from pathlib import Path

import flet as ft

from src.services.export_service import ExportService

_DEFAULT_EMAIL: str = ""
_EXPORT_PATH: Path = Path.home() / "Downloads" / "leefmeter_export.xlsx"


class ExportView:
    """Lets the user export all activity data to Excel and send by email.

    The Excel file is saved to ~/Downloads. A mailto: link is opened
    in the default mail client, where the user can attach the file.
    """

    def __init__(self, page: ft.Page, export_service: ExportService) -> None:
        """Initialise with the Flet page and export service.

        Args:
            page: The active Flet page used for dialogs and URL launching.
            export_service: Service that writes the Excel file.
        """
        self._page = page
        self._export_service = export_service
        self._email_field = ft.TextField(
            label="E-mailadres",
            keyboard_type=ft.KeyboardType.EMAIL,
            value=_DEFAULT_EMAIL,
            border_radius=12,
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
        )
        self._status_text = ft.Text(value="", color=ft.Colors.PRIMARY)

    async def _on_export(self, e: ft.ControlEvent) -> None:
        """Create the Excel file and update the status message.

        Args:
            e: The Flet control event from the export button.
        """
        try:
            path = self._export_service.export(output_path=_EXPORT_PATH)
            self._status_text.color = ft.Colors.PRIMARY
            self._status_text.value = f"Opgeslagen: {path}"
        except Exception as exc:
            self._status_text.color = ft.Colors.ERROR
            self._status_text.value = f"Fout: {exc}"
        self._page.update()

    async def _on_send(self, e: ft.ControlEvent) -> None:
        """Open the default mail client with a pre-filled subject.

        Creates the Excel file first, then opens a mailto: link.

        Args:
            e: The Flet control event from the send button.
        """
        email = self._email_field.value or ""
        if not email:
            self._status_text.color = ft.Colors.ERROR
            self._status_text.value = "Vul een e-mailadres in."
            self._page.update()
            return
        try:
            path = self._export_service.export(output_path=_EXPORT_PATH)
            self._status_text.color = ft.Colors.PRIMARY
            self._status_text.value = (
                f"Bestand klaar: {path}\n"
                "Voeg het bestand toe als bijlage in je mail."
            )
        except Exception as exc:
            self._status_text.color = ft.Colors.ERROR
            self._status_text.value = f"Fout: {exc}"
            self._page.update()
            return
        subject = "LeefMeter export"
        body = "Bijgevoegd vind je de LeefMeter activiteitenexport."
        await self._page.launch_url_async(
            f"mailto:{email}?subject={subject}&body={body}"
        )
        self._page.update()

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the export screen.

        Returns:
            A ft.View routed to "/export".
        """
        return ft.View(
            route="/export",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.MENU,
                        on_click=lambda _: self._page.show_drawer() and None,
                    ),
                    leading_width=48,
                    title=ft.Text("Versturen"),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.TABLE_CHART_OUTLINED,
                                size=56,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.Text(
                                "Exporteer je activiteiten naar Excel.",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.FilledTonalButton(
                                "Exporteer naar Excel",
                                icon=ft.Icons.DOWNLOAD_OUTLINED,
                                on_click=self._on_export,
                            ),
                            ft.Divider(),
                            ft.Text(
                                "Stuur per e-mail",
                                weight=ft.FontWeight.BOLD,
                            ),
                            self._email_field,
                            ft.FilledButton(
                                "Versturen",
                                icon=ft.Icons.SEND_OUTLINED,
                                on_click=self._on_send,
                            ),
                            self._status_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    padding=24,
                    expand=True,
                ),
            ],
        )
