"""Chart view — line chart of total points per day."""

from __future__ import annotations

from datetime import date

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
_HOVER_RADIUS: float = 20.0
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
    """Renders a line chart showing total points per day.

    Uses the flet.canvas module to draw axes, area fill, a polyline, and
    labelled dots with white inner circles. Mouse hover and tap both draw
    a tooltip near the nearest data point.
    Y-axis always starts at 0. Handles empty data gracefully.
    """

    def __init__(self, page: ft.Page, service: ActivityService) -> None:
        """Initialise with page and activity service.

        Args:
            page: The active Flet page.
            service: Service providing access to all activities.
        """
        self._page = page
        self._service = service
        self._points_by_date: dict[date, int] = {}
        self._point_positions: list[tuple[float, float, date, int]] = []
        self._last_width: float = 0.0
        self._last_height: float = 0.0
        self._active_hover: tuple[float, float, date, int] | None = None
        self._canvas = cv.Canvas(
            on_resize=self._on_resize,
            expand=True,
        )

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

    def _handle_pointer(self, x: float, y: float) -> None:
        """Find the nearest data point to (x, y) and trigger a tooltip redraw.

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
        """Delegate tap pointer to the shared handle-pointer logic.

        Args:
            e: TapEvent with local_x and local_y coordinates.
        """
        x: float = getattr(e, "local_x", 0.0)
        y: float = getattr(e, "local_y", 0.0)
        self._handle_pointer(x, y)

    def _redraw(self) -> None:
        """Rebuild canvas shapes for the base chart plus any active tooltip."""
        self._draw_base(self._last_width, self._last_height)
        if self._active_hover is not None:
            self._draw_tooltip(*self._active_hover)

    def _draw_base(self, width: float, height: float) -> None:
        """Build all base canvas shapes for the line chart.

        Draws grid lines, area fill, connecting lines, dots with white
        inner circles, x-axis labels, and y-axis labels.

        Args:
            width: Current canvas width in logical pixels.
            height: Current canvas height in logical pixels.
        """
        self._canvas.shapes = []
        self._point_positions = []

        if not self._points_by_date:
            return

        dates = list(self._points_by_date.keys())
        values = list(self._points_by_date.values())
        n = len(dates)

        plot_w = max(1.0, width - _PADDING_LEFT - _PADDING_RIGHT)
        plot_h = max(1.0, height - _PADDING_TOP - _PADDING_BOTTOM)

        # Y-axis always starts at 0
        min_val = 0
        max_val = max(max(values), 1)

        def x_pos(i: int) -> float:
            if n == 1:
                return _PADDING_LEFT + plot_w / 2
            return _PADDING_LEFT + (i / (n - 1)) * plot_w

        def y_pos(v: int) -> float:
            return _PADDING_TOP + plot_h - (v / max_val) * plot_h

        # "Punten" label — horizontal, above the y-axis
        self._canvas.shapes.append(
            cv.Text(
                x=_PADDING_LEFT - 4,
                y=_PADDING_TOP - 18,
                value="Punten",
                style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                text_align=ft.TextAlign.RIGHT,
            )
        )

        # Axes
        self._canvas.shapes.append(
            cv.Line(
                x1=_PADDING_LEFT,
                y1=_PADDING_TOP + plot_h,
                x2=_PADDING_LEFT + plot_w,
                y2=_PADDING_TOP + plot_h,
                paint=ft.Paint(color=_AXIS_COLOR, stroke_width=1),
            )
        )
        self._canvas.shapes.append(
            cv.Line(
                x1=_PADDING_LEFT,
                y1=_PADDING_TOP,
                x2=_PADDING_LEFT,
                y2=_PADDING_TOP + plot_h,
                paint=ft.Paint(color=_AXIS_COLOR, stroke_width=1),
            )
        )

        # Horizontal grid lines at 25%, 50%, 75%, 100% of max
        for fraction in (0.25, 0.50, 0.75, 1.0):
            grid_y = _PADDING_TOP + plot_h - fraction * plot_h
            self._canvas.shapes.append(
                cv.Line(
                    x1=_PADDING_LEFT,
                    y1=grid_y,
                    x2=_PADDING_LEFT + plot_w,
                    y2=grid_y,
                    paint=ft.Paint(color=_GRID_COLOR, stroke_width=0.5),
                )
            )

        # Area fill under the line
        if n >= 1:
            area_elements: list[cv.Path.PathElement] = [
                cv.Path.MoveTo(x=x_pos(0), y=_PADDING_TOP + plot_h),
                cv.Path.LineTo(x=x_pos(0), y=y_pos(values[0])),
            ]
            for i in range(1, n):
                area_elements.append(cv.Path.LineTo(x=x_pos(i), y=y_pos(values[i])))
            area_elements.append(
                cv.Path.LineTo(x=x_pos(n - 1), y=_PADDING_TOP + plot_h)
            )
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

        # Dots (outer colored + inner white), x-labels, and hover positions
        label_step = max(1, n // 8)
        for i, (d, v) in enumerate(zip(dates, values)):
            cx = x_pos(i)
            cy = y_pos(v)
            self._point_positions.append((cx, cy, d, v))
            # Outer colored circle
            self._canvas.shapes.append(
                cv.Circle(
                    x=cx,
                    y=cy,
                    radius=_DOT_RADIUS,
                    paint=ft.Paint(color=_DOT_COLOR),
                )
            )
            # Inner white circle
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

        # Y-axis labels: 0 at bottom, max//2 in middle, max at top
        mid_val = max_val // 2
        for val in (min_val, mid_val, max_val):
            self._canvas.shapes.append(
                cv.Text(
                    x=_PADDING_LEFT - 6,
                    y=y_pos(val),
                    value=str(val),
                    style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                    text_align=ft.TextAlign.RIGHT,
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
        # Position above-right; flip left if near right edge
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
        self._points_by_date = _group_points_by_date(activities)

        if self._points_by_date:
            chart_area: ft.Control = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.BASIC,
                on_hover=self._on_hover,  # type: ignore[arg-type]
                on_tap_down=self._on_tap_down,
                content=self._canvas,
                expand=True,
            )
        else:
            chart_area = ft.Container(
                content=ft.Text(
                    "Nog geen activiteiten geregistreerd.",
                    color=ft.Colors.OUTLINE,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
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
                                        "Aantal punten per dag",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
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
