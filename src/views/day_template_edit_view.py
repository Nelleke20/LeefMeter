"""Day template edit view — time-grid editor for a day template."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.activity import INTENSITY_LEVELS
from src.models.day_template import DayTemplate, DayTemplateEntry
from src.models.template import Template
from src.services.day_template_service import DayTemplateService
from src.services.template_service import TemplateService
from src.views.nav_bar import build_nav_rail

_START_HOUR: int = 6
_END_HOUR: int = 22
_SLOT_COUNT: int = (_END_HOUR - _START_HOUR) * 2

_CATEGORY_COLORS: dict[str, str] = {
    "rust": ft.Colors.BLUE_200,
    "laag": ft.Colors.LIGHT_GREEN_300,
    "gemiddeld": ft.Colors.AMBER_200,
    "zwaar": ft.Colors.RED_200,
}
_EMPTY_COLOR: str = ft.Colors.SURFACE_CONTAINER
_SELECTED_COLOR: str = ft.Colors.PRIMARY_CONTAINER
_POINTS_PER_SLOT: dict[str, int] = {"rust": -1, "laag": 1, "gemiddeld": 2, "zwaar": 3}

_INTENSITY_LABELS: dict[str, str] = {
    "rust": "Rust (−1 pt / 30 min)",
    "laag": "Laag (+1 pt / 30 min)",
    "gemiddeld": "Gemiddeld (+2 pt / 30 min)",
    "zwaar": "Zwaar (+3 pt / 30 min)",
}
_NEW_ACTIVITY_KEY: str = "__nieuw__"
_NAV_INDEX: int = 2


class DayTemplateEditView:
    """Time-grid editor for a day template — same look and feel as DayView.

    Users tap empty blocks to select them, then add an activity via a dialog.
    Occupied blocks can be tapped to delete. Changes persist immediately.
    """

    def __init__(
        self,
        page: ft.Page,
        template: DayTemplate,
        day_template_service: DayTemplateService,
        template_service: TemplateService,
    ) -> None:
        """Initialise with template and required services.

        Args:
            page: The active Flet page.
            template: The day template being edited.
            day_template_service: Used to persist changes to the template.
            template_service: Used to load and save activity name definitions.
        """
        self._page = page
        self._template = template
        self._dts = day_template_service
        self._ts = template_service
        self._selected_slots: set[int] = set()
        self._slot_containers: list[ft.Container] = []
        self._slot_to_entry: dict[int, DayTemplateEntry] = {}

        self._category_dd = ft.Dropdown(
            label="Categorie",
            options=[
                ft.dropdown.Option(key=lvl, text=_INTENSITY_LABELS[lvl])
                for lvl in INTENSITY_LEVELS
            ],
            border_radius=12,
            on_select=self._on_category_change,
        )
        self._activity_dd = ft.Dropdown(
            label="Activiteit",
            options=[],
            border_radius=12,
            on_select=self._on_activity_change,
        )
        self._new_name_field = ft.TextField(
            label="Naam nieuwe activiteit",
            border_radius=12,
            visible=False,
        )
        self._dialog_error = ft.Text(value="", color=ft.Colors.ERROR)
        self._add_btn = ft.FilledButton(
            "Voeg activiteit toe",
            icon=ft.Icons.ADD,
            on_click=self._on_add_tap,
            visible=False,
        )
        self._slots_list = ft.ListView(expand=True, spacing=2)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _slot_to_time_str(self, slot_idx: int) -> str:
        """Convert a slot index to a "HH:MM" string.

        Args:
            slot_idx: Zero-based half-hour block index.

        Returns:
            Time string like "08:30".
        """
        total = _START_HOUR * 60 + slot_idx * 30
        return f"{total // 60:02d}:{total % 60:02d}"

    def _time_str_to_slot(self, time_str: str) -> int | None:
        """Convert a "HH:MM" string to a slot index.

        Args:
            time_str: Time in "HH:MM" format.

        Returns:
            Slot index, or None if outside the displayed range.
        """
        try:
            h, m = map(int, time_str.split(":"))
            slot = (h * 60 + m - _START_HOUR * 60) // 30
            return slot if 0 <= slot < _SLOT_COUNT else None
        except (ValueError, AttributeError):
            return None

    def _build_slot_to_entry_map(self) -> dict[int, DayTemplateEntry]:
        """Map each occupied slot index to its template entry.

        Returns:
            Dict from slot index to DayTemplateEntry.
        """
        result: dict[int, DayTemplateEntry] = {}
        for entry in self._template.entries:
            start = self._time_str_to_slot(entry.start_time)
            if start is None:
                continue
            for i in range(max(1, entry.duration_minutes // 30)):
                if 0 <= start + i < _SLOT_COUNT:
                    result[start + i] = entry
        return result

    def _slot_color(self, slot_idx: int) -> str:
        """Return background colour for a slot.

        Args:
            slot_idx: Index of the slot.

        Returns:
            A Flet colour string.
        """
        if slot_idx in self._selected_slots:
            return _SELECTED_COLOR
        if slot_idx in self._slot_to_entry:
            cat = self._slot_to_entry[slot_idx].category
            return _CATEGORY_COLORS.get(cat, _EMPTY_COLOR)
        return _EMPTY_COLOR

    def _update_slot_colors(self) -> None:
        """Redraw all slot containers with their current colours."""
        for idx, container in enumerate(self._slot_containers):
            container.bgcolor = self._slot_color(idx)

    # ── in-place refresh ──────────────────────────────────────────────────────

    def _refresh(self) -> None:
        """Rebuild the grid in-place after a change."""
        self._slot_to_entry = self._build_slot_to_entry_map()
        self._slot_containers = []
        self._slots_list.controls = [
            self._build_slot_row(i) for i in range(_SLOT_COUNT)
        ]
        self._selected_slots.clear()
        self._add_btn.visible = False
        self._page.update()

    # ── event handlers ────────────────────────────────────────────────────────

    def _on_slot_tap(self, slot_idx: int) -> Callable[[ft.ControlEvent], None]:
        """Return a click handler for a single time slot.

        Args:
            slot_idx: Index of the tapped slot.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            if slot_idx in self._slot_to_entry:
                self._show_delete_dialog(self._slot_to_entry[slot_idx])
                return
            if slot_idx in self._selected_slots:
                self._selected_slots.remove(slot_idx)
            else:
                self._selected_slots.add(slot_idx)
            self._update_slot_colors()
            self._add_btn.visible = bool(self._selected_slots)
            self._page.update()

        return handler

    def _show_delete_dialog(self, entry: DayTemplateEntry) -> None:
        """Open a confirmation dialog to delete a template entry.

        Args:
            entry: The entry to delete.
        """

        def do_delete(e: ft.ControlEvent) -> None:
            self._template.entries.remove(entry)
            self._dts.update(self._template)
            self._page.pop_dialog()
            self._refresh()

        def cancel(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Verwijder '{entry.activity_name}'?"),
                content=ft.Text(f"{entry.duration_minutes} min · {entry.start_time}"),
                actions=[
                    ft.TextButton("Annuleren", on_click=cancel),
                    ft.FilledButton("Verwijderen", on_click=do_delete),
                ],
            )
        )

    def _on_category_change(self, e: ft.ControlEvent) -> None:
        """Repopulate the activity dropdown when category changes.

        Args:
            e: Select event from the category dropdown.
        """
        templates = self._ts.get_all_templates()
        self._activity_dd.options = [
            ft.dropdown.Option(key=t.name, text=t.name)
            for t in templates
            if t.category == self._category_dd.value
        ] + [ft.dropdown.Option(key=_NEW_ACTIVITY_KEY, text="+ Nieuwe activiteit")]
        self._activity_dd.value = None
        self._new_name_field.visible = False
        self._page.update()

    def _on_activity_change(self, e: ft.ControlEvent) -> None:
        """Show/hide the new-name field.

        Args:
            e: Select event from the activity dropdown.
        """
        self._new_name_field.visible = self._activity_dd.value == _NEW_ACTIVITY_KEY
        self._page.update()

    def _on_add_tap(self, e: ft.ControlEvent) -> None:
        """Open the add-activity dialog for the selected slots.

        Args:
            e: Click event from the add button.
        """
        self._category_dd.value = None
        self._activity_dd.options = []
        self._activity_dd.value = None
        self._new_name_field.value = ""
        self._new_name_field.visible = False
        self._dialog_error.value = ""

        sorted_slots = sorted(self._selected_slots)
        start_time = self._slot_to_time_str(sorted_slots[0])
        duration_minutes = len(sorted_slots) * 30

        def on_save(e: ft.ControlEvent) -> None:
            if not self._category_dd.value:
                self._dialog_error.value = "Kies een categorie."
                self._page.update()
                return
            if not self._activity_dd.value:
                self._dialog_error.value = "Kies een activiteit."
                self._page.update()
                return
            if self._activity_dd.value == _NEW_ACTIVITY_KEY:
                name = (self._new_name_field.value or "").strip()
                if not name:
                    self._dialog_error.value = "Vul een naam in."
                    self._page.update()
                    return
                self._ts.add_template(
                    Template(
                        name=name,
                        category=self._category_dd.value,  # type: ignore[arg-type]
                        duration_minutes=30,
                    )
                )
            else:
                name = self._activity_dd.value  # type: ignore[assignment]
            entry = DayTemplateEntry(
                activity_name=name,
                category=self._category_dd.value,  # type: ignore[arg-type]
                start_time=start_time,
                duration_minutes=duration_minutes,
            )
            self._template.entries.append(entry)
            self._template.entries.sort(key=lambda en: en.start_time)
            self._dts.update(self._template)
            self._page.pop_dialog()
            self._refresh()

        def on_cancel(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Activiteit toevoegen"),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"{start_time}  ·  {duration_minutes} min",
                            color=ft.Colors.PRIMARY,
                        ),
                        self._category_dd,
                        self._activity_dd,
                        self._new_name_field,
                        self._dialog_error,
                    ],
                    spacing=12,
                    tight=True,
                    width=320,
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=on_cancel),
                    ft.FilledButton("Opslaan", on_click=on_save),
                ],
            )
        )

    # ── grid building ─────────────────────────────────────────────────────────

    def _build_slot_row(self, slot_idx: int) -> ft.Row:
        """Build a single row in the time grid.

        Args:
            slot_idx: Index of the half-hour block.

        Returns:
            A Row with a time label and a coloured tap-target block.
        """
        show_label = slot_idx % 2 == 0
        entry = self._slot_to_entry.get(slot_idx)
        content: ft.Control | None = None

        if entry is not None:
            start = self._time_str_to_slot(entry.start_time)
            pts = _POINTS_PER_SLOT.get(entry.category, 0)
            if start == slot_idx:
                content = ft.Row(
                    controls=[
                        ft.Text(
                            entry.activity_name,
                            size=10,
                            color=ft.Colors.ON_SURFACE,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                        ft.Text(
                            f"{pts:+d}pt",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text("✕", size=9, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=4,
                )
            else:
                content = ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.Text(
                            f"{pts:+d}pt",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=4,
                )

        container = ft.Container(
            bgcolor=self._slot_color(slot_idx),
            border_radius=4,
            height=28,
            expand=True,
            on_click=self._on_slot_tap(slot_idx),
            content=content,
            padding=ft.padding.symmetric(horizontal=6) if content else None,
        )
        self._slot_containers.append(container)

        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        self._slot_to_time_str(slot_idx) if show_label else "",
                        size=10,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    width=40,
                    alignment=ft.Alignment(-1, 0),
                ),
                container,
            ],
            spacing=4,
        )

    # ── build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.View:
        """Compose and return the full Flet View for template editing.

        Returns:
            A ft.View routed to "/day-templates/edit/<id>".
        """
        today = date.today()
        self._slot_to_entry = self._build_slot_to_entry_map()
        self._slot_containers = []
        self._slots_list.controls = [
            self._build_slot_row(i) for i in range(_SLOT_COUNT)
        ]

        content_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: self._page.run_task(
                                            self._page.push_route, "/day-templates"
                                        ),
                                    ),
                                    ft.Text(
                                        self._template.name,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                ],
                            ),
                            self._slots_list,
                            self._add_btn,
                        ],
                        expand=True,
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    expand=True,
                ),
            ],
            expand=True,
        )
        return ft.View(
            route=f"/day-templates/edit/{self._template.id}",
            padding=0,
            controls=[
                ft.Row(
                    controls=[
                        build_nav_rail(
                            self._page,
                            selected_index=_NAV_INDEX,
                            year=today.year,
                            month=today.month,
                        ),
                        ft.VerticalDivider(
                            width=1,
                            thickness=1,
                            color=ft.Colors.OUTLINE_VARIANT,
                        ),
                        content_column,
                    ],
                    expand=True,
                    spacing=0,
                )
            ],
        )
