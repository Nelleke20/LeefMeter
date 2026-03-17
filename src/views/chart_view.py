"""Chart view — 30-day bar chart of total points per day."""

from __future__ import annotations

from datetime import date, timedelta

import flet as ft
import flet.canvas as cv

from src.models.activity import Activity
from src.models.settings import AppSettings
from src.services.activity_service import ActivityService
from src.services.settings_service import SettingsService
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_PADDING_LEFT: float = 28.0
_PADDING_RIGHT: float = 38.0
_PADDING_TOP: float = 24.0
_PADDING_BOTTOM: float = 48.0
_DOT_RADIUS: float = 5.0
_HOVER_RADIUS: float = 40.0
_Y_MIN: int = -5
_Y_MAX: int = 40
_DAYS_BEFORE: int = 29
_WINDOW_DAYS: int = _DAYS_BEFORE + 1
_LABEL_FONT_SIZE: float = 11.0
_TOOLTIP_FONT_SIZE: float = 11.0
_AXIS_COLOR: str = ft.Colors.OUTLINE_VARIANT
_LINE_COLOR: str = ft.Colors.PRIMARY
_LABEL_COLOR: str = ft.Colors.ON_SURFACE_VARIANT
_TOOLTIP_BG: str = ft.Colors.SURFACE_CONTAINER_HIGH
_TOOLTIP_TEXT: str = ft.Colors.ON_SURFACE
_TODAY_COLOR: str = ft.Colors.TERTIARY

# Threshold band colours — very subtle, nearly transparent
_COLOR_BLUE: str = ft.Colors.with_opacity(0.08, ft.Colors.BLUE)
_COLOR_GREEN: str = ft.Colors.with_opacity(0.10, ft.Colors.GREEN)
_COLOR_ORANGE: str = ft.Colors.with_opacity(0.10, ft.Colors.ORANGE)
_COLOR_RED: str = ft.Colors.with_opacity(0.10, ft.Colors.RED)


def _group_points_by_date(activities: list[Activity]) -> dict[date, int]:
    """Aggregate total points per calendar date.

    Args:
        activities: All Activity objects to aggregate.

    Returns:
        A dict mapping each date to its summed points, sorted ascending.
    """
    totals: dict[date, int] = {}
    for activity in activities:
        totals[activity.date] = totals.get(activity.date, 0) + activity.points
    return dict(sorted(totals.items()))


