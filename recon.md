# recon.md — Flask → FastAPI Migration Reconnaissance

> **Scope:** `legacy-flask-app/` only.  
> **Purpose:** Complete pre-migration analysis. No application code was modified.  
> **Note:** Intended for `reforge/recon.md` but written to project root because `reforge/` is in `.bobignore`.

---

## 1. File Inventory

```
legacy-flask-app/
├── app.py                          # App factory (create_app), entry point
├── config.py                       # Config class — DEAD CODE, never imported
├── requirements.txt                # Runtime + test dependencies
│
├── db/
│   └── database.py                 # SQLAlchemy singleton: db = SQLAlchemy()
│
├── models/
│   ├── user.py                     # User ORM model
│   └── product.py                  # Product ORM model
│
├── routes/
│   ├── auth.py                     # Blueprint: auth_bp  (/auth)
│   ├── users.py                    # Blueprint: users_bp (/users)
│   └── products.py                 # Blueprint: products_bp (/products)
│
├── services/
│   ├── auth_service.py             # create_user()
│   └── product_service.py          # list_products(), create_product()
│
├── tests/
│   ├── conftest.py                 # Shared pytest fixtures — BROKEN (see §7)
│   ├── test_auth.py                # Auth endpoint tests (local fixture)
│   ├── test_products.py            # Product endpoint tests (uses conftest)
│   └── test_users.py               # User endpoint tests (uses conftest)
│
└── instance/                       # Empty — SQLite .db file written here at runtime
```

**Total Python files:** 12 (excl. `__pycache__`, `.git`)  
**Dead files:** `config.py` (never imported anywhere)

---

## 2. Dependency Map

### `requirements.txt`
| Package | Version pinned | Role |
|---|---|---|
| `flask` | No | Web framework |
| `flask-sqlalchemy` | No | ORM integration |
| `pytest` | No | Test runner |

### Internal import graph
```
app.py
  └── db.database          (db singleton)
  └── routes.auth          → services.auth_service → models.user, db.database
  └── routes.users         → models.user
  └── routes.products      → services.product_service → models.product, db.database

tests/conftest.py
  └── app (create_app + db) ← BROKEN: db not exported from app.py
tests/test_auth.py
  └── app (create_app), db.database ← correct pattern
tests/test_products.py, test_users.py
  └── conftest.py (client fixture) ← depends on broken conftest
```

**No circular imports.** Clean layered graph: routes → services → models → db.

---

## 3. Endpoint Inventory

### `POST /auth/register` — `routes/auth.py`

| Attribute | Detail |
|---|---|
| Method | POST |
| Request content-type | JSON |
| Required request fields | `username` (str), `email` (str) |
| Success response | `201` `{"message": "User created successfully", "user": {id, username, email}}` |
| Error responses | `400` `{"error": "Invalid payload"}` — missing/null body or fields<br>`400` `{"error": "Email already registered"}` — duplicate email |
| Calls | `services.auth_service.create_user(username, email)` |
| Side effects | Inserts row into `users` table |

---

### `GET /users` — `routes/users.py`

| Attribute | Detail |
|---|---|
| Method | GET |
| Request body | None |
| Success response | `200` `[{id, username, email}, ...]` (list, possibly empty) |
| Error responses | None defined |
| Calls | `User.query.all()` directly in route (no service layer) |
| Side effects | None |

**Note:** Only route that bypasses the service layer — queries the model directly.

---

### `GET /products` — `routes/products.py`

| Attribute | Detail |
|---|---|
| Method | GET |
| Request body | None |
| Success response | `200` `[{id, name, price}, ...]` (list, possibly empty) |
| Error responses | None defined |
| Calls | `services.product_service.list_products()` |
| Side effects | None |

---

### `POST /products` — `routes/products.py`

| Attribute | Detail |
|---|---|
| Method | POST |
| Request content-type | JSON |
| Required request fields | `name` (str), `price` (float) |
| Success response | `201` `{id, name, price}` |
| Error responses | `400` `{"error": "Invalid payload"}` — missing/null body or fields |
| Calls | `services.product_service.create_product(name, price)` |
| Side effects | Inserts row into `products` table |

