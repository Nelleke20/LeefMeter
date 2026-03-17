"""Day templates view — list, create, apply and delete day schedules."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import flet as ft

from src.models.day_template import DayTemplate
from src.services.activity_service import ActivityService
from src.services.day_template_service import DayTemplateService
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_NAV_INDEX: int = 3


class DayTemplatesView:
    """Lists day templates with apply, edit, and delete actions.

    New templates are created with just a name and start empty.
    Activities are added via the edit view.
    """

    def __init__(
        self,
        page: ft.Page,
        day_template_service: DayTemplateService,
        activity_service: ActivityService,
    ) -> None:
        """Initialise with services.

        Args:
            page: The active Flet page.
            day_template_service: CRUD for day templates.
            activity_service: Used when applying templates.
        """
        self._page = page
        self._dts = day_template_service
        self._as = activity_service
        self._tiles_list = ft.ListView(expand=True)

    def _refresh_tiles(self) -> None:
        """Reload templates and rebuild the card list in-place."""
        templates = self._dts.get_all()
        if templates:
            self._tiles_list.controls = [
                self._build_template_card(t) for t in templates
            ]
        else:
            self._tiles_list.controls = [
                ft.Container(
                    content=ft.Text(
                        "Nog geen dag templates.",
                        color=ft.Colors.OUTLINE,
                    ),
                    padding=16,
                )
            ]
        self._page.update()

    def _on_delete(self, template_id: str) -> Callable[[ft.ControlEvent], None]:
        """Return a handler that deletes a template and refreshes in-place.

        Args:
            template_id: UUID of the template to delete.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            self._dts.delete(template_id)
            self._refresh_tiles()

        return handler

    def _on_edit(self, template: DayTemplate) -> Callable[[ft.ControlEvent], None]:
        """Return a handler navigating to the template edit view.

        Args:
            template: Template to edit.

        Returns:
            Async event handler.
        """

        async def handler(e: ft.ControlEvent) -> None:
            await self._page.push_route(f"/day-templates/edit/{template.id}")

        return handler

    def _on_apply(self, template: DayTemplate) -> Callable[[ft.ControlEvent], None]:
        """Return a handler that opens the apply-to-day dialog.

        Args:
            template: The template to apply.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            def on_date_change(ev: ft.ControlEvent) -> None:
                val = picker.value  # type: ignore[union-attr]
                if val is not None:
                    if hasattr(val, "hour"):
                        # Shift +12h to neutralise any UTC timezone offset
                        # (Android DatePicker may return midnight UTC = prev day local)
                        shifted = val + timedelta(hours=12)
                        target = date(shifted.year, shifted.month, shifted.day)
                    else:
                        target = val
                    self._dts.apply_to_day(template, target, self._as)
                    self._page.run_task(
                        self._page.push_route, f"/day/{target.isoformat()}"
                    )

            picker = ft.DatePicker(
                value=date.today(),
                on_change=on_date_change,
                on_dismiss=lambda _: None,
                help_text=(
                    f"Pas toe: {template.name}"
                    f" ({len(template.entries)} activiteiten)"
                ),
                confirm_text="Toepassen",
                cancel_text="Annuleren",
            )
            self._page.overlay.append(picker)
            self._page.update()
            picker.open = True
            self._page.update()

        return handler

    def _on_create(self, e: ft.ControlEvent) -> None:
        """Open a dialog to create a new empty template.

        Args:
            e: Click event from the create button.
        """
        name_field = ft.TextField(
            label="Naam template",
            hint_text="Bijv. Werkdag, Rustdag",
            border_radius=12,
            autofocus=True,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def on_save(e: ft.ControlEvent) -> None:
            name = (name_field.value or "").strip()
            if not name:
                error_text.value = "Vul een naam in."
                self._page.update()
                return
            from src.models.day_template import DayTemplate as DT

            new_template = DT(name=name, entries=[])
            self._dts.save(new_template)
            self._page.pop_dialog()
            self._page.run_task(
                self._page.push_route, f"/day-templates/edit/{new_template.id}"
            )

        def on_cancel(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=False,
                title=ft.Text("Nieuw dag template"),
                content=ft.Column(
                    controls=[name_field, error_text],
                    spacing=12,
                    tight=True,
                    width=300,
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=on_cancel),
                    ft.FilledButton("Aanmaken", on_click=on_save),
                ],
            )
        )

    def _build_template_card(self, template: DayTemplate) -> ft.Card:
        """Build a card for a single day template.

        Args:
            template: The day template to render.

        Returns:
            A Card with apply, edit, and delete actions.
        """
        n = len(template.entries)
        total_min = sum(e.duration_minutes for e in template.entries)
        hours = total_min // 60
        mins = total_min % 60
        subtitle = f"{n} activiteiten · {hours}u {mins}min" if n else "Leeg"
        return ft.Card(
            content=ft.ListTile(
                title=ft.Text(template.name, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(subtitle),
                trailing=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW_OUTLINED,
                            icon_color=ft.Colors.PRIMARY,
                            tooltip="Toepassen op datum",
                            on_click=self._on_apply(template),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=ft.Colors.SECONDARY,
                            tooltip="Bewerken",
                            on_click=self._on_edit(template),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.ERROR,
                            tooltip="Verwijderen",
                            on_click=self._on_delete(template.id),
                        ),
                    ],
                    tight=True,
                    spacing=0,
                ),
            ),
            margin=ft.margin.symmetric(horizontal=8, vertical=4),
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for day templates.

        Returns:
            A ft.View routed to "/day-templates".
        """
        today = date.today()
        self._refresh_tiles()
        content_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.MENU,
                                on_click=lambda _: open_nav_drawer(self._page),
                                icon_size=20,
                            ),
                            ft.Text(
                                "Dag Templates",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=8),
                ),
                ft.Column(
                    controls=[
                        self._tiles_list,
                        ft.Container(
                            content=ft.FilledTonalButton(
                                "Nieuw template",
                                icon=ft.Icons.ADD_OUTLINED,
                                on_click=self._on_create,
                            ),
                            padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        ),
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )
        view = ft.View(
            route="/day-templates",
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
