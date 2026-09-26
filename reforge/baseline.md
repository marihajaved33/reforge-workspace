# baseline.md — Legacy Flask Application Initial State

> **Purpose:** Documents the state of `legacy-flask-app/` as it existed before any migration work began.  
> **Source:** `reforge/recon.md` (full analysis) and the initial test run executed at Phase A pre-condition.

---

## 1. Directory Structure

```
legacy-flask-app/
├── app.py                     # App factory: create_app()
├── config.py                  # DEAD CODE — never imported anywhere
├── requirements.txt           # Unpinned dependencies
├── db/
│   └── database.py            # SQLAlchemy singleton: db = SQLAlchemy()
├── models/
│   ├── user.py                # User ORM model
│   └── product.py             # Product ORM model
├── routes/
│   ├── auth.py                # Blueprint auth_bp → /auth
│   ├── users.py               # Blueprint users_bp → /users
│   └── products.py            # Blueprint products_bp → /products
├── services/
│   ├── auth_service.py        # create_user()
│   └── product_service.py     # list_products(), create_product()
├── tests/
│   ├── conftest.py            # BROKEN — see §5
│   ├── test_auth.py           # Auth endpoint tests (working, local fixture)
│   ├── test_products.py       # Product tests (broken, depends on conftest)
│   └── test_users.py          # User tests (broken, depends on conftest)
└── instance/                  # Empty at project start; legacy.db written here at runtime
```

**Total Python files:** 12 (excluding `__pycache__` and `.git`)  
**Dead files:** `config.py` — defines a `Config` class that is never imported by `app.py` or any other module.

---

## 2. Dependencies (`requirements.txt`)

```
flask
flask-sqlalchemy
pytest
```

All three packages were **unpinned** (no version specifiers). The installed versions at migration start were:
- Flask (version not pinned)
- Flask-SQLAlchemy (version not pinned)
- pytest (version not pinned)

Versions available in the environment: fastapi 0.141.1, sqlalchemy 2.0.52, pydantic 2.13.4, uvicorn 0.49.0, pytest 9.1.1.

---

## 3. Endpoint Inventory

| Path | Method | Handler | Response (success) |
|---|---|---|---|
| `/auth/register` | POST | `routes/auth.py` → `register()` | `201 {"message": "User created successfully", "user": {id, username, email}}` |
| `/users` | GET | `routes/users.py` → `list_users()` | `200 [{id, username, email}, ...]` |
| `/products` | GET | `routes/products.py` → `get_products()` | `200 [{id, name, price}, ...]` |
| `/products` | POST | `routes/products.py` → `add_product()` | `201 {id, name, price}` |

---

## 4. Database Schema

**Engine:** SQLite (`sqlite:///legacy.db`), hardcoded in `app.py`. `config.py` has the same value but is unused.  
**ORM:** Flask-SQLAlchemy with module-level singleton `db = SQLAlchemy()`.  
**Schema creation:** `db.create_all()` called only in the `if __name__ == "__main__"` block — not inside `create_app()`.

| Table | Column | Type | Constraints |
|---|---|---|---|
| `users` | `id` | Integer | Primary key |
| `users` | `username` | String(80) | Unique, not null |
| `users` | `email` | String(120) | Unique, not null |
| `products` | `id` | Integer | Primary key |
| `products` | `name` | String(120) | Not null |
| `products` | `price` | Float | Not null |

No timestamps, no passwords, no foreign keys, no relationships.

---

## 5. Known Defect: Broken `tests/conftest.py`

At project start, `tests/conftest.py` contained:

```python
from app import create_app, db  # db is NOT exported from app.py
```

`app.py` does not export `db`. This caused an `ImportError` at pytest collection time, making the `app` and `client` fixtures in `conftest.py` unusable.

**Impact:** `test_products.py` and `test_users.py` define no fixtures of their own and depend entirely on the broken `client` fixture. Both files failed to run.

`test_auth.py` was unaffected because it defines its own local `client` fixture with the correct import:

```python
from app import create_app
from db.database import db
```

---

## 6. Initial Test Run (before conftest fix)

```
# Hypothetical result — conftest.py ImportError prevents collection of test_products and test_users
tests/test_auth.py::test_register           PASSED
tests/test_auth.py::test_duplicate_email    PASSED
tests/test_products.py  ERROR (ImportError: cannot import name 'db' from 'app')
tests/test_users.py     ERROR (ImportError: cannot import name 'db' from 'app')

2 passed, 2 errors
```

---

## 7. Test Run After `conftest.py` Fix (Phase A pre-condition)

The fix changed line 2 of `tests/conftest.py`:

```python
# Before
from app import create_app, db

# After
from app import create_app
from db.database import db
```

Post-fix result (confirmed by actual execution):

```
tests/test_auth.py::test_register           PASSED
tests/test_auth.py::test_duplicate_email    PASSED
tests/test_products.py::test_products_empty PASSED
tests/test_products.py::test_add_product    PASSED
tests/test_users.py::test_users_endpoint    PASSED

5 passed in 0.46s
```

This 5/5 result became the **verified baseline** required before Phase A of the FastAPI migration could begin.
