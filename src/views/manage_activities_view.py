"""Register activities view — add, move between categories, and delete templates."""

from __future__ import annotations

from datetime import date

import flet as ft

from src.models.activity import INTENSITY_LEVELS
from src.models.template import Template
from src.services.template_service import TemplateService
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_NAV_INDEX: int = 2

_INTENSITY_LABELS: dict[str, str] = {
    "rust": "Rust (−1 pt / 30 min)",
    "laag": "Laag (+1 pt / 30 min)",
    "gemiddeld": "Gemiddeld (+2 pt / 30 min)",
    "zwaar": "Zwaar (+3 pt / 30 min)",
}

_CATEGORY_DISPLAY: dict[str, str] = {
    "rust": "Rust",
    "laag": "Laag",
    "gemiddeld": "Gemiddeld",
    "zwaar": "Zwaar",
}


class ManageActivitiesView:
    """Full-page view for registering and managing activity templates.

    Shows all saved activity names grouped by category.
    Allows adding new activities, moving between categories, and deleting.
    """

    def __init__(self, page: ft.Page, template_service: TemplateService) -> None:
        """Initialise with page and template service.

        Args:
            page: The active Flet page.
            template_service: Service for CRUD on activity templates.
        """
        self._page = page
        self._ts = template_service
        self._list_col = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True)

    def _refresh(self) -> None:
        """Reload templates and rebuild the list in-place."""
        templates = self._ts.get_all_templates()
        controls: list[ft.Control] = []

        for category in INTENSITY_LEVELS:
            cat_templates = sorted(
                [t for t in templates if t.category == category], key=lambda t: t.name
            )
            controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                _CATEGORY_DISPLAY[category],
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.ON_SECONDARY_CONTAINER,
                                size=13,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                icon_color=ft.Colors.ON_SECONDARY_CONTAINER,
                                icon_size=18,
                                tooltip=(
                                    f"Toevoegen aan {_CATEGORY_DISPLAY[category]}"
                                ),
                                on_click=self._make_add_handler(  # type: ignore[arg-type]  # noqa: E501
                                    category
                                ),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    border_radius=8,
                    padding=ft.padding.only(left=12, top=2, bottom=2, right=4),
                    margin=ft.margin.only(top=8, bottom=2),
                )
            )
            for tmpl in cat_templates:
                controls.append(self._build_row(tmpl))

        if not any(isinstance(c, ft.Row) for c in controls):
            controls.append(
                ft.Container(
                    content=ft.Text(
                        "Nog geen activiteiten. Voeg er hieronder een toe.",
                        color=ft.Colors.OUTLINE,
                        size=13,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                )
            )

        self._list_col.controls = controls
        self._page.update()

    def _make_add_handler(
        self, category: str
    ) -> ft.ControlEventHandler:  # type: ignore[type-arg]
        """Return a click handler that opens the add dialog for a category.

        Args:
            category: The intensity category to add to.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            self._show_add_dialog(category)

        return handler  # type: ignore[return-value]

    def _show_add_dialog(self, preset_category: str) -> None:
        """Open a dialog to add a new activity to a category.

        Args:
            preset_category: Category pre-selected in the dropdown.
        """
        name_field = ft.TextField(
            label="Naam activiteit",
            border_radius=12,
            autofocus=True,
        )
        category_dd = ft.Dropdown(
            label="Categorie",
            value=preset_category,
            options=[
                ft.dropdown.Option(key=lvl, text=_INTENSITY_LABELS[lvl])
                for lvl in INTENSITY_LEVELS
            ],
            border_radius=12,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def on_save(ev: ft.ControlEvent) -> None:
            name = (name_field.value or "").strip()
            if not name:
                error_text.value = "Vul een naam in."
                self._page.update()
                return
            cat = category_dd.value or preset_category
            self._ts.add_template(
                Template(name=name, category=cat, duration_minutes=30)
            )
            self._page.pop_dialog()
            self._refresh()

        def on_cancel(ev: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=False,
                title=ft.Text("Activiteit toevoegen"),
                content=ft.Column(
                    controls=[name_field, category_dd, error_text],
                    spacing=12,
                    tight=True,
                    width=300,
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=on_cancel),
                    ft.FilledButton("Opslaan", on_click=on_save),
                ],
            )
        )

    def _show_edit_dialog(self, tmpl: Template) -> None:
        """Open a dialog to rename or move an activity to another category.

        Args:
            tmpl: The template to edit.
        """
        name_field = ft.TextField(
            label="Naam activiteit",
            value=tmpl.name,
            border_radius=12,
            autofocus=True,
        )
        category_dd = ft.Dropdown(
            label="Categorie",
            value=tmpl.category,
            options=[
                ft.dropdown.Option(key=lvl, text=_INTENSITY_LABELS[lvl])
                for lvl in INTENSITY_LEVELS
            ],
            border_radius=12,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def on_save(ev: ft.ControlEvent) -> None:
            name = (name_field.value or "").strip()
            if not name:
                error_text.value = "Vul een naam in."
                self._page.update()
                return
            tmpl.name = name
            tmpl.category = category_dd.value or tmpl.category
            self._ts.update_template(tmpl)
            self._page.pop_dialog()
            self._refresh()

        def on_cancel(ev: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=False,
                title=ft.Text("Activiteit bewerken"),
                content=ft.Column(
                    controls=[name_field, category_dd, error_text],
                    spacing=12,
                    tight=True,
                    width=300,
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=on_cancel),
                    ft.FilledButton("Opslaan", on_click=on_save),
                ],
            )
        )

    def _build_row(self, tmpl: Template) -> ft.Row:
        """Build a single activity row with edit and delete buttons.

        Args:
            tmpl: The template to display.

        Returns:
            A Row with name, edit icon, and delete icon.
        """

        def on_edit(e: ft.ControlEvent) -> None:
            self._show_edit_dialog(tmpl)

        def on_delete(e: ft.ControlEvent) -> None:
            self._ts.delete_template(tmpl.id)
            self._refresh()

        return ft.Row(
            controls=[
                ft.Text(
                    tmpl.name,
                    expand=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    size=14,
                ),
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_color=ft.Colors.SECONDARY,
                    icon_size=18,
                    tooltip="Naam of categorie wijzigen",
                    on_click=on_edit,  # type: ignore[arg-type]
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.ERROR,
                    icon_size=18,
                    tooltip="Verwijderen",
                    on_click=on_delete,  # type: ignore[arg-type]
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for activity registration.

        Returns:
            A ft.View routed to \"/manage-activities\".
        """
        today = date.today()
        self._refresh()

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
                                        "Registreer activiteiten",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                ],
                            ),
                            self._list_col,
                        ],
                        expand=True,
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    expand=True,
                ),
            ],
            expand=True,
        )
        view = ft.View(
            route="/manage-activities",
            padding=0,
            controls=[content_column],
        )
        view.drawer = build_nav_drawer(
            self._page,
            selected_index=_NAV_INDEX,
            year=today.year,
            month=today.month,
        )
        return view
