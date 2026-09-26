# AGENTS.md — Ask Mode (Documentation)

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Documentation Context

- The workspace contains three distinct areas: `legacy-flask-app/` (readable Flask app), `dashboard/` (Streamlit app, bobignore'd), and `reforge/` (migration docs, bobignore'd). Only `legacy-flask-app/` is fully accessible.
- `config.py` exists but is never imported — it is misleading dead code.
- `conftest.py` has a broken import (`db` from `app`) — the working test fixture pattern is in `test_auth.py`, not `conftest.py`.
- `test_products.py` and `test_users.py` contain no imports and no fixtures — they depend entirely on `conftest.py`'s `client` fixture.
- The `.gitignore` hides `*.db` files and `.streamlit/secrets.toml`, hinting that the dashboard uses Streamlit with secrets.
