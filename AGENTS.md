# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Structure

```
legacy-flask-app/   # Main Flask application (active codebase)
dashboard/          # Streamlit dashboard (bobignore'd — unreadable by Bob)
reforge/            # Migration/recon docs (bobignore'd — unreadable by Bob)
venv/               # Python virtual environment (gitignore'd)
```

The **`legacy-flask-app/`** directory is the only fully accessible application code.

## Stack

- Python, Flask, Flask-SQLAlchemy, SQLite
- Testing: pytest
- No linter, formatter, or type-checker configured

## Commands

All commands must be run **from inside `legacy-flask-app/`**, not the workspace root.
The import paths (`from app import ...`, `from db.database import db`, etc.) are root-relative within that directory.

```bash
# Run app
cd legacy-flask-app
python app.py

# Run all tests
cd legacy-flask-app
pytest tests/

# Run a single test file
pytest tests/test_auth.py

# Run a single test by name
pytest tests/test_auth.py::test_register
```

## Architecture

```
app.py (create_app factory)
  ├── db/database.py        — SQLAlchemy singleton: db = SQLAlchemy()
  ├── models/user.py        — User model (users table), exposes .to_dict()
  ├── models/product.py     — Product model (products table), exposes .to_dict()
  ├── routes/auth.py        — Blueprint auth_bp  → /auth/register (POST)
  ├── routes/users.py       — Blueprint users_bp → /users (GET)
  ├── routes/products.py    — Blueprint products_bp → /products (GET, POST)
  ├── services/auth_service.py    — create_user()
  └── services/product_service.py — list_products(), create_product()
```

## Critical Gotchas

- **`config.py` is never used.** `app.py` hardcodes `"sqlite:///legacy.db"` directly; `Config` class is dead code.
- **`conftest.py` imports `db` from `app`** (`from app import create_app, db`) but `app.py` does not export `db` — this fixture is broken. The working fixture pattern is in `test_auth.py` (imports `db` from `db.database` directly).
- **`test_products.py` and `test_users.py` rely on `conftest.py`'s `client` fixture** (no local fixture), so they will fail unless the `conftest.py` import bug is fixed.
- No password hashing — users are stored with only `username` and `email` (no password field).

## Code Style (observed conventions)

- Imports: stdlib → flask → local (no enforced order)
- No type hints anywhere
- Models always implement `.to_dict()` returning a plain dict
- Routes validate payload presence + required keys and return `{"error": "..."}` with 4xx on failure
- Services handle DB writes; routes do not call `db.session` directly
- Blueprints are named `<resource>_bp` and registered with a URL prefix in `create_app()`