class ChartView:
    """Renders a 30-day bar+line chart (today and 29 preceding days).

    Background bands reflect the same colour thresholds as the month view.
    Each data point is coloured by threshold. A tooltip appears on tap/hover.
    """

    def __init__(
        self,
        page: ft.Page,
        service: ActivityService,
        settings_service: SettingsService,
    ) -> None:
        """Initialise with page, activity service, and settings service.

        Args:
            page: The active Flet page.
            service: Service providing access to all activities.
            settings_service: Service for loading colour thresholds.
        """
        self._page = page
        self._service = service
        self._settings_service = settings_service
        self._settings: AppSettings = settings_service.load()
        self._all_points: dict[date, int] = {}
        self._point_positions: list[tuple[float, float, date, int]] = []
        self._last_width: float = 0.0
        self._last_height: float = 0.0
        self._active_hover: tuple[float, float, date, int] | None = None
        self._canvas = cv.Canvas(
            on_resize=self._on_resize,
            expand=True,
        )

    def _window_dates(self) -> list[date]:
        """Return the 30-day window ending today.

        Returns:
            List of dates from today-29 to today inclusive.
        """
        today = date.today()
        return [today - timedelta(days=_DAYS_BEFORE - i) for i in range(_WINDOW_DAYS)]

    def _dot_color(self, v: int) -> str:
        """Return a colour for a data point based on threshold settings.

        Args:
            v: The point value for the day.

        Returns:
            A Flet colour string.
        """
        s = self._settings
        if v >= s.red_threshold:
            return _COLOR_RED
        if v >= s.orange_threshold:
            return _COLOR_ORANGE
        if v >= s.green_threshold:
            return _COLOR_GREEN
        return _COLOR_BLUE

    def _on_resize(self, e: cv.CanvasResizeEvent) -> None:
        """Redraw on canvas resize.

        Args:
            e: Resize event with new dimensions.
        """
        self._last_width = e.width
        self._last_height = e.height
        self._active_hover = None
        self._redraw()
        self._page.update()

    def _handle_pointer(self, x: float, y: float) -> None:
        """Show tooltip for the nearest data point within hover radius.

        Args:
            x: Pointer x in canvas-local pixels.
            y: Pointer y in canvas-local pixels.
        """
        nearest: tuple[float, float, date, int] | None = None
        min_dist = _HOVER_RADIUS
        for px, py, d, v in self._point_positions:
            dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = (px, py, d, v)
        if nearest != self._active_hover:
            self._active_hover = nearest
            self._redraw()
            self._page.update()

    def _on_hover(self, e: ft.ControlEvent) -> None:
        """Handle mouse hover.

        Args:
            e: Hover event with pointer coordinates.
        """
        ex: float = e.local_x if hasattr(e, "local_x") else getattr(e, "x", 0.0)
        ey: float = e.local_y if hasattr(e, "local_y") else getattr(e, "y", 0.0)
        self._handle_pointer(ex, ey)

    def _on_tap_down(self, e: ft.TapEvent) -> None:  # type: ignore[type-arg]
        """Handle tap on mobile.

        Args:
            e: Tap event with coordinates.
        """
        x: float = getattr(e, "local_x", None) or getattr(e, "x", 0.0)
        y: float = getattr(e, "local_y", None) or getattr(e, "y", 0.0)
        self._handle_pointer(x, y)

    def _on_tap(self, e: ft.ControlEvent) -> None:
        """Clear tooltip on second tap.

        Args:
            e: Tap event.
        """
        if self._active_hover is not None:
            self._active_hover = None
            self._redraw()
            self._page.update()

    def _on_long_press_start(self, e: ft.ControlEvent) -> None:
        """Show tooltip on long press.

        Args:
            e: Long-press event with coordinates.
        """
        x: float = getattr(e, "local_x", 0.0)
        y: float = getattr(e, "local_y", 0.0)
        self._handle_pointer(x, y)

    def _redraw(self) -> None:
        """Rebuild all canvas shapes."""
        self._draw_base(self._last_width, self._last_height)
        if self._active_hover is not None:
            self._draw_tooltip(*self._active_hover)

    def _draw_base(self, width: float, height: float) -> None:
        """Draw background bands, axes, grid, bars, and line.

        Args:
            width: Canvas width in logical pixels.
            height: Canvas height in logical pixels.
        """
        self._canvas.shapes = []
        self._point_positions = []

        today = date.today()
        dates = self._window_dates()
        n = len(dates)
        s = self._settings

        plot_w = max(1.0, width - _PADDING_LEFT - _PADDING_RIGHT)
        plot_h = max(1.0, height - _PADDING_TOP - _PADDING_BOTTOM)
        y_range = _Y_MAX - _Y_MIN

        def x_pos(i: int) -> float:
            return _PADDING_LEFT + (i / (n - 1)) * plot_w

        def y_pos(v: float) -> float:
            frac = (v - _Y_MIN) / y_range
            return _PADDING_TOP + plot_h - frac * plot_h

        # ── Background colour bands (matching month-view thresholds) ──────────
        bands = [
            (_Y_MIN, 0, _COLOR_BLUE),
            (0, s.green_threshold, _COLOR_BLUE),
            (s.green_threshold, s.orange_threshold, _COLOR_GREEN),
            (s.orange_threshold, s.red_threshold, _COLOR_ORANGE),
            (s.red_threshold, _Y_MAX, _COLOR_RED),
        ]
        for band_lo, band_hi in [
            (b[0], b[1]) for b in bands
        ]:
            band_color = next(c for lo, hi, c in bands if lo == band_lo and hi == band_hi)
            by_top = y_pos(min(band_hi, _Y_MAX))
            by_bot = y_pos(max(band_lo, _Y_MIN))
            if by_bot > by_top:
                self._canvas.shapes.append(
                    cv.Rect(
                        x=_PADDING_LEFT,
                        y=by_top,
                        width=plot_w,
                        height=by_bot - by_top,
                        paint=ft.Paint(color=band_color, style=ft.PaintingStyle.FILL),
                    )
                )

        # ── Y-axis ────────────────────────────────────────────────────────────
        self._canvas.shapes.append(
            cv.Line(
                x1=_PADDING_LEFT,
                y1=_PADDING_TOP,
                x2=_PADDING_LEFT,
                y2=_PADDING_TOP + plot_h,
                paint=ft.Paint(color=_AXIS_COLOR, stroke_width=1),
            )
        )

        # ── Grid lines + labels ───────────────────────────────────────────────
        for tick in (_Y_MIN, 0, s.green_threshold, s.orange_threshold, s.red_threshold, _Y_MAX):
            gy = y_pos(tick)
            sw = 1.2 if tick == 0 else 0.5
            self._canvas.shapes.append(
                cv.Line(
                    x1=_PADDING_LEFT,
                    y1=gy,
                    x2=_PADDING_LEFT + plot_w,
                    y2=gy,
                    paint=ft.Paint(color=_AXIS_COLOR, stroke_width=sw),
                )
            )
            self._canvas.shapes.append(
                cv.Text(
                    x=_PADDING_LEFT - 6,
                    y=gy,
                    value=str(tick),
                    style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                    text_align=ft.TextAlign.RIGHT,
                )
            )

        data_points = [
            (i, d, self._all_points[d])
            for i, d in enumerate(dates)
            if d in self._all_points
        ]

        # ── Data points (position tracking for tooltip) ───────────────────────
        for i, d, v in data_points:
            self._point_positions.append((x_pos(i), y_pos(v), d, v))

        # ── Line connecting data points ───────────────────────────────────────
        for k in range(len(data_points) - 1):
            i0, d0, v0 = data_points[k]
            i1, d1, v1 = data_points[k + 1]
            if (d1 - d0).days == 1:
                self._canvas.shapes.append(
                    cv.Line(
                        x1=x_pos(i0),
                        y1=y_pos(v0),
                        x2=x_pos(i1),
                        y2=y_pos(v1),
                        paint=ft.Paint(color=_LINE_COLOR, stroke_width=2.0),
                    )
                )

        # ── Dots at each data point ───────────────────────────────────────────
        for i, d, v in data_points:
            color = ft.Colors.RED if d == today else ft.Colors.BLACK
            self._canvas.shapes.append(
                cv.Circle(
                    x=x_pos(i),
                    y=y_pos(v),
                    radius=3.0,
                    paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL),
                )
            )

        # ── X-axis date labels ────────────────────────────────────────────────
        label_step = max(1, n // 6)
        for i, d in enumerate(dates):
            if i % label_step == 0 or i == n - 1:
                self._canvas.shapes.append(
                    cv.Text(
                        x=x_pos(i),
                        y=_PADDING_TOP + plot_h + 14,
                        value=d.strftime("%d-%m"),
                        style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                        text_align=ft.TextAlign.CENTER,
                    )
                )

        # ── Hover vertical line ───────────────────────────────────────────────
        if self._active_hover is not None:
            hx = self._active_hover[0]
            self._canvas.shapes.append(
                cv.Line(
                    x1=hx,
                    y1=_PADDING_TOP,
                    x2=hx,
                    y2=_PADDING_TOP + plot_h,
                    paint=ft.Paint(
                        color=ft.Colors.ON_SURFACE_VARIANT, stroke_width=1
                    ),
                )
            )

    def _draw_tooltip(self, px: float, py: float, d: date, v: int) -> None:
        """Draw a tooltip near a hovered or tapped data point.

        Args:
            px: X position of the data point.
            py: Y position of the data point.
            d: Date of the data point.
            v: Point value.
        """
        label = f"{d.strftime('%d-%m-%Y')}  {v:+d} pt"
        pad = 6.0
        box_w = 138.0
        box_h = 24.0
        tx = px + 10
        if self._last_width > 0 and tx + box_w > self._last_width - _PADDING_RIGHT:
            tx = px - box_w - 10
        ty = py - box_h - 8
        if ty < _PADDING_TOP:
            ty = py + 8
        self._canvas.shapes.append(
            cv.Rect(
                x=tx,
                y=ty,
                width=box_w,
                height=box_h,
                border_radius=6,
                paint=ft.Paint(color=_TOOLTIP_BG),
            )
        )
        self._canvas.shapes.append(
            cv.Text(
                x=tx + pad,
                y=ty + pad,
                value=label,
                style=ft.TextStyle(size=_TOOLTIP_FONT_SIZE, color=_TOOLTIP_TEXT),
            )
        )

    def build(self) -> ft.View:
        """Compose and return the full Flet View for the chart.

        Returns:
            A ft.View routed to "/chart".
        """
        today = date.today()
        self._settings = self._settings_service.load()
        activities = self._service._repository.get_all()
        self._all_points = _group_points_by_date(activities)

        chart_area: ft.Control = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.BASIC,
            on_hover=self._on_hover,  # type: ignore[arg-type]
            on_tap_down=self._on_tap_down,
            on_tap=self._on_tap,
            on_long_press_start=self._on_long_press_start,  # type: ignore[arg-type]
            content=self._canvas,
            expand=True,
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
                                        "Punten per dag",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                        text_align=ft.TextAlign.LEFT,
                                    ),
                                ],
                            ),
                            ft.Container(
                                content=chart_area,
                                expand=True,
                            ),
                        ],
                        expand=True,
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=8),
                    expand=True,
                ),
            ],
            expand=True,
        )

        view = ft.View(
            route="/chart",
            padding=0,
            controls=[content_column],
        )
        view.drawer = build_nav_drawer(
            self._page,
            selected_index=4,
            year=today.year,
            month=today.month,
        )
        return view