---

## 4. Middleware and Application Setup

### `app.py` — `create_app()` factory

```python
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///legacy.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
app.register_blueprint(auth_bp,     url_prefix="/auth")
app.register_blueprint(users_bp,    url_prefix="/users")
app.register_blueprint(products_bp, url_prefix="/products")
```

- **No custom middleware** (no `before_request`, `after_request`, error handlers).
- **No CORS** configuration.
- **No rate limiting, request logging, or authentication middleware.**
- Database initialised via `db.init_app(app)` — standard Flask-SQLAlchemy app-context pattern.
- Schema creation (`db.create_all()`) is called **outside** `create_app()`, in `__main__` block only — not called by the factory.

---

## 5. Database Connection and ORM Models

### `db/database.py`
```python
db = SQLAlchemy()   # Module-level singleton, bound to app via db.init_app(app)
```

### `models/user.py` — `User`
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `username` | String(80) | unique, not null |
| `email` | String(120) | unique, not null |

No password, no created_at, no relationships.

### `models/product.py` — `Product`
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, auto-increment |
| `name` | String(120) | not null |
| `price` | Float | not null |

No category, no timestamps, no relationships.

### ORM patterns in use
- `Model.query.all()` — Flask-SQLAlchemy legacy query interface (deprecated in SQLAlchemy 2.x)
- `Model.query.filter_by(...).first()` — same legacy interface
- `db.session.add()` / `db.session.commit()` — standard, compatible with SQLAlchemy 2.x
- No `db.session.rollback()` or exception handling around commits
- `SQLALCHEMY_TRACK_MODIFICATIONS = False` — suppresses deprecation warning; this setting is removed in Flask-SQLAlchemy 3.x

---

## 6. Service / Business Logic

### `services/auth_service.py` — `create_user(username, email)`
1. Query `User` by email — if found, return `None` (signals duplicate)
2. Construct `User`, add to session, commit
3. Return the new `User` instance

**No password hashing. No email format validation beyond uniqueness.**

### `services/product_service.py`
- `list_products()` — returns `Product.query.all()`
- `create_product(name, price)` — creates and commits a `Product`, returns it

**No input sanitisation, no price validation (accepts any float, including negative).**

---

## 7. Authentication Behavior

**There is no authentication.** The `/auth/register` endpoint creates a user record but:
- No password stored
- No login endpoint
- No session management
- No JWT or token issuance
- No protected routes
- No authorization checks on any endpoint

The name "auth" is misleading — it is purely a user-registration endpoint.

---

## 8. Tests and Their Assumptions

### `tests/conftest.py` — **BROKEN**
```python
from app import create_app, db   # db is NOT exported from app.py — ImportError at runtime
```
The `app` and `client` fixtures defined here will raise `ImportError` when collected.

**Impact:** `test_products.py` and `test_users.py` have no local imports or fixtures and depend entirely on this broken `client` fixture — they will both fail to run.

### `tests/test_auth.py` — **Working** (defines its own fixture)
```python
from app import create_app
from db.database import db        # correct import path
```
- Spins up a fresh in-memory SQLite DB per test class
- Drops schema after each test block
- Tests: `test_register` (happy path 201), `test_duplicate_email` (400 on second POST)
- **Assumption:** `username` uniqueness is not enforced at the API layer (only `email` is checked by the service)

### `tests/test_products.py` — **Broken** (depends on broken conftest)
- `test_products_empty`: GET `/products` returns `[]`
- `test_add_product`: POST `/products` with `{name, price}` returns 201

### `tests/test_users.py` — **Broken** (depends on broken conftest)
- `test_users_endpoint`: GET `/users` returns a list

### Key test assumptions for migration
- Tests use `sqlite:///:memory:` — no file I/O
- Tests call `db.create_all()` + `db.drop_all()` to isolate state per test
- No mocking of services — tests are full-stack integration tests
- No tests for error paths on products or users endpoints

---

## 9. Dependencies and Deprecated Patterns

