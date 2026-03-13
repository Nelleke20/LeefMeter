# LeefMeter

A Python project following strict code quality standards.

---

## Project Structure

```
LeefMeter/
├── src/
│   └── __init__.py
├── tests/
│   └── __init__.py
├── pyproject.toml
├── requirements.txt
├── .flake8
└── CLAUDE.md
```

---

## Setup

```bash
pip install -r requirements.txt
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

## Code Standards

See [CLAUDE.md](CLAUDE.md) for full coding standards including type hints, docstrings, design patterns, and testing conventions.
