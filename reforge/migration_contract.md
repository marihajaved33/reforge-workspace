# migration_contract.md — Flask → FastAPI Migration Contract

> **Repository:** `legacy-flask-app/` → `fastapi-app/`  
> **Source of truth for recon:** `reforge/recon.md`  
> **This document is a binding contract.** Any deviation from sections A–G requires explicit human sign-off before implementation proceeds.

---

## A. Non-Negotiable Invariants

The following behaviors must be identical in the FastAPI app. They are the pass/fail criteria for every phase.

### A1. Endpoint Paths
| Path | Method | Must remain |
|---|---|---|
| `/auth/register` | POST | Unchanged |
| `/users` | GET | Unchanged |
| `/products` | GET | Unchanged |
| `/products` | POST | Unchanged |

No new paths. No path aliases. No version prefixes (e.g. `/v1/`).

### A2. HTTP Methods
All methods are fixed as documented above. No additional methods may be added to existing paths.

### A3. Successful Response Semantics

| Endpoint | Status | Response shape | Invariant |
|---|---|---|---|
| `POST /auth/register` | `201` | `{"message": "User created successfully", "user": {"id": int, "username": str, "email": str}}` | Field names and nesting are exact |
| `GET /users` | `200` | `[{"id": int, "username": str, "email": str}, ...]` | List, possibly empty; field names exact |
| `GET /products` | `200` | `[{"id": int, "name": str, "price": float}, ...]` | List, possibly empty; field names exact |
| `POST /products` | `201` | `{"id": int, "name": str, "price": float}` | Field names exact; no wrapping envelope |

### A4. Validation and Error Semantics

| Endpoint | Condition | Status | Response |
|---|---|---|---|
| `POST /auth/register` | Missing body, or missing `username`/`email` field | `400` | `{"detail": ...}` — see note below |
| `POST /auth/register` | Duplicate email | `400` | `{"detail": "Email already registered"}` or equivalent |
| `POST /products` | Missing body, or missing `name`/`price` field | `400` | `{"detail": ...}` — see note below |

> **Note on error shape:** The legacy app returns `{"error": "..."}`. FastAPI's default validation error shape is `{"detail": [...]}`. This shape change is **permitted** because Pydantic validation replaces manual `if not data` checks — the semantic meaning (400 on bad input) is preserved. If a consumer depends on the `"error"` key specifically, flag it under G.

### A5. SQLite Data Behavior
- Database file: `fastapi-app/legacy.db` (same filename, new directory)
- Tables: `users`, `products` — exact names preserved (set via `__tablename__`)
- Column names, types, and constraints must be identical to the legacy schema (see recon §5)
- No schema migrations, no new columns, no renamed columns
- `id` must remain integer primary key with auto-increment

### A6. Test Greenness
- All tests that pass in the legacy app before migration must have a direct equivalent in `fastapi-app/tests/`
- The broken legacy tests (`test_products.py`, `test_users.py`) must be fixed as part of Phase A baseline work before any FastAPI code is written
- FastAPI equivalents must cover the same assertions; adding coverage is permitted, removing is not

---

## B. Phase Boundaries

Each phase produces a commit. No phase may touch files outside its allowed set (see §C).

### Phase A — Models, Database Access, and Pydantic Schemas
**Goal:** Establish the data layer with no HTTP code.  
**Deliverables:**
- `fastapi-app/db/database.py` — SQLAlchemy 2.x engine, `SessionLocal`, `Base`, `get_db()` dependency
- `fastapi-app/models/user.py` — `User` ORM model (SQLAlchemy 2.x declarative)
- `fastapi-app/models/product.py` — `Product` ORM model
- `fastapi-app/schemas/user.py` — `UserCreate`, `UserRead` Pydantic models
- `fastapi-app/schemas/product.py` — `ProductCreate`, `ProductRead` Pydantic models
- `fastapi-app/requirements.txt` — pinned dependencies

**Pre-condition:** Legacy `conftest.py` bug must be fixed and `cd legacy-flask-app && pytest tests/` must be green before this phase begins.

---

### Phase B — Routes and Service Integration
**Goal:** Implement all 4 endpoints using `APIRouter`. Services handle all DB writes.  
**Deliverables:**
- `fastapi-app/services/auth_service.py`
- `fastapi-app/services/product_service.py`
- `fastapi-app/routers/auth.py`
- `fastapi-app/routers/users.py`
- `fastapi-app/routers/products.py`

**Pre-condition:** Phase A commit exists and its acceptance criteria pass.