| Pattern | Status | Migration Note |
|---|---|---|
| `Model.query.all()` | Deprecated (SQLAlchemy 2.x) | Replace with `select(Model)` via `session.execute()` |
| `Model.query.filter_by(...).first()` | Deprecated (SQLAlchemy 2.x) | Replace with `session.scalar(select(Model).where(...))` |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | Removed in Flask-SQLAlchemy 3.x | Drop entirely in FastAPI + SQLAlchemy 2.x |
| `db.init_app(app)` | Flask-specific | Replace with SQLAlchemy `engine` + `sessionmaker` / `AsyncSession` |
| `Flask.Blueprint` | Flask-specific | Replace with FastAPI `APIRouter` |
| `flask.request.get_json()` | Flask-specific | Replace with Pydantic request body models |
| `flask.jsonify()` | Flask-specific | FastAPI returns dicts/Pydantic models automatically |
| No version pins in `requirements.txt` | Risk | Pin versions before migration to avoid surprise upgrades |
| No password hashing | Security gap | Not a migration blocker, but must be noted |
| `db.session.commit()` without try/except | Risk | Add rollback on exception in service layer |

---

## 10. Risk List

| Risk | Severity | Detail |
|---|---|---|
| **Broken test suite** | High | `conftest.py` ImportError means 2 of 3 test files are non-runnable. Fix before migration so baseline is trustworthy. |
| **No version pins** | High | `flask`, `flask-sqlalchemy`, `pytest` are unpinned. Freeze current environment with `pip freeze` before starting. |
| **Legacy SQLAlchemy query API** | Medium | `.query` interface is deprecated. Rewrite to `select()` style in FastAPI + SQLAlchemy 2.x. |
| **No rollback on DB commit failure** | Medium | Any DB error leaves the session in a dirty state. Add `try/except/rollback` in services. |
| **`/users` bypasses service layer** | Low | Inconsistent with rest of codebase; easy to fix during migration. |
| **No input validation on price** | Low | Negative/zero prices accepted silently. Pydantic in FastAPI will enforce types but not business rules unless validators are added. |
| **`config.py` confusion** | Low | Dead file. Remove it during migration to avoid future confusion. |
| **No CORS, no auth middleware** | Informational | FastAPI migration should define these explicitly from the start. |

---

## 11. Recommended Migration Order

The migration can be done in one focused pass given the small surface area (4 endpoints, 2 models, 2 services). The recommended order minimises inter-step dependencies:

```
Step 1 — Fix & freeze baseline
  - Fix conftest.py: change `from app import create_app, db`
                     to `from app import create_app` + `from db.database import db`
  - Confirm all tests pass: cd legacy-flask-app && pytest tests/
  - Pin dependencies: pip freeze > requirements.txt

Step 2 — Project scaffold
  - New directory (e.g. fastapi-app/) with FastAPI + SQLAlchemy 2.x + uvicorn
  - Establish db/database.py equivalent: engine, sessionmaker, Base, get_db() dependency

Step 3 — Models (no Flask dependency)
  - Migrate User and Product to SQLAlchemy 2.x declarative style
  - Add Pydantic schemas: UserCreate, UserRead, ProductCreate, ProductRead

Step 4 — Services (no Flask dependency)
  - Migrate auth_service and product_service
  - Update query patterns from .query to select()
  - Add try/except + rollback around commits

Step 5 — Routers (replace Blueprints with APIRouter)
  - POST /auth/register
  - GET  /users
  - GET  /products
  - POST /products
  - Inject DB session via FastAPI Depends(get_db)

Step 6 — App factory
  - main.py: create FastAPI app, include routers, configure lifespan (db.create_all on startup)
  - Delete config.py equivalent — no dead code carried forward

Step 7 — Tests
  - Port all tests using httpx.AsyncClient + override get_db with in-memory SQLite
  - Ensure same happy-path and error-path coverage as original
  - Fix the username-uniqueness gap (currently only email is checked in the service)

Step 8 — Validation
  - Run full test suite
  - Smoke-test all 4 endpoints manually
  - Verify parity with legacy responses (field names, status codes, error shapes)
```
