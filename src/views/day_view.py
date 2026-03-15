"""Day view — interactive time-grid for a single calendar date."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import flet as ft

from src.models.activity import Activity, INTENSITY_LEVELS
from src.models.template import Template
from src.services.activity_service import ActivityService
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


class DayView:
    """Renders a half-hour time grid for one day.

    Tapping empty blocks selects them; the add-activity button then opens
    a dialog to assign category and name. Occupied blocks show colour and
    points and can be tapped to delete. All changes update in-place.
    A gear button lets the user set the day start/end hours.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        template_service: TemplateService,
        day_date: date,
        settings_service: SettingsService,
    ) -> None:
        """Initialise with page, services, target date, and settings.

        Args:
            page: The active Flet page.
            service: Activity CRUD service.
            template_service: Used to load and save activity definitions.
            day_date: The date whose time grid should be displayed.
            settings_service: Service for loading and saving user settings.
        """
        self._page = page
        self._service = service
        self._template_service = template_service
        self._date = day_date
        self._ss = settings_service
        settings = settings_service.load()
        self._start_hour: int = settings.day_start_hour
        self._end_hour: int = settings.day_end_hour
        self._slot_count: int = (self._end_hour - self._start_hour) * 2
        self._selected_slots: set[int] = set()
        self._slot_containers: list[ft.Container] = []
        self._slot_to_activity: dict[int, Activity] = {}

        self._add_btn = ft.FilledButton(
            "Voeg activiteit toe",
            icon=ft.Icons.ADD,
            on_click=self._on_add_tap,
            visible=False,
        )
        self._points_text = ft.Text(
            "",
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PRIMARY,
        )
        self._slots_list = ft.ListView(expand=True, spacing=2)

    # ── helpers ──────────────────────────────────────────────────────────────

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

    def _build_slot_to_activity_map(
        self, activities: list[Activity]
    ) -> dict[int, Activity]:
        """Map each occupied slot index to its activity.

        Args:
            activities: All activities for the day.

        Returns:
            Dict from slot index to Activity.
        """
        result: dict[int, Activity] = {}
        for a in activities:
            if a.start_time is None:
                continue
            start = self._time_str_to_slot(a.start_time)
            if start is None:
                continue
            for i in range(max(1, a.duration_minutes // 30)):
                if 0 <= start + i < self._slot_count:
                    result[start + i] = a
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
        if slot_idx in self._slot_to_activity:
            cat = self._slot_to_activity[slot_idx].category
            return _CATEGORY_COLORS.get(cat, _EMPTY_COLOR)
        return _EMPTY_COLOR

    def _update_slot_colors(self) -> None:
        """Redraw all slot containers with their current colours."""
        for idx, container in enumerate(self._slot_containers):
            container.bgcolor = self._slot_color(idx)

    # ── in-place refresh ─────────────────────────────────────────────────────

    def _refresh(self) -> None:
        """Reload activities and rebuild the grid in-place."""
        day = self._service.get_activities_for_day(self._date)
        self._slot_to_activity = self._build_slot_to_activity_map(day.activities)
        self._slot_containers = []
        self._slots_list.controls = [
            self._build_slot_row(i) for i in range(self._slot_count)
        ]
        self._selected_slots.clear()
        self._add_btn.visible = False
        total = day.total_points
        self._points_text.value = f"{total:+d} pnt"
        self._points_text.color = ft.Colors.ERROR if total < 0 else ft.Colors.PRIMARY
        self._page.update()

    # ── event handlers ────────────────────────────────────────────────────────

    def _on_slot_tap(self, slot_idx: int) -> Callable[[ft.ControlEvent], None]:
        """Return a click handler for a single time slot.

        Tapping the first slot of an activity deletes the whole activity.
        Tapping a later slot truncates the activity up to (not including) that slot.

        Args:
            slot_idx: Index of the tapped slot.

        Returns:
            Sync event handler.
        """

        def handler(e: ft.ControlEvent) -> None:
            if slot_idx in self._slot_to_activity:
                activity = self._slot_to_activity[slot_idx]
                first_slot = self._time_str_to_slot(activity.start_time or "")
                if first_slot == slot_idx:
                    self._show_delete_dialog(activity)
                else:
                    self._show_truncate_dialog(activity, slot_idx)
                return
            if slot_idx in self._selected_slots:
                self._selected_slots.remove(slot_idx)
            else:
                self._selected_slots.add(slot_idx)
            self._update_slot_colors()
            self._add_btn.visible = bool(self._selected_slots)
            self._page.update()

        return handler

    def _show_delete_dialog(self, activity: Activity) -> None:
        """Open a confirmation dialog to delete the whole activity.

        Args:
            activity: The activity to delete.
        """

        def do_delete(e: ft.ControlEvent) -> None:
            self._service.delete_activity(activity.id)
            self._page.pop_dialog()
            self._refresh()

        def cancel(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Verwijder '{activity.name}'?"),
                content=ft.Text(
                    f"{activity.duration_minutes} min · {activity.start_time}"
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=cancel),
                    ft.FilledButton("Verwijderen", on_click=do_delete),
                ],
            )
        )

    def _show_truncate_dialog(self, activity: Activity, from_slot: int) -> None:
        """Open a dialog to truncate an activity from a given slot onward.

        Args:
            activity: The activity to shorten.
            from_slot: The slot index at which to start truncating.
        """
        first_slot = self._time_str_to_slot(activity.start_time or "") or 0
        new_duration = (from_slot - first_slot) * 30
        remove_duration = activity.duration_minutes - new_duration

        def do_truncate(e: ft.ControlEvent) -> None:
            activity.duration_minutes = new_duration
            self._service.update_activity(activity)
            self._page.pop_dialog()
            self._refresh()

        def cancel(e: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Verwijder laatste {remove_duration} min?"),
                content=ft.Text(
                    f"'{activity.name}' wordt ingekort van "
                    f"{activity.duration_minutes} naar {new_duration} min."
                ),
                actions=[
                    ft.TextButton("Annuleren", on_click=cancel),
                    ft.FilledButton("Inkorten", on_click=do_truncate),
                ],
            )
        )

    def _on_add_tap(self, e: ft.ControlEvent) -> None:
        """Open the add-activity dialog for the selected slots.

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
        activity_dd = ft.Dropdown(
            label="Activiteit",
            options=[],
            border_radius=12,
        )
        new_name_field = ft.TextField(
            label="Naam nieuwe activiteit",
            border_radius=12,
            visible=False,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def on_category_change(ev: ft.ControlEvent) -> None:
            templates = self._template_service.get_all_templates()
            activity_dd.options = [
                ft.dropdown.Option(key=t.name, text=t.name)
                for t in templates
                if t.category == category_dd.value
            ] + [ft.dropdown.Option(key=_NEW_ACTIVITY_KEY, text="+ Nieuwe activiteit")]
            activity_dd.value = None
            new_name_field.visible = False
            self._page.update()

        def on_activity_change(ev: ft.ControlEvent) -> None:
            new_name_field.visible = activity_dd.value == _NEW_ACTIVITY_KEY
            self._page.update()

        category_dd.on_select = on_category_change
        activity_dd.on_select = on_activity_change

        def on_save(ev: ft.ControlEvent) -> None:
            if not category_dd.value:
                error_text.value = "Kies een categorie."
                self._page.update()
                return
            if not activity_dd.value:
                error_text.value = "Kies een activiteit."
                self._page.update()
                return
            if activity_dd.value == _NEW_ACTIVITY_KEY:
                name = (new_name_field.value or "").strip()
                if not name:
                    error_text.value = "Vul een naam in."
                    self._page.update()
                    return
                self._template_service.add_template(
                    Template(
                        name=name,
                        category=category_dd.value,  # type: ignore[arg-type]
                        duration_minutes=30,
                    )
                )
            else:
                name = activity_dd.value  # type: ignore[assignment]
            self._service.add_activity(
                Activity(
                    name=name,
                    category=category_dd.value,  # type: ignore[arg-type]
                    duration_minutes=duration_minutes,
                    date=self._date,
                    start_time=start_time,
                )
            )
            self._page.pop_dialog()
            self._refresh()

        def on_cancel(ev: ft.ControlEvent) -> None:
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
                        category_dd,
                        activity_dd,
                        new_name_field,
                        error_text,
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

    # ── drawer ────────────────────────────────────────────────────────────────

    def _open_drawer(self, e: ft.ControlEvent) -> None:
        """Open the navigation drawer.

        Args:
            e: Click event from the menu button.
        """
        open_nav_drawer(self._page)

    # ── settings ──────────────────────────────────────────────────────────────

    def _open_settings(self, e: ft.ControlEvent) -> None:
        """Open a dialog for adjusting the day grid start and end hours.

        Args:
            e: Click event from the settings button.
        """
        settings = self._ss.load()
        start_field = ft.TextField(
            label="Begintijd (uur, 0-23)",
            value=str(settings.day_start_hour),
            border_radius=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=180,
        )
        end_field = ft.TextField(
            label="Eindtijd (uur, 1-24)",
            value=str(settings.day_end_hour),
            border_radius=12,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=180,
        )
        error_text = ft.Text(value="", color=ft.Colors.ERROR)

        def on_save(ev: ft.ControlEvent) -> None:
            try:
                start = int(start_field.value or "6")
                end = int(end_field.value or "22")
            except ValueError:
                error_text.value = "Voer geldige uren in."
                self._page.update()
                return
            if not (0 <= start < end <= 24):
                error_text.value = "Begintijd moet kleiner zijn dan eindtijd (0-24)."
                self._page.update()
                return
            settings.day_start_hour = start
            settings.day_end_hour = end
            self._ss.save(settings)
            self._start_hour = start
            self._end_hour = end
            self._slot_count = (end - start) * 2
            self._page.pop_dialog()
            self._refresh()

        def on_cancel(ev: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Dag-instellingen"),
                content=ft.Column(
                    controls=[start_field, end_field, error_text],
                    spacing=12,
                    tight=True,
                    width=260,
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
        activity = self._slot_to_activity.get(slot_idx)
        content: ft.Control | None = None

        if activity is not None:
            start = self._time_str_to_slot(activity.start_time or "")
            if start == slot_idx:
                content = ft.Row(
                    controls=[
                        ft.Text(
                            activity.name,
                            size=10,
                            color=ft.Colors.ON_SURFACE,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                        ft.Text(
                            f"{activity.points:+d}pt",
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
                        ft.Text("✕", size=9, color=ft.Colors.ON_SURFACE_VARIANT),
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
        """Compose and return the full Flet View for the time grid.

        Returns:
            A ft.View routed to "/day/<date>".
        """
        day = self._service.get_activities_for_day(self._date)
        self._slot_to_activity = self._build_slot_to_activity_map(day.activities)
        self._slot_containers = []
        self._slots_list.controls = [
            self._build_slot_row(i) for i in range(self._slot_count)
        ]
        total = day.total_points
        self._points_text.value = f"{total:+d} pnt"
        self._points_text.color = ft.Colors.ERROR if total < 0 else ft.Colors.PRIMARY

        content_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.MENU,
                                        on_click=self._open_drawer,
                                        icon_size=20,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CHEVRON_LEFT,
                                        on_click=lambda _: self._page.run_task(
                                            self._page.push_route,
                                            "/day/"
                                            + (
                                                self._date - timedelta(days=1)
                                            ).isoformat(),
                                        ),
                                        icon_size=20,
                                    ),
                                    ft.Text(
                                        self._date.strftime("%d %b %Y"),
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    self._points_text,
                                    ft.IconButton(
                                        icon=ft.Icons.SETTINGS_OUTLINED,
                                        tooltip="Tijdinstellingen",
                                        on_click=self._open_settings,
                                        icon_size=20,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CHEVRON_RIGHT,
                                        on_click=lambda _: self._page.run_task(
                                            self._page.push_route,
                                            "/day/"
                                            + (
                                                self._date + timedelta(days=1)
                                            ).isoformat(),
                                        ),
                                        icon_size=20,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
            route=f"/day/{self._date.isoformat()}",
            padding=0,
            controls=[content_column],
        )
        view.drawer = build_nav_drawer(
            self._page,
            selected_index=0,
            year=self._date.year,
            month=self._date.month,
        )
        return view
