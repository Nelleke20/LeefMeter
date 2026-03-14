"""Chart view — line chart of total points per day."""

from __future__ import annotations

from datetime import date

import flet as ft
import flet.canvas as cv

from src.services.activity_service import ActivityService
from src.views.nav_bar import build_nav_rail

_PADDING_LEFT: float = 48.0
_PADDING_RIGHT: float = 16.0
_PADDING_TOP: float = 16.0
_PADDING_BOTTOM: float = 40.0
_DOT_RADIUS: float = 5.0
_HOVER_RADIUS: float = 20.0
_LABEL_FONT_SIZE: float = 10.0
_AXIS_COLOR: str = ft.Colors.OUTLINE_VARIANT
_LINE_COLOR: str = ft.Colors.PRIMARY
_DOT_COLOR: str = ft.Colors.PRIMARY
_LABEL_COLOR: str = ft.Colors.ON_SURFACE_VARIANT


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
    Mouse hover shows the date and points for the nearest data point.
    Handles empty data gracefully by showing a message instead of a chart.
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
        self._tooltip = ft.Text(
            "",
            size=12,
            color=ft.Colors.ON_SURFACE,
            text_align=ft.TextAlign.CENTER,
        )
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
        self._draw(e.width, e.height)
        self._page.update()

    def _on_hover(self, e: ft.HoverEvent) -> None:
        """Update the tooltip when the mouse moves over the chart area.

        Args:
            e: Hover event with local x/y coordinates.
        """
        nearest: tuple[date, int] | None = None
        min_dist = _HOVER_RADIUS
        for px, py, d, v in self._point_positions:
            dist = ((e.local_x - px) ** 2 + (e.local_y - py) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = (d, v)
        self._tooltip.value = (
            f"{nearest[0].strftime('%d-%m-%Y')}  ·  {nearest[1]:+d} punten"
            if nearest
            else ""
        )
        self._page.update()

    def _draw(self, width: float, height: float) -> None:
        """Build all canvas shapes for the line chart.

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

        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val if max_val != min_val else 1

        def x_pos(i: int) -> float:
            if n == 1:
                return _PADDING_LEFT + plot_w / 2
            return _PADDING_LEFT + (i / (n - 1)) * plot_w

        def y_pos(v: int) -> float:
            return _PADDING_TOP + plot_h - ((v - min_val) / val_range) * plot_h

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
                        style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                        text_align=ft.TextAlign.CENTER,
                    )
                )

        # Y-axis labels (min and max)
        for val, yp in [(min_val, y_pos(min_val)), (max_val, y_pos(max_val))]:
            self._canvas.shapes.append(
                cv.Text(
                    x=_PADDING_LEFT - 4,
                    y=yp,
                    value=str(val),
                    style=ft.TextStyle(size=_LABEL_FONT_SIZE, color=_LABEL_COLOR),
                    text_align=ft.TextAlign.RIGHT,
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
                alignment=ft.alignment.center,
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
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(
                                            "Punten",
                                            size=11,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            rotate=-1.5708,
                                        ),
                                        width=20,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Container(
                                        content=chart_area,
                                        expand=True,
                                    ),
                                ],
                                expand=True,
                                spacing=0,
                            ),
                            self._tooltip,
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