---

### Phase C — FastAPI Entry Point, Dependencies, and Auth Integration
**Goal:** Wire the application together; no new business logic.  
**Deliverables:**
- `fastapi-app/main.py` — `FastAPI` app, router includes, lifespan for `create_all`
- `fastapi-app/dependencies.py` (if needed) — shared `Depends` wrappers

**Pre-condition:** Phase B commit exists and its acceptance criteria pass.

---

### Phase D — Tests, Cleanup, and Final Audit
**Goal:** Port all tests, remove dead code, verify full parity.  
**Deliverables:**
- `fastapi-app/tests/conftest.py`
- `fastapi-app/tests/test_auth.py`
- `fastapi-app/tests/test_products.py`
- `fastapi-app/tests/test_users.py`
- Delete `fastapi-app/` dead code (any unused files)
- Update `reforge/migration_log.md` with final status

**Pre-condition:** Phase C commit exists and its acceptance criteria pass.

---

## C. Allowed Files Per Phase

Only files explicitly listed here may be created or modified in that phase. **Any other file is off-limits.**

### Phase A
```
fastapi-app/                          ← create directory
fastapi-app/requirements.txt
fastapi-app/db/
fastapi-app/db/database.py
fastapi-app/models/
fastapi-app/models/user.py
fastapi-app/models/product.py
fastapi-app/schemas/
fastapi-app/schemas/user.py
fastapi-app/schemas/product.py

legacy-flask-app/tests/conftest.py    ← bug fix only (import path correction)
```

### Phase B
```
fastapi-app/services/
fastapi-app/services/auth_service.py
fastapi-app/services/product_service.py
fastapi-app/routers/
fastapi-app/routers/auth.py
fastapi-app/routers/users.py
fastapi-app/routers/products.py
```

### Phase C
```
fastapi-app/main.py
fastapi-app/dependencies.py           ← only if needed
```

### Phase D
```
fastapi-app/tests/
fastapi-app/tests/conftest.py
fastapi-app/tests/test_auth.py
fastapi-app/tests/test_products.py
fastapi-app/tests/test_users.py
reforge/migration_log.md
```

---

## D. Forbidden Changes

The following are prohibited in all phases without explicit human approval:

| Category | Forbidden action |
|---|---|
| **Features** | Adding any endpoint, field, or behavior not present in the legacy app |
| **Schema** | Renaming columns, adding columns, changing column types, adding tables |
| **UI** | Any work on `dashboard/` or any frontend code |
| **Unrelated refactors** | Reformatting, renaming, or reorganising files outside the allowed list |
| **Secrets/config** | Hardcoding secrets, adding `.env` files, or exposing config values in committed files |
| **Legacy app** | Any change to `legacy-flask-app/` other than the `conftest.py` import fix in Phase A |
| **Dead code carry-forward** | `config.py` must not be ported — it is dead code and must not exist in `fastapi-app/` |

---

## E. Acceptance Criteria

Run these exact commands at the end of each phase. All must pass with zero failures before the phase commit is made.

### Phase A
```bash
# 1. Legacy baseline is green (run from legacy-flask-app/)
cd legacy-flask-app
pytest tests/ -v

# 2. FastAPI app imports cleanly (run from fastapi-app/)
cd ../fastapi-app
python -c "from db.database import Base, get_db; from models.user import User; from models.product import Product; from schemas.user import UserCreate, UserRead; from schemas.product import ProductCreate, ProductRead; print('Phase A imports OK')"

# 3. SQLAlchemy can create schema in memory
python -c "
from sqlalchemy import create_engine, inspect
from db.database import Base
from models.user import User
from models.product import Product
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
tables = inspect(engine).get_table_names()
assert 'users' in tables and 'products' in tables, f'Missing tables: {tables}'
print('Phase A schema OK:', tables)
"
```

### Phase B
```bash
cd fastapi-app

# 1. All routers import cleanly
python -c "from routers.auth import router; from routers.users import router; from routers.products import router; print('Phase B router imports OK')"

# 2. Services import cleanly
python -c "from services.auth_service import create_user; from services.product_service import list_products, create_product; print('Phase B service imports OK')"
```

