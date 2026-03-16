"""Export view — export activities to Excel."""

from __future__ import annotations

import os
import subprocess
from datetime import date

import flet as ft

from src.services.export_service import ExportService, get_export_path
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_NO_DATE: str = "Geen datum"


class ExportView:
    """Lets the user export all activity data to an Excel file.

    Date range can be selected via a calendar date picker.
    On Android the file is saved to the app's external files directory,
    visible in the Files app under Android > data > com.flet.leefmeter > files.
    On desktop it is saved to ~/Downloads.
    """

    def __init__(self, page: ft.Page, export_service: ExportService) -> None:
        """Initialise with the Flet page and export service.

        Args:
            page: The active Flet page.
            export_service: Service that writes the Excel file.
        """
        self._page = page
        self._export_service = export_service
        self._from_date: date | None = None
        self._to_date: date | None = None
        self._status_text = ft.Text(value="", color=ft.Colors.PRIMARY)
        self._from_label = ft.Text(_NO_DATE, color=ft.Colors.ON_SURFACE_VARIANT)
        self._to_label = ft.Text(_NO_DATE, color=ft.Colors.ON_SURFACE_VARIANT)

        self._from_picker = ft.DatePicker(
            on_change=self._on_from_change,
            on_dismiss=lambda _: None,
        )
        self._to_picker = ft.DatePicker(
            on_change=self._on_to_change,
            on_dismiss=lambda _: None,
        )

    def _on_from_change(self, e: ft.ControlEvent) -> None:
        """Store the selected from-date and update label.

        Args:
            e: Change event from the from-date picker.
        """
        val = self._from_picker.value
        if val is not None:
            self._from_date = val.date() if hasattr(val, "date") else val
            self._from_label.value = self._from_date.strftime("%d-%m-%Y")
        else:
            self._from_date = None
            self._from_label.value = _NO_DATE
        self._page.update()

    def _on_to_change(self, e: ft.ControlEvent) -> None:
        """Store the selected to-date and update label.

        Args:
            e: Change event from the to-date picker.
        """
        val = self._to_picker.value
        if val is not None:
            self._to_date = val.date() if hasattr(val, "date") else val
            self._to_label.value = self._to_date.strftime("%d-%m-%Y")
        else:
            self._to_date = None
            self._to_label.value = _NO_DATE
        self._page.update()

    def _open_from_picker(self, e: ft.ControlEvent) -> None:
        """Open the from-date calendar picker.

        Args:
            e: Click event from the from-date button.
        """
        self._from_picker.open = True
        self._page.update()

    def _open_to_picker(self, e: ft.ControlEvent) -> None:
        """Open the to-date calendar picker.

        Args:
            e: Click event from the to-date button.
        """
        self._to_picker.open = True
        self._page.update()

    def _open_android_settings(self, e: ft.ControlEvent) -> None:
        """Open Android app-permissions settings so the user can grant storage.

        Only effective on Android. Launches the system settings page for
        managing all-files access for this app.

        Args:
            e: Click event from the settings button.
        """
        try:
            subprocess.Popen(
                [
                    "am",
                    "start",
                    "-a",
                    "android.settings.MANAGE_APP_ALL_FILES_ACCESS_PERMISSION",
                    "-d",
                    "package:com.flet.leefmeter",
                ]
            )
        except Exception:
            subprocess.Popen(  # type: ignore[call-overload]
                [
                    "am",
                    "start",
                    "-a",
                    "android.settings.APPLICATION_DETAILS_SETTINGS",
                    "-d",
                    "package:com.flet.leefmeter",
                ]
            )
        self._page.pop_dialog()

    def _show_permission_dialog(self) -> None:
        """Show a dialog explaining how to grant storage permission on Android."""
        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Toegang tot Bestanden vereist"),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Om op te slaan in Documenten heeft de app "
                            "'Toegang tot alle bestanden' nodig.\n\n"
                            "Tik op 'Open instellingen', zoek 'Toegang tot "
                            "alle bestanden' en zet deze aan voor LeefMeter.",
                            size=13,
                        ),
                    ],
                    tight=True,
                    width=280,
                ),
                actions=[
                    ft.TextButton(
                        "Annuleren",
                        on_click=lambda _: self._page.pop_dialog(),
                    ),
                    ft.FilledButton(
                        "Open instellingen",
                        icon=ft.Icons.SETTINGS,
                        on_click=self._open_android_settings,  # type: ignore[arg-type]
                    ),
                ],
            )
        )

    def _on_export(self, e: ft.ControlEvent) -> None:
        """Generate the Excel file and show the save path.

        On Android, if saving to Documents fails due to missing permissions,
        shows a dialog guiding the user to grant storage access.

        Args:
            e: Click event from the export button.
        """
        try:
            path = self._export_service.export(
                from_date=self._from_date,
                to_date=self._to_date,
            )
            self._status_text.color = ft.Colors.PRIMARY
            self._status_text.value = f"Opgeslagen: {path}"
            self._page.update()
        except PermissionError:
            self._page.update()
            if os.environ.get("FLET_APP_STORAGE_DATA"):
                self._show_permission_dialog()
            else:
                self._status_text.color = ft.Colors.ERROR
                self._status_text.value = "Geen toegang tot de opslagmap."
                self._page.update()
        except Exception as exc:
            self._status_text.color = ft.Colors.ERROR
            self._status_text.value = f"Fout: {exc}"
            self._page.update()

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the export screen.

        Returns:
            A ft.View routed to "/export".
        """
        today = date.today()
        if self._from_picker not in self._page.overlay:
            self._page.overlay.append(self._from_picker)
        if self._to_picker not in self._page.overlay:
            self._page.overlay.append(self._to_picker)

        if os.environ.get("FLET_APP_STORAGE_DATA"):
            hint_text = "Wordt opgeslagen in: Interne opslag > Documenten"
        else:
            hint_text = f"Wordt opgeslagen in: {get_export_path()}"
        path_hint = ft.Text(
            hint_text,
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        )

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
                                        "Exporteren",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                "Van",
                                                weight=ft.FontWeight.W_500,
                                            ),
                                            ft.OutlinedButton(
                                                "Kies datum",
                                                icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
                                                on_click=self._open_from_picker,
                                            ),
                                            self._from_label,
                                        ],
                                        horizontal_alignment=(
                                            ft.CrossAxisAlignment.CENTER
                                        ),
                                        spacing=4,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                "Tot",
                                                weight=ft.FontWeight.W_500,
                                            ),
                                            ft.OutlinedButton(
                                                "Kies datum",
                                                icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
                                                on_click=self._open_to_picker,
                                            ),
                                            self._to_label,
                                        ],
                                        horizontal_alignment=(
                                            ft.CrossAxisAlignment.CENTER
                                        ),
                                        spacing=4,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=24,
                            ),
                            ft.FilledButton(
                                "Exporteer naar Excel",
                                icon=ft.Icons.DOWNLOAD_OUTLINED,
                                on_click=self._on_export,  # type: ignore[arg-type]
                            ),
                            path_hint,
                            self._status_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    padding=24,
                    expand=True,
                ),
            ],
            expand=True,
        )
        view = ft.View(
            route="/export",
            padding=0,
            controls=[content_column],
        )
        view.drawer = build_nav_drawer(
            self._page,
            selected_index=5,
            year=today.year,
            month=today.month,
        )
        return view
