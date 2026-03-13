# LeefMeter

A cross-platform activity tracker for Android and iOS built with [Flet](https://flet.dev).
Track daily activities across categories like sport, voeding, mentaal, sociaal, and rust —
and earn points for every logged activity.

---

## Architecture

| Layer | Pattern | Description |
|---|---|---|
| `src/models/` | — | `Activity` and `Day` dataclasses |
| `src/repositories/` | Repository | `ActivityRepository` ABC → `FirebaseRepository`, `InMemoryRepository` |
| `src/services/` | Strategy | `PointCalculationStrategy` ABC → `CategoryPointStrategy`, `DurationPointStrategy`, `CombinedPointStrategy`; `ActivityService` orchestrates CRUD + scoring |
| `src/views/` | — | Flet views: `AgendaView`, `DayView`, `ActivityForm` |
| `src/app.py` | — | Flet entry point with client-side routing |

---

## Project Structure

```
LeefMeter/
├── src/
│   ├── app.py
│   ├── models/
│   │   ├── activity.py       # Activity dataclass
│   │   └── day.py            # Day dataclass with total_points
│   ├── repositories/
│   │   ├── base.py           # ActivityRepository ABC
│   │   ├── firebase_repository.py
│   │   └── in_memory_repository.py
│   ├── services/
│   │   ├── point_strategy.py # Strategy pattern for scoring
│   │   └── activity_service.py
│   └── views/
│       ├── agenda_view.py
│       ├── day_view.py
│       └── activity_form.py
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

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running the App

```bash
python -m src.app
```

---

## Firebase Setup (production)

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com).
2. Enable **Firestore** in your project.
3. Download the service-account key and save it as `firebase_credentials.json` in the project root.
4. In `src/app.py`, replace `InMemoryRepository()` with `FirebaseRepository()`.

> `firebase_credentials.json` is gitignored — never commit it.

---

## Mobile Build

```bash
# Android
flet build apk

# iOS (requires macOS + Xcode)
flet build ipa
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

## Point Calculation

| Strategy | Logic |
|---|---|
| `CategoryPointStrategy` | Fixed points per category (sport=10, mentaal=8, sociaal=6, voeding=5, rust=4) |
| `DurationPointStrategy` | 1 point per 10 minutes of activity |
| `CombinedPointStrategy` | Sum of both (default) |

---

## Code Standards

See [CLAUDE.md](CLAUDE.md) for full coding standards.
