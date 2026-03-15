# LeefMeter

A cross-platform activity tracker for Android, iOS, and desktop built with [Flet](https://flet.dev).

LeefMeter helps you stay aware of how you spend your energy throughout the day. You log activities in 30-minute blocks, each assigned an intensity category. The app calculates a daily point total so you can see at a glance whether your day was balanced or demanding.

The four intensity categories reflect energy load:

| Categorie | Kleur | Punten per 30 min | Bedoeld voor |
|---|---|---|---|
| Rust | Blauw (pastel) | −1 | Slapen, ontspannen, niets doen |
| Laag | Groen (pastel) | +1 | Lichte bezigheden, wandelen |
| Gemiddeld | Amber (pastel) | +2 | Werk, sociale activiteiten |
| Zwaar | Rood (pastel) | +3 | Sport, intensieve concentratie |

A higher total means a more demanding day. Color thresholds on the calendar (green → orange → red) let you spot heavy days at a glance.

---

## Logo

![LeefMeter logo](assets/logo.svg)

The app icon (`icon.png`) is used as the launcher icon when building for Android/iOS.

---

## Architecture

See [`assets/architecture.drawio`](assets/architecture.drawio) for the full diagram (open with [draw.io](https://app.diagrams.net)).

| Layer | Pattern | Description |
|---|---|---|
| `src/models/` | — | `Activity`, `Day`, `Template`, `DayTemplate`, `AppSettings` dataclasses |
| `src/repositories/` | Repository | `ActivityRepository` ABC → `JsonRepository`, `TemplateRepository`, `DayTemplateRepository` |
| `src/services/` | Strategy | `IntensityPointStrategy`; `ActivityService`, `TemplateService`, `DayTemplateService`, `ExportService`, `SettingsService` |
| `src/views/` | — | `HomeView`, `MonthView`, `DayView`, `DayTemplatesView`, `DayTemplateEditView`, `ExportView`, `ChartView`; shared `nav_bar` |
| `src/app.py` | — | Flet entry point with client-side routing |

---

## Project Structure

```
LeefMeter/
├── assets/
│   ├── logo.svg               # App logo
│   └── architecture.drawio   # Architecture diagram
├── src/
│   ├── app.py
│   ├── models/
│   │   ├── activity.py         # Activity dataclass + INTENSITY_LEVELS
│   │   ├── day.py              # Day dataclass with total_points
│   │   ├── settings.py         # AppSettings dataclass
│   │   ├── template.py         # Activity name/category template
│   │   └── day_template.py     # Full-day schedule template
│   ├── repositories/
│   │   ├── base.py             # ActivityRepository ABC
│   │   ├── json_repository.py  # Local JSON storage for activities
│   │   ├── in_memory_repository.py  # In-memory storage (used in tests)
│   │   ├── template_repository.py
│   │   └── day_template_repository.py
│   ├── services/
│   │   ├── point_strategy.py   # IntensityPointStrategy
│   │   ├── activity_service.py
│   │   ├── template_service.py
│   │   ├── day_template_service.py
│   │   ├── export_service.py   # Excel export (all days on one sheet)
│   │   └── settings_service.py # Reads/writes user preferences
│   └── views/
│       ├── month_view.py       # Calendar month with prev/next navigation
│       ├── day_view.py         # Half-hour time grid + day arrows + settings
│       ├── day_templates_view.py     # List/create/delete day templates
│       ├── day_template_edit_view.py # Edit template (same grid as DayView)
│       ├── export_view.py      # Excel export with calendar date range picker
│       ├── home_view.py        # Landing screen with logo, title, intro
│       ├── chart_view.py       # Line chart: points per day (with area fill and tap tooltip)
│       └── nav_bar.py          # Shared dismissible navigation drawer
├── tests/
│   ├── test_models.py
│   ├── test_strategies.py
│   ├── test_repositories.py
│   └── test_activity_service.py
├── pyproject.toml
├── requirements.txt
└── CLAUDE.md
```

---

## Navigation

The app starts on the **Home screen** (`/`) and uses a **dismissible NavigationDrawer** (hamburger icon) to switch between views. Tapping a destination closes the drawer automatically.

| # | Tab | Route | Description |
|---|---|---|---|
| — | Home | `/` | Landing screen with logo, title, and intro. Always shown on startup. |
| 0 | Dag | `/day/<date>` | Half-hour time grid; tap blocks to log activities |
| 1 | Maand | `/month/<year>/<month>` | Calendar overview with color-coded point totals |
| 2 | Templates | `/day-templates` | Save and apply full-day schedule templates |
| 3 | Exporteren | `/export` | Export to Excel with a date range picker |
| 4 | Grafiek | `/chart` | Line chart of total points per day with area fill and tap tooltips |

The drawer header ("LeefMeter" + icon) is also clickable and navigates back to the home screen.

---

## Data Storage

All data is stored **locally on the device** as JSON files. No network connection or cloud account is required.

### Desktop (macOS / Windows / Linux)

Files are saved in your home directory:

```
~/.leefmeter/
├── activities.json      # All logged activities
├── templates.json       # Activity name/category templates
├── day_templates.json   # Full-day schedule templates
└── settings.json        # User preferences (thresholds, day hours)
```

### Android

When built as an APK, Flet stores app data in the app's private internal storage:

```
/data/data/com.leefmeter.app/files/.leefmeter/
```

This directory is only accessible to the app (no root required to use it, but not visible in a standard file browser). Data persists across app restarts and survives updates, but is removed if the app is uninstalled.

### iOS

On iOS, Flet stores data in the app's sandboxed Documents directory:

```
/var/mobile/Containers/Data/Application/<UUID>/Documents/.leefmeter/
```

This data persists across restarts and updates. It can be backed up via iCloud if the user has iCloud Backup enabled.

---

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running the App

```bash
python -m src.app
```

---

## Mobile Build

```bash
# Android (includes app icon)
flet build apk --icon icon.png

# iOS (requires macOS + Xcode + Apple Developer account)
flet build ipa --icon icon.png
```

---

## Development Commands

```bash
black .                          # format code
flake8 .                         # lint
mypy .                           # type check
pydocstyle .                     # docstring check
python -m pytest tests/ -v       # run tests
python -m pytest tests/ --cov    # run tests with coverage
```

Run all checks before committing:

```bash
black . && flake8 . && mypy . && pydocstyle . && python -m pytest tests/ -v
```

---

## Excel Export

The export tab saves to `~/Downloads/leefmeter_export.xlsx`:

- Date range selectable via a calendar date picker
- All days on one **Activiteiten** sheet; each day is a separate table block:
  - Date header (bold)
  - Column headers: Tijd, Naam, Intensiteit, Duur (min), Punten
  - One row per activity
  - A bold **Totaal** row at the bottom
  - A blank separator row before the next day
- A **Categorieën** sheet listing all unique activity names per category

---

## Settings

- **Dag-instellingen** (gear icon in the day view): set the start and end hour of the time grid. Default is 06:00–22:00. Changes apply immediately without restarting.
- **Kleur drempelwaarden** (gear icon in the month view): set the point thresholds for green, orange, and red calendar cells. Default: green ≥ 5, orange ≥ 10, red ≥ 20.

---

## Code Standards

See [CLAUDE.md](CLAUDE.md) for full coding standards.
