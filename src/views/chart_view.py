"""Chart view — line chart of total points per day."""

from __future__ import annotations

from datetime import date

import flet as ft
import flet.canvas as cv

from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_rail

_PADDING_LEFT: float = 52.0
_PADDING_RIGHT: float = 16.0
_PADDING_TOP: float = 32.0
_PADDING_BOTTOM: float = 40.0
_DOT_RADIUS: float = 5.0
_HOVER_RADIUS: float = 20.0
_LABEL_FONT_SIZE: float = 10.0
_TOOLTIP_FONT_SIZE: float = 11.0
_AXIS_COLOR: str = ft.Colors.OUTLINE_VARIANT
_LINE_COLOR: str = ft.Colors.PRIMARY
_DOT_COLOR: str = ft.Colors.PRIMARY
_LABEL_COLOR: str = ft.Colors.ON_SURFACE_VARIANT
_TOOLTIP_BG: str = ft.Colors.SURFACE_CONTAINER_HIGH
_TOOLTIP_TEXT: str = ft.Colors.ON_SURFACE


def _group_points_by_date(activities: list) -> dict[date, int]:
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

    Uses the flet.canvas module to draw axes, a polyline, and labelled dots.
    Mouse hover draws a tooltip near the nearest data point.
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

    def _on_hover(self, e: ft.ControlEvent) -> None:
        """Find the nearest data point and draw a tooltip there.

        Args:
            e: Hover event with pointer coordinates.
        """
        ex: float = (
            e.local_x if hasattr(e, "local_x") else getattr(e, "x", 0.0)
        )
        ey: float = (
            e.local_y if hasattr(e, "local_y") else getattr(e, "y", 0.0)
        )
        nearest: tuple[float, float, date, int] | None = None
        min_dist = _HOVER_RADIUS
        for px, py, d, v in self._point_positions:
            dist = ((ex - px) ** 2 + (ey - py) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = (px, py, d, v)
        if nearest != self._active_hover:
            self._active_hover = nearest
            self._redraw()
            self._page.update()

    def _redraw(self) -> None:
        """Rebuild canvas shapes for the base chart plus any active tooltip."""
        self._draw_base(self._last_width, self._last_height)
        if self._active_hover is not None:
            self._draw_tooltip(*self._active_hover)

    def _draw_base(self, width: float, height: float) -> None:
        """Build all base canvas shapes for the line chart.

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

        # Connecting lines
        for i in range(n - 1):
            self._canvas.shapes.append(
                cv.Line(
                    x1=x_pos(i),
                    y1=y_pos(values[i]),
                    x2=x_pos(i + 1),
                    y2=y_pos(values[i + 1]),
                    paint=ft.Paint(color=_LINE_COLOR, stroke_width=2),
                )
            )

        # Dots, x-labels, and hover positions
        label_step = max(1, n // 8)
        for i, (d, v) in enumerate(zip(dates, values)):
            cx = x_pos(i)
            cy = y_pos(v)
            self._point_positions.append((cx, cy, d, v))
            self._canvas.shapes.append(
                cv.Circle(
                    x=cx,
                    y=cy,
                    radius=_DOT_RADIUS,
                    paint=ft.Paint(color=_DOT_COLOR),
                )
            )
            if i % label_step == 0 or i == n - 1:
                self._canvas.shapes.append(
                    cv.Text(
                        x=cx,
                        y=_PADDING_TOP + plot_h + 6,
                        value=d.strftime("%d-%m"),
                        style=ft.TextStyle(
                            size=_LABEL_FONT_SIZE, color=_LABEL_COLOR
                        ),
                        text_align=ft.TextAlign.CENTER,
                    )
                )

        # Y-axis labels: 0 at bottom, max at top
        for val, yp in [(min_val, y_pos(min_val)), (max_val, y_pos(max_val))]:
            self._canvas.shapes.append(
                cv.Text(
                    x=_PADDING_LEFT - 6,
                    y=yp,
                    value=str(val),
                    style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                    text_align=ft.TextAlign.RIGHT,
                )
            )

    def _draw_tooltip(
        self, px: float, py: float, d: date, v: int
    ) -> None:
        """Draw a tooltip bubble near a hovered data point.

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
                on_hover=self._on_hover,
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
                            ft.Text(
                                "Aantal punten per dag",
                                size=20,
                                weight=ft.FontWeight.BOLD,
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

        return ft.View(
            route="/chart",
            padding=0,
            controls=[
                ft.Row(
                    controls=[
                        build_nav_rail(
                            self._page,
                            selected_index=4,
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