### Phase C
```bash
cd fastapi-app

# 1. App starts without error
python -c "from main import app; print('Phase C app import OK')"

# 2. OpenAPI schema generates (all 4 routes visible)
python -c "
from main import app
routes = [r.path for r in app.routes]
required = ['/auth/register', '/users', '/products']
for r in required:
    assert r in routes, f'Missing route: {r}'
print('Phase C routes OK:', routes)
"

# 3. Manual smoke test (requires uvicorn running in a separate terminal)
# uvicorn main:app --port 8000
# curl -s -X POST http://localhost:8000/auth/register \
#      -H "Content-Type: application/json" \
#      -d '{"username":"alice","email":"alice@example.com"}' | python -m json.tool
# curl -s http://localhost:8000/users | python -m json.tool
# curl -s http://localhost:8000/products | python -m json.tool
# curl -s -X POST http://localhost:8000/products \
#      -H "Content-Type: application/json" \
#      -d '{"name":"Keyboard","price":25.0}' | python -m json.tool
```

### Phase D
```bash
# 1. Full FastAPI test suite
cd fastapi-app
pytest tests/ -v

# 2. Legacy test suite still green (no regressions)
cd ../legacy-flask-app
pytest tests/ -v

# 3. Response shape parity check — run both apps and diff key responses
#    (manual step; see §G item G4 for shape decision)
```

---

## F. Rollback Points

A Git commit must be made at the **start** of each phase (before writing any phase files), tagged as the rollback point for that phase. If a phase fails its acceptance criteria, reset to this commit.

| Phase | Rollback commit tag | Description |
|---|---|---|
| Phase A | `pre-phase-a` | State after `legacy-flask-app/` conftest fix; before any `fastapi-app/` files exist |
| Phase B | `pre-phase-b` | State after Phase A acceptance criteria pass; `fastapi-app/` has data layer only |
| Phase C | `pre-phase-c` | State after Phase B acceptance criteria pass; routers and services exist |
| Phase D | `pre-phase-d` | State after Phase C acceptance criteria pass; app runs end-to-end |

**Tagging command (run at start of each phase):**
```bash
git tag pre-phase-a   # or pre-phase-b, etc.
git push origin pre-phase-a
```

---

## G. Human Review Items

Bob must **stop and flag** the following decisions rather than making them unilaterally. Each item lists the question and the two options.

| ID | Decision point | Options | Default if not flagged |
|---|---|---|---|
| **G1** | **Error response shape** — Legacy uses `{"error": "..."}`. FastAPI Pydantic validation returns `{"detail": [...]}`. Should the FastAPI app normalize error responses to match `{"detail": "..."}` (string, not list) for the 400 duplicate-email case, or accept FastAPI's native shape? | A) Normalize to `{"detail": "string"}` uniformly · B) Accept native FastAPI validation shape | **Must flag — no default** |
| **G2** | **`username` uniqueness** — The `users` table has a `UNIQUE` constraint on `username`, but `auth_service.create_user()` only checks email uniqueness. A duplicate username will currently raise a DB integrity error (unhandled). Should the FastAPI service add explicit username uniqueness checking, or preserve the silent DB-level-only enforcement? | A) Add explicit check + 400 response · B) Let DB integrity error propagate as 500 | **Must flag — no default** |
| **G3** | **`/users` service layer** — Legacy `GET /users` queries `User.query.all()` directly in the route, bypassing the service layer. Should the FastAPI port introduce a `list_users()` service function (consistent with other routes), or query the model directly in the router (preserving the legacy pattern)? | A) Add `list_users()` service · B) Query model directly in router | **Must flag — no default** |
| **G4** | **Async vs sync** — FastAPI supports both sync and async route handlers. Given the app uses SQLite (no async driver available without `aiosqlite`), should the migration use sync SQLAlchemy with a standard `Session`, or async SQLAlchemy with `AsyncSession` + `aiosqlite`? | A) Sync (`Session`, `sessionmaker`) — simpler, no new dependency · B) Async (`AsyncSession`, `aiosqlite`) — FastAPI idiomatic but adds complexity | **Must flag — no default** |
| **G5** | **`price` validation** — Legacy accepts any float including negative values. Pydantic can trivially add `price: float = Field(gt=0)`. Should the migration add a positive-price constraint, or faithfully preserve the no-validation behavior? | A) Add `gt=0` validator · B) Preserve no validation | **Preserve (B) unless user says otherwise** |
| **G6** | **DB file location** — Legacy writes `legacy.db` into `legacy-flask-app/instance/` (SQLite path resolution). FastAPI app will write to `fastapi-app/legacy.db` or wherever it is run from. Should they share the same physical DB file, or use separate files? | A) Shared file (requires absolute path config) · B) Separate files | **Must flag — no default** |
