"""LeefMeter entry point for flet build (Android / iOS / desktop)."""

from __future__ import annotations

import os
import sys
import traceback

import flet as ft

# Ensure the project root is on sys.path so 'src' is importable on mobile.
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)


async def main(page: ft.Page) -> None:
    """Bootstrap the app, showing a readable error if startup fails.

    Args:
        page: The root Flet page provided by the framework.
    """
    try:
        from src.app import main as _app_main

        await _app_main(page)
    except Exception:
        page.controls.clear()
        page.add(
            ft.Text(
                traceback.format_exc(),
                color=ft.Colors.ERROR,
                size=10,
                selectable=True,
            )
        )
        page.update()


ft.run(main)
