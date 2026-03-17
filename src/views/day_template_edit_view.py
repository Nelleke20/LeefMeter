"""Day template edit view — time-grid editor for a day template."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import flet as ft

from src.models.activity import INTENSITY_LEVELS
from src.models.day_template import DayTemplate, DayTemplateEntry
from src.models.template import Template
from src.services.day_template_service import DayTemplateService
from src.services.settings_service import SettingsService
from src.services.template_service import TemplateService
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

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
_NAV_INDEX: int = 3


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
        settings_service: SettingsService,
    ) -> None:
        """Initialise with template and required services.

        Args:
            page: The active Flet page.
            template: The day template being edited.
            day_template_service: Used to persist changes to the template.
            template_service: Used to load and save activity name definitions.
            settings_service: Used to load day start/end hours.
        """
        self._page = page
        self._template = template
        self._dts = day_template_service
        self._ts = template_service
        settings = settings_service.load()
        self._start_hour: int = settings.day_start_hour
        self._end_hour: int = settings.day_end_hour
        self._slot_count: int = (self._end_hour - self._start_hour) * 2
        self._selected_slots: set[int] = set()
        self._slot_containers: list[ft.Container] = []
        self._slot_to_entry: dict[int, DayTemplateEntry] = {}

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
        total = self._start_hour * 60 + slot_idx * 30
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
            slot = (h * 60 + m - self._start_hour * 60) // 30
            return slot if 0 <= slot < self._slot_count else None
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
                if 0 <= start + i < self._slot_count:
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
            self._build_slot_row(i) for i in range(self._slot_count)
        ]
        self._selected_slots.clear()
        self._add_btn.visible = False
        self._page.update()

    # ── event handlers ────────────────────────────────────────────────────────

    def _on_slot_tap(self, slot_idx: int) -> Callable[[ft.ControlEvent], None]:
        """Return a click handler that toggles slot selection.

        Args:
            slot_idx: Index of the tapped slot.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            if slot_idx in self._selected_slots:
                self._selected_slots.remove(slot_idx)
            else:
                self._selected_slots.add(slot_idx)
            self._update_slot_colors()
            self._add_btn.visible = bool(self._selected_slots)
            self._page.update()

        return handler

    def _on_x_tap(
        self, entry: DayTemplateEntry, slot_idx: int
    ) -> Callable[[ft.ControlEvent], None]:
        """Return a handler for the ✕ icon on an occupied slot.

        Args:
            entry: The template entry occupying this slot.
            slot_idx: Index of the slot whose ✕ was tapped.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            first_slot = self._time_str_to_slot(entry.start_time) or 0
            if first_slot == slot_idx:
                self._show_delete_dialog(entry)
            else:
                self._show_truncate_dialog(entry, slot_idx)

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
                modal=False,
                title=ft.Text(f"Verwijder '{entry.activity_name}'?"),
                content=ft.Text(f"{entry.duration_minutes} min · {entry.start_time}"),
                actions=[
                    ft.TextButton("Annuleren", on_click=cancel),
                    ft.FilledButton("Verwijderen", on_click=do_delete),
                ],
            )
        )

    def _show_truncate_dialog(self, entry: DayTemplateEntry, from_slot: int) -> None:
        """Open a dialog to shorten a template entry from a given slot onward.

        Args:
            entry: The entry to shorten.
            from_slot: The slot index at which truncation begins.
        """
        first_slot = self._time_str_to_slot(entry.start_time) or 0
        new_duration = (from_slot - first_slot) * 30
        remove_duration = entry.duration_minutes - new_duration

        def do_truncate(e: ft.ControlEvent) -> None:
            entry.duration_minutes = new_duration
            self._dts.update(self._template)
            self._page.pop_dialog()
            self._refresh()

        def cancel(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=False,
                title=ft.Text(f"Inkorten '{entry.activity_name}'?"),
                content=ft.Text(
                    f"Verwijder de laatste {remove_duration} min "
                    f"(blijft {new_duration} min)."
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=cancel),
                    ft.FilledButton("Inkorten", on_click=do_truncate),
                ],
            )
        )

    def _on_add_tap(self, e: ft.ControlEvent) -> None:
        """Open the add-activity dialog for the selected slots.

        Creates fresh controls each call so no stale values appear.

        Args:
            e: Click event from the add button.
        """
        sorted_slots = sorted(self._selected_slots)
        start_time = self._slot_to_time_str(sorted_slots[0])
        duration_minutes = len(sorted_slots) * 30

        category_dd = ft.Dropdown(
            label="Categorie",
            options=[
                ft.dropdown.Option(key=lvl, text=_INTENSITY_LABELS[lvl])
                for lvl in INTENSITY_LEVELS
            ],
            border_radius=12,
        )
        activity_scroll = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )
        activity_group = ft.RadioGroup(content=activity_scroll)
        activity_list_box = ft.Container(
            content=activity_group,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=4),
            height=160,
            visible=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
        add_new_btn = ft.TextButton(
            "+ Activiteit toevoegen",
            icon=ft.Icons.ADD,
            visible=False,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def refresh_activity_list() -> None:
            templates = self._ts.get_all_templates()
            activity_scroll.controls = [
                ft.Radio(value=t.name, label=t.name)
                for t in templates
                if t.category == category_dd.value
            ]
            activity_list_box.visible = True
            add_new_btn.visible = True

        def on_category_change(ev: ft.ControlEvent) -> None:
            refresh_activity_list()
            activity_group.value = None
            self._page.update()

        def on_activity_change(ev: ft.ControlEvent) -> None:
            self._page.update()

        def on_add_new_click(ev: ft.ControlEvent) -> None:
            name_field = ft.TextField(
                label="Naam nieuwe activiteit",
                border_radius=12,
                autofocus=True,
            )
            name_error = ft.Text(value="", color=ft.Colors.ERROR)

            def on_add(ev2: ft.ControlEvent) -> None:
                name = (name_field.value or "").strip()
                if not name:
                    name_error.value = "Vul een naam in."
                    self._page.update()
                    return
                self._ts.add_template(
                    Template(
                        name=name,
                        category=category_dd.value,  # type: ignore[arg-type]
                        duration_minutes=30,
                    )
                )
                self._page.pop_dialog()
                refresh_activity_list()
                activity_group.value = name
                self._page.update()

            self._page.show_dialog(
                ft.AlertDialog(
                    modal=False,
                    title=ft.Text("Nieuwe activiteit"),
                    content=ft.Column(
                        controls=[name_field, name_error],
                        spacing=12,
                        tight=True,
                        width=280,
                    ),
                    actions=[
                        ft.FilledButton("Toevoegen", on_click=on_add),
                    ],
                )
            )

        category_dd.on_select = on_category_change
        activity_group.on_change = on_activity_change
        add_new_btn.on_click = on_add_new_click

        def on_save(ev: ft.ControlEvent) -> None:
            if not category_dd.value:
                error_text.value = "Kies een categorie."
                self._page.update()
                return
            if not activity_group.value:
                error_text.value = "Kies een activiteit."
                self._page.update()
                return
            name: str = activity_group.value  # type: ignore[assignment]
            # Remove or trim any existing entries that overlap the selected range
            sorted_slots = sorted(self._selected_slots)
            min_slot = sorted_slots[0]
            max_slot = sorted_slots[-1]
            affected = {
                id(ent): ent
                for s in range(min_slot, max_slot + 1)
                if s in self._slot_to_entry
                for ent in [self._slot_to_entry[s]]
            }
            for ent in affected.values():
                ent_start = self._time_str_to_slot(ent.start_time) or 0
                ent_slots = ent.duration_minutes // 30
                self._template.entries.remove(ent)
                before_count = max(0, min_slot - ent_start)
                if before_count > 0:
                    self._template.entries.append(
                        DayTemplateEntry(
                            activity_name=ent.activity_name,
                            category=ent.category,
                            start_time=self._slot_to_time_str(ent_start),
                            duration_minutes=before_count * 30,
                        )
                    )
                after_start = max_slot + 1
                after_count = max(0, (ent_start + ent_slots) - after_start)
                if after_count > 0:
                    self._template.entries.append(
                        DayTemplateEntry(
                            activity_name=ent.activity_name,
                            category=ent.category,
                            start_time=self._slot_to_time_str(after_start),
                            duration_minutes=after_count * 30,
                        )
                    )
            entry = DayTemplateEntry(
                activity_name=name,
                category=category_dd.value,  # type: ignore[arg-type]
                start_time=start_time,
                duration_minutes=duration_minutes,
            )
            self._template.entries.append(entry)
            self._template.entries.sort(key=lambda en: en.start_time)
            self._dts.update(self._template)
            self._page.pop_dialog()
            self._refresh()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=False,
                title=ft.Text("Activiteit toevoegen"),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"{start_time}  ·  {duration_minutes} min",
                            color=ft.Colors.PRIMARY,
                        ),
                        category_dd,
                        activity_list_box,
                        error_text,
                    ],
                    spacing=12,
                    tight=True,
                    width=320,
                ),
                actions=[
                    add_new_btn,
                    ft.FilledButton("Opslaan", on_click=on_save),
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
                        ft.Container(
                            content=ft.Row(
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
                                ],
                                spacing=4,
                            ),
                            expand=True,
                            on_click=self._on_slot_tap(slot_idx),
                        ),
                        ft.Container(
                            content=ft.Text(
                                "✕", size=9, color=ft.Colors.ON_SURFACE_VARIANT
                            ),
                            on_click=self._on_x_tap(entry, slot_idx),
                            padding=ft.padding.only(left=4, right=2),
                        ),
                    ],
                    spacing=0,
                )
            else:
                content = ft.Row(
                    controls=[
                        ft.Container(
                            expand=True,
                            on_click=self._on_slot_tap(slot_idx),
                        ),
                        ft.Container(
                            content=ft.Text(
                                "✕", size=9, color=ft.Colors.ON_SURFACE_VARIANT
                            ),
                            on_click=self._on_x_tap(entry, slot_idx),
                            padding=ft.padding.only(left=4, right=2),
                        ),
                    ],
                    spacing=0,
                )

        container = ft.Container(
            bgcolor=self._slot_color(slot_idx),
            border_radius=4,
            height=28,
            expand=True,
            on_click=self._on_slot_tap(slot_idx) if entry is None else None,
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
            self._build_slot_row(i) for i in range(self._slot_count)
        ]

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
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: self._page.run_task(
                                            self._page.push_route, "/day-templates"
                                        ),
                                        icon_size=20,
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
        view = ft.View(
            route=f"/day-templates/edit/{self._template.id}",
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
