# migration_log.md — Flask → FastAPI Migration Execution Log

> **Source app:** `legacy-flask-app/`  
> **Target app:** `fastapi-app/`  
> **Contract:** `reforge/migration_contract.md`  
> **Phases:** A (data layer) → B (routes and services) → C (entry point) → D (tests, cleanup, audit)

---

## Pre-Migration: Baseline Fix

**Action:** Fixed broken import in `legacy-flask-app/tests/conftest.py`.

**Change:**
```python
# Before (line 2)
from app import create_app, db  # db not exported from app.py — causes ImportError

# After
from app import create_app
from db.database import db
```

**Validation:**
```
legacy-flask-app/ $ pytest tests/ -v
5 passed in 0.46s
```

All 5 legacy tests passing. Baseline locked.

---

## Phase A — Models, Database Access, and Pydantic Schemas

**Goal:** Establish the data layer with no HTTP code. The `fastapi-app/` directory did not exist before this phase.

### Files Created

| File | Notes |
|---|---|
| `fastapi-app/requirements.txt` | Pinned: fastapi==0.141.1, sqlalchemy==2.0.52, pydantic==2.13.4, uvicorn==0.49.0, pytest==9.1.1, httpx2>=2.13.1 |
| `fastapi-app/db/database.py` | SQLAlchemy 2.x: `create_engine`, `DeclarativeBase`, `sessionmaker`, `get_db()` generator dependency |
| `fastapi-app/models/user.py` | `User` with `__tablename__ = "users"`, columns: id (Integer PK), username (String(80) unique not null), email (String(120) unique not null) |
| `fastapi-app/models/product.py` | `Product` with `__tablename__ = "products"`, columns: id (Integer PK), name (String(120) not null), price (Float not null) |
| `fastapi-app/schemas/user.py` | `UserCreate(username, email)`, `UserRead(id, username, email)` with `model_config = {"from_attributes": True}` |
| `fastapi-app/schemas/product.py` | `ProductCreate(name, price)`, `ProductRead(id, name, price)` with `model_config = {"from_attributes": True}` |

### Acceptance Checks Passed

```
# 1. Legacy baseline still green
legacy-flask-app/ $ pytest tests/ -v  →  5 passed

# 2. All Phase A imports resolve
fastapi-app/ $ python -c "from db.database import Base, get_db; from models.user import User;
  from models.product import Product; from schemas.user import UserCreate, UserRead;
  from schemas.product import ProductCreate, ProductRead; print('Phase A imports OK')"
Phase A imports OK

# 3. SQLAlchemy creates correct schema
fastapi-app/ $ python -c "...create_engine(':memory:'), create_all, inspect..."
Phase A schema OK: ['products', 'users']
```

**Phase A result: PASS**

---

## Phase B — Routes and Service Integration

**Goal:** Implement all 4 endpoints. Services own all DB writes.  
**Pre-condition met:** Phase A acceptance checks green.

**Human-review decisions applied in this phase:** G1, G2, G3, G4 (see `reforge/human_review.md`).

### Files Created

| File | Notes |
|---|---|
| `fastapi-app/services/auth_service.py` | `create_user(db, username, email)` — raises `ValueError` on duplicate email or username (G2); `list_users(db)` added per G3 |
| `fastapi-app/services/product_service.py` | `list_products(db)`, `create_product(db, name, price)` — uses SQLAlchemy 2.x `select()` API throughout |
| `fastapi-app/routers/auth.py` | `POST /register` → catches `ValueError` → `HTTPException(status_code=400, detail=str(exc))` per G1 |
| `fastapi-app/routers/users.py` | `GET ""` → delegates to `list_users(db)` per G3 |
| `fastapi-app/routers/products.py` | `GET ""` → `list_products(db)`, `POST ""` → `create_product(db, ...)` |

### Acceptance Checks Passed

```
# Router imports
fastapi-app/ $ python -c "from routers.auth import router; from routers.users import router;
  from routers.products import router; print('Phase B router imports OK')"
Phase B router imports OK

# Service imports
fastapi-app/ $ python -c "from services.auth_service import create_user, list_users;
  from services.product_service import list_products, create_product; print('Phase B service imports OK')"
Phase B service imports OK

# In-memory service integration test (all assertions passed):
create_user OK: alice alice@example.com
duplicate email ValueError OK
duplicate username ValueError OK
list_users OK: 1
create_product OK: Keyboard 25.0
list_products OK: 1
All Phase B service tests passed
```

