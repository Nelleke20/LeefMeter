"""Chart view — scrollable 30-day line chart of total points per day."""

from __future__ import annotations

from datetime import date, timedelta

import flet as ft
import flet.canvas as cv

from src.models.activity import Activity
from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_drawer, open_nav_drawer

_PADDING_LEFT: float = 52.0
_PADDING_RIGHT: float = 16.0
_PADDING_TOP: float = 32.0
_PADDING_BOTTOM: float = 40.0
_DOT_RADIUS: float = 6.0
_DOT_INNER_RADIUS: float = 3.0
_HOVER_RADIUS: float = 40.0
_Y_MIN: int = -5
_Y_MAX: int = 40
_WINDOW_DAYS: int = 30  # total days shown at once
_DAYS_BEFORE: int = 15  # days before center date
_DAYS_AFTER: int = 14  # days after center date
_PAN_THRESHOLD: float = 12.0  # px of drag before shifting window
_LABEL_FONT_SIZE: float = 10.0
_TOOLTIP_FONT_SIZE: float = 11.0
_AXIS_COLOR: str = ft.Colors.OUTLINE_VARIANT
_LINE_COLOR: str = ft.Colors.PRIMARY
_DOT_COLOR: str = ft.Colors.PRIMARY
_DOT_INNER_COLOR: str = ft.Colors.SURFACE
_LABEL_COLOR: str = ft.Colors.ON_SURFACE_VARIANT
_TOOLTIP_BG: str = ft.Colors.SURFACE_CONTAINER_HIGH
_TOOLTIP_TEXT: str = ft.Colors.ON_SURFACE
_AREA_COLOR: str = ft.Colors.PRIMARY_CONTAINER
_GRID_COLOR: str = ft.Colors.OUTLINE_VARIANT
_TODAY_DOT_COLOR: str = ft.Colors.TERTIARY


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
    """Renders a scrollable 30-day line chart showing total points per day.

    The window is always 30 days wide (15 before, 14 after the centre date).
    Swipe/drag left to move forward in time, right to go back.
    Days with no activities show as 0. Today's dot is highlighted.
    """

    def __init__(self, page: ft.Page, service: ActivityService) -> None:
        """Initialise with page and activity service.

        Args:
            page: The active Flet page.
            service: Service providing access to all activities.
        """
        self._page = page
        self._service = service
        self._all_points: dict[date, int] = {}
        self._point_positions: list[tuple[float, float, date, int]] = []
        self._last_width: float = 0.0
        self._last_height: float = 0.0
        self._active_hover: tuple[float, float, date, int] | None = None
        self._center_date: date = date.today()
        self._drag_accumulated: float = 0.0
        self._canvas = cv.Canvas(
            on_resize=self._on_resize,
            expand=True,
        )

    # ── window helpers ──────────────────────────────────────────────────────

    def _window_dates(self) -> list[date]:
        """Return the list of 30 dates in the current window.

        Returns:
            Dates from center - 15 days to center + 14 days inclusive.
        """
        start = self._center_date - timedelta(days=_DAYS_BEFORE)
        return [start + timedelta(days=i) for i in range(_WINDOW_DAYS)]

    # ── resize ──────────────────────────────────────────────────────────────

    def _on_resize(self, e: cv.CanvasResizeEvent) -> None:
        """Redraw the chart whenever the canvas is resized.

        Args:
            e: Resize event containing the new canvas dimensions.
        """
        self._last_width = e.width
        self._last_height = e.height
        self._active_hover = None
        self._redraw()
        self._page.update()

    # ── pointer / drag ──────────────────────────────────────────────────────

    def _handle_pointer(self, x: float, y: float) -> None:
        """Find the nearest data point to (x, y) and show a tooltip.

        Args:
            x: Pointer x coordinate in canvas-local pixels.
            y: Pointer y coordinate in canvas-local pixels.
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
        """Delegate hover pointer to the shared handle-pointer logic.

        Args:
            e: Hover event with pointer coordinates.
        """
        ex: float = e.local_x if hasattr(e, "local_x") else getattr(e, "x", 0.0)
        ey: float = e.local_y if hasattr(e, "local_y") else getattr(e, "y", 0.0)
        self._handle_pointer(ex, ey)

    def _on_tap_down(self, e: ft.TapEvent) -> None:  # type: ignore[type-arg]
        """Show tooltip at tapped position.

        Args:
            e: TapEvent with local_x and local_y coordinates.
        """
        self._drag_accumulated = 0.0
        self._handle_pointer(e.local_x, e.local_y)

    def _on_tap(self, e: ft.ControlEvent) -> None:
        """Clear the active tooltip on tap.

        Args:
            e: Tap event.
        """
        self._active_hover = None
        self._redraw()
        self._page.update()

    def _on_long_press_start(self, e: ft.ControlEvent) -> None:
        """Show tooltip on long press (mobile alternative to hover).

        Args:
            e: Long-press-start event with local_x and local_y.
        """
        x: float = getattr(e, "local_x", 0.0)
        y: float = getattr(e, "local_y", 0.0)
        self._handle_pointer(x, y)

    def _on_pan_update(self, e: ft.DragUpdateEvent) -> None:
        """Shift the chart window left or right on horizontal drag.

        Dragging right moves the window backward in time; left moves forward.

        Args:
            e: Drag update event with delta_x.
        """
        dx: float = getattr(e, "delta_x", 0.0)
        self._drag_accumulated += dx
        step = (self._last_width - _PADDING_LEFT - _PADDING_RIGHT) / _WINDOW_DAYS
        threshold = max(step, _PAN_THRESHOLD)
        if abs(self._drag_accumulated) >= threshold:
            days = -int(self._drag_accumulated / threshold)
            self._center_date += timedelta(days=days)
            self._drag_accumulated = 0.0
            self._active_hover = None
            self._redraw()
            self._page.update()

    # ── drawing ─────────────────────────────────────────────────────────────

    def _redraw(self) -> None:
        """Rebuild canvas shapes for the base chart plus any active tooltip."""
        self._draw_base(self._last_width, self._last_height)
        if self._active_hover is not None:
            self._draw_tooltip(*self._active_hover)

    def _draw_base(self, width: float, height: float) -> None:
        """Build all base canvas shapes for the line chart.

        Always draws exactly _WINDOW_DAYS columns. Days without activities
        are shown as 0. Today's dot is highlighted in a tertiary colour.

        Args:
            width: Current canvas width in logical pixels.
            height: Current canvas height in logical pixels.
        """
        self._canvas.shapes = []
        self._point_positions = []

        today = date.today()
        dates = self._window_dates()
        n = len(dates)
        values = [self._all_points.get(d, 0) for d in dates]

        plot_w = max(1.0, width - _PADDING_LEFT - _PADDING_RIGHT)
        plot_h = max(1.0, height - _PADDING_TOP - _PADDING_BOTTOM)
        y_range = _Y_MAX - _Y_MIN

        def x_pos(i: int) -> float:
            return _PADDING_LEFT + (i / (n - 1)) * plot_w

        def y_pos(v: int) -> float:
            frac = (v - _Y_MIN) / y_range
            return _PADDING_TOP + plot_h - frac * plot_h

        # "Punten" label
        self._canvas.shapes.append(
            cv.Text(
                x=_PADDING_LEFT - 4,
                y=_PADDING_TOP - 18,
                value="Punten",
                style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                text_align=ft.TextAlign.RIGHT,
            )
        )

        # Y-axis
        self._canvas.shapes.append(
            cv.Line(
                x1=_PADDING_LEFT,
                y1=_PADDING_TOP,
                x2=_PADDING_LEFT,
                y2=_PADDING_TOP + plot_h,
                paint=ft.Paint(color=_AXIS_COLOR, stroke_width=1),
            )
        )

        # X-axis at y=0
        self._canvas.shapes.append(
            cv.Line(
                x1=_PADDING_LEFT,
                y1=y_pos(0),
                x2=_PADDING_LEFT + plot_w,
                y2=y_pos(0),
                paint=ft.Paint(color=_AXIS_COLOR, stroke_width=1),
            )
        )

        # Horizontal grid lines + y-axis labels at fixed ticks
        for tick in (_Y_MIN, 0, 10, 20, 30, _Y_MAX):
            gy = y_pos(tick)
            sw = 1.0 if tick == 0 else 0.5
            self._canvas.shapes.append(
                cv.Line(
                    x1=_PADDING_LEFT,
                    y1=gy,
                    x2=_PADDING_LEFT + plot_w,
                    y2=gy,
                    paint=ft.Paint(color=_GRID_COLOR, stroke_width=sw),
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

        # Area fill anchored at zero line
        zero_y = y_pos(0)
        area_elements: list[cv.Path.PathElement] = [
            cv.Path.MoveTo(x=x_pos(0), y=zero_y),
            cv.Path.LineTo(x=x_pos(0), y=y_pos(values[0])),
        ]
        for i in range(1, n):
            area_elements.append(cv.Path.LineTo(x=x_pos(i), y=y_pos(values[i])))
        area_elements.append(cv.Path.LineTo(x=x_pos(n - 1), y=zero_y))
        area_elements.append(cv.Path.Close())
        self._canvas.shapes.append(
            cv.Path(
                elements=area_elements,
                paint=ft.Paint(
                    color=_AREA_COLOR,
                    style=ft.PaintingStyle.FILL,
                ),
            )
        )

        # Connecting lines
        for i in range(n - 1):
            self._canvas.shapes.append(
                cv.Line(
                    x1=x_pos(i),
                    y1=y_pos(values[i]),
                    x2=x_pos(i + 1),
                    y2=y_pos(values[i + 1]),
                    paint=ft.Paint(color=_LINE_COLOR, stroke_width=2.5),
                )
            )

        # Dots, x-labels, hover positions
        label_step = max(1, n // 6)
        for i, (d, v) in enumerate(zip(dates, values)):
            cx = x_pos(i)
            cy = y_pos(v)
            self._point_positions.append((cx, cy, d, v))
            dot_color = _TODAY_DOT_COLOR if d == today else _DOT_COLOR
            self._canvas.shapes.append(
                cv.Circle(
                    x=cx,
                    y=cy,
                    radius=_DOT_RADIUS,
                    paint=ft.Paint(color=dot_color),
                )
            )
            self._canvas.shapes.append(
                cv.Circle(
                    x=cx,
                    y=cy,
                    radius=_DOT_INNER_RADIUS,
                    paint=ft.Paint(color=_DOT_INNER_COLOR),
                )
            )
            if i % label_step == 0 or i == n - 1:
                self._canvas.shapes.append(
                    cv.Text(
                        x=cx,
                        y=_PADDING_TOP + plot_h + 6,
                        value=d.strftime("%d-%m"),
                        style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                        text_align=ft.TextAlign.CENTER,
                    )
                )

    def _draw_tooltip(self, px: float, py: float, d: date, v: int) -> None:
        """Draw a tooltip bubble near a hovered or tapped data point.

        Args:
            px: X position of the data point.
            py: Y position of the data point.
            d: Date of the data point.
            v: Point value of the data point.
        """
        label = f"{d.strftime('%d-%m-%Y')}  {v:+d} pt"
        pad = 6.0
        box_w = 130.0
        box_h = 22.0
        tx = px + 10
        if self._last_width > 0 and tx + box_w > self._last_width - _PADDING_RIGHT:
            tx = px - box_w - 10
        ty = py - box_h - 6

        self._canvas.shapes.append(
            cv.Rect(
                x=tx,
                y=ty,
                width=box_w,
                height=box_h,
                border_radius=4,
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
        activities = self._service._repository.get_all()
        self._all_points = _group_points_by_date(activities)

        chart_area: ft.Control = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.BASIC,
            on_hover=self._on_hover,  # type: ignore[arg-type]
            on_tap_down=self._on_tap_down,
            on_tap=self._on_tap,
            on_long_press_start=self._on_long_press_start,  # type: ignore[arg-type]
            on_pan_update=self._on_pan_update,  # type: ignore[arg-type]
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
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.TODAY,
                                        tooltip="Ga naar vandaag",
                                        on_click=(  # type: ignore[arg-type]
                                            self._go_to_today
                                        ),
                                        icon_size=20,
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
                    padding=ft.padding.symmetric(horizontal=8, vertical=12),
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

    def _go_to_today(self, e: ft.ControlEvent) -> None:
        """Reset the chart window to centre on today.

        Args:
            e: Click event from the today button.
        """
        self._center_date = date.today()
        self._active_hover = None
        self._redraw()
        self._page.update()
