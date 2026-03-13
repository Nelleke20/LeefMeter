"""Activity form — add a new activity for a given date."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.models.activity import Activity, VALID_CATEGORIES
from src.services.activity_service import ActivityService

_MIN_DURATION_MINUTES: int = 1
_MAX_DURATION_MINUTES: int = 480


class ActivityForm:
    """Form view for creating a new activity.

    Presents fields for name, category, and duration. On submit the
    activity is scored and saved via ActivityService, then the user
    is redirected to the corresponding DayView.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        day_date: date | None = None,
    ) -> None:
        """Initialise the form for a specific date.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer for saving the new activity.
            day_date: Date to attach the activity to. Defaults to today.
        """
        self._page = page
        self._service = service
        self._date = day_date or date.today()
        self._name_field = ft.TextField(
            label="Naam activiteit", autofocus=True
        )
        self._category_dropdown = ft.Dropdown(
            label="Categorie",
            options=[ft.dropdown.Option(c) for c in sorted(VALID_CATEGORIES)],
        )
        self._duration_field = ft.TextField(
            label="Duur (minuten)",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(_MIN_DURATION_MINUTES),
        )
        self._error_text = ft.Text(value="", color=ft.colors.ERROR)

    def _validate(self) -> str | None:
        """Check that all required fields are filled in correctly.

        Returns:
            An error message string, or None if the form is valid.
        """
        if not self._name_field.value:
            return "Vul een naam in."
        if not self._category_dropdown.value:
            return "Kies een categorie."
        raw = self._duration_field.value or ""
        if not raw.isdigit() or int(raw) < _MIN_DURATION_MINUTES:
            return f"Duur moet minimaal {_MIN_DURATION_MINUTES} minuut zijn."
        return None

    def _on_submit(self, e: ft.ControlEvent) -> None:
        """Validate, save the activity, and navigate to DayView.

        Args:
            e: The Flet control event from the submit button.
        """
        error = self._validate()
        if error:
            self._error_text.value = error
            self._page.update()
            return
        activity = Activity(
            name=self._name_field.value,  # type: ignore[arg-type]
            category=self._category_dropdown.value,  # type: ignore[arg-type]
            duration_minutes=int(self._duration_field.value),  # type: ignore[arg-type]
            date=self._date,
        )
        self._service.add_activity(activity)
        self._page.go(f"/day/{self._date.isoformat()}")

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the form.

        Returns:
            A ft.View routed to "/add/<date>".
        """
        return ft.View(
            route=f"/add/{self._date.isoformat()}",
            controls=[
                ft.AppBar(
                    title=ft.Text("Activiteit toevoegen"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                ),
                ft.Column(
                    controls=[
                        self._name_field,
                        self._category_dropdown,
                        self._duration_field,
                        self._error_text,
                        ft.ElevatedButton(
                            "Opslaan", on_click=self._on_submit
                        ),
                    ],
                    spacing=16,
                    expand=True,
                ),
            ],
        )
