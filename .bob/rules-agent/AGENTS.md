# AGENTS.md — Agent Mode (Coding)

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Coding Rules

- **Never call `db.session` in route handlers.** All DB writes go through service functions in `services/`.
- **`config.py` is dead code** — do not add config keys there expecting them to take effect. Configuration is set directly in `create_app()` in `app.py`.
- **`conftest.py` is broken** — it does `from app import create_app, db` but `db` is not exported from `app.py`. Fix: import `db` from `db.database` as done in `test_auth.py`. Do not copy the `conftest.py` pattern.
- **Tests MUST be run from `legacy-flask-app/`** — all imports are root-relative to that directory. Running pytest from the workspace root will fail with `ModuleNotFoundError`.
- **All models must implement `.to_dict()`** — routes use list comprehensions like `[x.to_dict() for x in ...]` and will break without it.
- **Blueprint variable names follow `<resource>_bp`** and must be registered in `create_app()` with a URL prefix.
- No password field exists on `User` — do not assume auth beyond username/email.
- `dashboard/` and `reforge/` are in `.bobignore` — Bob cannot read files in those directories.