**Phase B result: PASS**

---

## Phase C — FastAPI Entry Point

**Goal:** Wire the application together with no new business logic.  
**Pre-condition met:** Phase B acceptance checks green.

### Files Created

| File | Notes |
|---|---|
| `fastapi-app/main.py` | `FastAPI(lifespan=lifespan)` — lifespan calls `Base.metadata.create_all(bind=engine)` on startup; includes `auth.router` at `/auth`, `users.router` at `/users`, `products.router` at `/products` |

`fastapi-app/dependencies.py` was **not created** — `get_db()` lives in `db/database.py` and is imported directly by routers. No shared wrappers were needed.

### Acceptance Checks Passed

```
# App import
fastapi-app/ $ python -c "from main import app; print('Phase C app import OK')"
Phase C app import OK

# Route verification via OpenAPI schema (contract's app.routes check is incompatible
# with FastAPI 0.141's _IncludedRouter model; app.openapi() used as equivalent)
fastapi-app/ $ python -c "from main import app; paths = list(app.openapi()['paths'].keys());
  assert '/auth/register' in paths and '/users' in paths and '/products' in paths;
  print('Phase C routes OK:', paths)"
Phase C routes OK: ['/auth/register', '/users', '/products']

# Methods confirmed:
/auth/register: ['post']
/users: ['get']
/products: ['get', 'post']
```

**Phase C result: PASS**

---

## Phase D — Tests, Cleanup, and Final Audit

**Goal:** Port all tests; verify full parity.  
**Pre-condition met:** Phase C acceptance checks green.

### Files Created

| File | Notes |
|---|---|
| `fastapi-app/tests/conftest.py` | `client` fixture: creates `sqlite:///:memory:` engine with `StaticPool` (required so all sessions share one connection), calls `Base.metadata.create_all`, overrides `get_db` via `app.dependency_overrides`, yields `TestClient`, clears overrides and drops schema on teardown |
| `fastapi-app/tests/test_auth.py` | `test_register` (201, checks `data["user"]["username"]`), `test_duplicate_email` (second POST with same email returns 400) |
| `fastapi-app/tests/test_products.py` | `test_products_empty` (GET returns `[]`), `test_add_product` (POST 201, checks `name`) |
| `fastapi-app/tests/test_users.py` | `test_users_endpoint` (GET 200, response is list) |

**Note on `conftest.py` first attempt:** The initial implementation used a plain `sessionmaker` without `StaticPool`. SQLite in-memory databases are connection-scoped; each new `Session()` opened a fresh connection to a different empty database, causing `no such table: users`. Fixed by adding `poolclass=StaticPool`.

### `requirements.txt` update

`httpx>=0.27.0` was replaced with `httpx2>=2.13.1` because Starlette 1.2.1 (installed in this environment) deprecated `httpx` in favour of `httpx2`. This is a test-infrastructure change only.

### Final Test Run

```
fastapi-app/ $ pytest tests/ -v
tests/test_auth.py::test_register           PASSED
tests/test_auth.py::test_duplicate_email    PASSED
tests/test_products.py::test_products_empty PASSED
tests/test_products.py::test_add_product    PASSED
tests/test_users.py::test_users_endpoint    PASSED
5 passed in 0.31s

legacy-flask-app/ $ pytest tests/ -v
tests/test_auth.py::test_register           PASSED
tests/test_auth.py::test_duplicate_email    PASSED
tests/test_products.py::test_products_empty PASSED
tests/test_products.py::test_add_product    PASSED
tests/test_users.py::test_users_endpoint    PASSED
5 passed in 0.51s
```

**Phase D result: PASS — 10 / 10 tests passing across both suites.**

---

## Summary

| Phase | Files created/modified | Tests at end |
|---|---|---|
| Pre-migration fix | 1 modified (`legacy-flask-app/tests/conftest.py`) | 5 / 5 legacy |
| A — Data layer | 6 created in `fastapi-app/` | 5 / 5 legacy |
| B — Routes + services | 5 created in `fastapi-app/` | 5 / 5 legacy |
| C — Entry point | 1 created in `fastapi-app/` | 5 / 5 legacy |
| D — Tests + audit | 4 created + 1 updated in `fastapi-app/` | 5 / 5 legacy + 5 / 5 FastAPI |
| **Total** | **1 modified + 16 created** | **10 / 10** |
