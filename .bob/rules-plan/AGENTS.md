# AGENTS.md — Plan Mode (Architecture)

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Architectural Constraints

- **Layered architecture is strict**: routes → services → models/db. Routes must not touch `db.session`; that belongs in services.
- **`create_app()` is the only configuration point** — `config.py` exists but is never used. All config changes go in `create_app()`.
- **SQLite with file-based DB in production** (`sqlite:///legacy.db`), in-memory only during tests (`sqlite:///:memory:`).
- **No migration tooling** (no Flask-Migrate/Alembic) — schema is created via `db.create_all()` on startup. Schema changes require manual intervention.
- **No authentication enforcement** — there is a `/auth/register` endpoint but no login, sessions, tokens, or protected routes.
- **Test infrastructure is partially broken** — `conftest.py`'s `app` fixture fails because it tries to import `db` from `app.py` which doesn't export it. Any plan involving new tests must account for this by importing `db` from `db.database`.
- `dashboard/` is a separate Streamlit application (`.gitignore` contains `.streamlit/secrets.toml`) — it is a distinct service, not part of the Flask app.
