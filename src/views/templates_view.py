"""Templates view — manage and apply reusable activity templates."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.activity import INTENSITY_LEVELS
from src.models.template import Template
from src.services.activity_service import ActivityService
from src.services.template_service import TemplateService

_INTENSITY_LABELS: dict[str, str] = {
    "rust": "Rust (−1 pt/30 min)",
    "laag": "Laag (+1 pt/30 min)",
    "gemiddeld": "Gemiddeld (+2 pt/30 min)",
    "zwaar": "Zwaar (+3 pt/30 min)",
}


class TemplatesView:
    """Renders the template list and a form to add new templates.

    Templates can be applied to today, creating a scored activity.
    """

    def __init__(
        self,
        page: ft.Page,
        template_service: TemplateService,
        activity_service: ActivityService,
    ) -> None:
        """Initialise with services for templates and activities.

        Args:
            page: The active Flet page used for navigation.
            template_service: Manages template CRUD.
            activity_service: Used when applying a template.
        """
        self._page = page
        self._ts = template_service
        self._as = activity_service
        self._name_field = ft.TextField(
            label="Naam", border_radius=12, expand=True
        )
        self._intensity_dropdown = ft.Dropdown(
            label="Intensiteit",
            options=[
                ft.dropdown.Option(key=lvl, text=_INTENSITY_LABELS[lvl])
                for lvl in INTENSITY_LEVELS
            ],
            border_radius=12,
            expand=True,
        )
        self._duration_field = ft.TextField(
            label="Duur (min)",
            keyboard_type=ft.KeyboardType.NUMBER,
            value="30",
            border_radius=12,
            width=100,
        )
        self._error_text = ft.Text(value="", color=ft.Colors.ERROR)

    def _refresh(self) -> None:
        """Rebuild and replace the current view in-place."""
        self._page.views[-1] = TemplatesView(
            self._page, self._ts, self._as
        ).build()
        self._page.update()

    def _on_delete(self, template_id: str) -> Callable[[ft.ControlEvent], None]:
        """Return a handler deleting a template and refreshing.

        Args:
            template_id: UUID of the template to delete.

        Returns:
            Async event handler.
        """

        async def handler(e: ft.ControlEvent) -> None:
            self._ts.delete_template(template_id)
            self._refresh()

        return handler

    def _on_apply(self, template: Template) -> Callable[[ft.ControlEvent], None]:
        """Return a handler applying a template to today.

        Args:
            template: The template to apply.

        Returns:
            Async event handler.
        """

        async def handler(e: ft.ControlEvent) -> None:
            self._ts.apply_template(template, date.today(), self._as)
            await self._page.push_route(f"/day/{date.today().isoformat()}")

        return handler

    async def _on_add(self, e: ft.ControlEvent) -> None:
        """Validate the form and add a new template.

        Args:
            e: The Flet control event from the save button.
        """
        if not self._name_field.value or not self._intensity_dropdown.value:
            self._error_text.value = "Vul naam en intensiteit in."
            self._page.update()
            return
        raw = self._duration_field.value or ""
        if not raw.isdigit() or int(raw) < 1:
            self._error_text.value = "Ongeldige duur."
            self._page.update()
            return
        template = Template(
            name=self._name_field.value,
            category=self._intensity_dropdown.value,
            duration_minutes=int(raw),
        )
        self._ts.add_template(template)
        self._refresh()

    def _build_template_tile(self, template: Template) -> ft.Card:
        """Build a card for a single template.

        Args:
            template: The template to render.

        Returns:
            A Card with apply and delete actions.
        """
        label = _INTENSITY_LABELS.get(template.category, template.category)
        return ft.Card(
            content=ft.ListTile(
                title=ft.Text(template.name, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(f"{label} · {template.duration_minutes} min"),
                trailing=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW_OUTLINED,
                            icon_color=ft.Colors.PRIMARY,
                            tooltip="Vandaag toepassen",
                            on_click=self._on_apply(template),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.ERROR,
                            on_click=self._on_delete(template.id),
                        ),
                    ],
                    tight=True,
                    spacing=0,
                ),
            ),
            margin=ft.margin.symmetric(horizontal=8, vertical=4),
        )

    def _build_add_form(self) -> ft.Container:
        """Build the form for adding a new template.

        Returns:
            A Container wrapping the add-template form fields.
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Nieuw template",
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    ),
                    ft.Row(
                        controls=[self._name_field, self._duration_field],
                        spacing=8,
                    ),
                    self._intensity_dropdown,
                    self._error_text,
                    ft.FilledButton(
                        "Template opslaan",
                        icon=ft.Icons.ADD,
                        on_click=self._on_add,
                    ),
                ],
                spacing=10,
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border_radius=12,
            margin=ft.margin.all(8),
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for templates.

        Returns:
            A ft.View routed to "/templates".
        """
        templates = self._ts.get_all_templates()
        empty = ft.Container(
            content=ft.Text("Nog geen templates.", color=ft.Colors.OUTLINE),
            padding=16,
        )
        tiles: list[ft.Control] = (
            [self._build_template_tile(t) for t in templates]
            if templates
            else [empty]
        )
        return ft.View(
            route="/templates",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.MENU,
                        on_click=lambda _: self._page.show_drawer() and None,
                    ),
                    leading_width=48,
                    title=ft.Text("Templates"),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                ),
                ft.Column(
                    controls=[
                        ft.ListView(controls=tiles, expand=True),
                        self._build_add_form(),
                    ],
                    expand=True,
                ),
            ],
        )
