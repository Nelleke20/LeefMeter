# Python Project — Claude Code Standards

## Philosophy
- Simple over complex.

- Readable over clever. If a junior developer can't understand it in 30 seconds, simplify it.

- Always run the unittest before pushing code to a branch.

-A lways adjust the readme based on new code changes.

- Make a prompt file where all my prompt instructions are automatically saved and analyzed when running code just like the claud.md file. 
This way if i start a new session my history can be analyzed.
---

## Commands

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

## Code Style

- **Formatter:** Black (line length 88). Never argue with Black — just run it.
- **Linter:** Flake8. Fix all warnings, no `# noqa` shortcuts unless truly unavoidable.
- **Types:** Mypy strict mode. Every function must have full type hints.
- **Docs:** Pydocstyle with Google-style docstrings. Every public function, class, and module needs one.

---

## Type Hints — Always Required

```python
# ✅ Correct
def get_user(user_id: int) -> User | None:
    ...

# ❌ Wrong — missing hints
def get_user(user_id):
    ...
```

Use `from __future__ import annotations` at the top of each file for forward references.

---

## Docstrings — Google Style, Always

Every module, class, and public function needs a docstring.

```python
def calculate_discount(price: float, rate: float) -> float:
    """Calculate the discounted price.

    Args:
        price: The original price in dollars.
        rate: The discount rate as a decimal (e.g. 0.2 for 20%).

    Returns:
        The final price after applying the discount.

    Raises:
        ValueError: If rate is not between 0 and 1.
    """
    if not 0 <= rate <= 1:
        raise ValueError(f"Rate must be between 0 and 1, got {rate}")
    return price * (1 - rate)
```

---

## Design Patterns — Always Use One

Pick the simplest pattern that fits. Document which pattern you're using in the module docstring.

**Common patterns and when to use them:**

| Pattern | Use When |
|---|---|
| Strategy | You need to swap algorithms (e.g. different exporters, parsers) |
| Factory | You create objects without specifying the exact class |
| Repository | You're abstracting data access (DB, API, file) |
| Observer | One event should trigger multiple reactions |
| Singleton | Exactly one instance is needed (e.g. config, logger) |

---

## Unit Tests — Always Write Them

- One test file per source file: `src/calculator.py` → `tests/test_calculator.py`
- Use `unittest` (standard library only, no pytest-specific features)
- Test the happy path, edge cases, and expected errors
- Keep tests short and focused — one concept per test

---

## General Rules

- **No magic numbers** — use named constants or Enum
- **No bare `except`** — always catch specific exceptions
- **No mutable default arguments** — use `None` and set inside the function
- **Keep functions small** — if it's longer than ~20 lines, consider splitting it
- **Flat over nested** — use early returns to avoid deep indentation
- **Descriptive names** — `calculate_tax()` not `calc()`, `user_id` not `uid`
- **README** — update the README with every code change

---

## Project Structure

```
project/
├── src/
│   ├── __init__.py
│   └── your_module.py
├── tests/
│   ├── __init__.py
│   └── test_your_module.py
├── pyproject.toml       # tool config (black, mypy, flake8)
├── requirements.txt
└── CLAUDE.md
```

---

## Tool Config (pyproject.toml)

```toml
[tool.black]
line-length = 88

[tool.mypy]
strict = true
python_version = "3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```
