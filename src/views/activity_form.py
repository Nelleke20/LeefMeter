"""Activity form — add or edit an activity for a given date."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.models.activity import Activity, VALID_CATEGORIES
from src.services.activity_service import ActivityService

_MIN_DURATION_MINUTES: int = 1
_ADD_TITLE: str = "Activiteit toevoegen"
_EDIT_TITLE: str = "Activiteit bewerken"


class ActivityForm:
    """Form view for creating or editing an activity.

    When an existing Activity is passed, the form pre-fills its values
    and calls update_activity on submit. Without an existing activity
    the form starts blank and calls add_activity on submit.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        day_date: date | None = None,
        activity: Activity | None = None,
    ) -> None:
        """Initialise the form, optionally pre-filled with an existing activity.

        Args:
            page: The active Flet page used for navigation.
            service: Service layer for saving or updating the activity.
            day_date: Date to attach the activity to. Defaults to today.
            activity: Existing activity to edit, or None for add mode.
        """
        self._page = page
        self._service = service
        self._date = day_date or date.today()
        self._activity = activity
        self._name_field = ft.TextField(
            label="Naam activiteit",
            autofocus=True,
            value=activity.name if activity else "",
        )
        self._category_dropdown = ft.Dropdown(
            label="Categorie",
            options=[ft.dropdown.Option(c) for c in sorted(VALID_CATEGORIES)],
            value=activity.category if activity else None,
        )
        self._duration_field = ft.TextField(
            label="Duur (minuten)",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=(
                str(activity.duration_minutes)
                if activity
                else str(_MIN_DURATION_MINUTES)
            ),
        )
        self._error_text = ft.Text(value="", color=ft.Colors.ERROR)

    def _is_edit_mode(self) -> bool:
        """Return True when editing an existing activity.

        Returns:
            True if an existing activity was passed, False for add mode.
        """
        return self._activity is not None

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

    async def _on_submit(self, e: ft.ControlEvent) -> None:
        """Validate, save or update the activity, and navigate to DayView.

        Args:
            e: The Flet control event from the submit button.
        """
        error = self._validate()
        if error:
            self._error_text.value = error
            self._page.update()
            return
        if self._is_edit_mode():
            activity = Activity(
                id=self._activity.id,  # type: ignore[union-attr]
                name=self._name_field.value,  # type: ignore[arg-type]
                category=self._category_dropdown.value,  # type: ignore[arg-type]
                duration_minutes=int(self._duration_field.value),  # type: ignore[arg-type]
                date=self._date,
            )
            self._service.update_activity(activity)
        else:
            activity = Activity(
                name=self._name_field.value,  # type: ignore[arg-type]
                category=self._category_dropdown.value,  # type: ignore[arg-type]
                duration_minutes=int(self._duration_field.value),  # type: ignore[arg-type]
                date=self._date,
            )
            self._service.add_activity(activity)
        await self._page.push_route(f"/day/{self._date.isoformat()}")

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the form.

        Returns:
            A ft.View routed to "/add/<date>" or "/edit/<date>/<id>".
        """
        if self._is_edit_mode():
            route = f"/edit/{self._date.isoformat()}/{self._activity.id}"  # type: ignore[union-attr]
            title = _EDIT_TITLE
        else:
            route = f"/add/{self._date.isoformat()}"
            title = _ADD_TITLE
        return ft.View(
            route=route,
            controls=[
                ft.AppBar(
                    title=ft.Text(title),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
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
