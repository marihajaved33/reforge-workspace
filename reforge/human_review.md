# human_review.md — Migration Human-Review Decisions

> **Purpose:** Records the exact decisions made by the human reviewer for items G1–G6 identified in `reforge/migration_contract.md` §G.  
> All decisions were provided before Phase B implementation began.

---

## G1 — Error Response Shape

**Contract question:**  
The legacy app returns `{"error": "..."}` on 400 responses. FastAPI's default Pydantic validation error shape is `{"detail": [...]}` (a list). For app-raised 400 errors (e.g., duplicate email), should the FastAPI app normalize to `{"detail": "string"}`, or accept FastAPI's native list shape?

**Decision:** Normalize app-raised 400 errors to `{"detail": "string"}` format.

**Implementation:**  
In `fastapi-app/routers/auth.py`, `ValueError` raised by the service layer is caught and converted:
```python
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
```
This produces `{"detail": "Email already registered"}` or `{"detail": "Username already taken"}` — a plain string, not a list.

**Note on Pydantic validation errors (missing fields):**  
Missing required fields (`username`, `email`, `name`, `price`) produce `422 Unprocessable Entity` with `{"detail": [...]}` (a list). This is FastAPI's native `RequestValidationError` and is not affected by G1. The contract §A4 explicitly permits this shape change. Confirmed by audit smoke test:
```json
{
  "detail": [
    {"type": "missing", "loc": ["body", "email"], "msg": "Field required", "input": {"username": "x"}}
  ]
}
```

---

## G2 — `username` Uniqueness Enforcement

**Contract question:**  
The `users` table has a `UNIQUE` constraint on `username`, but the legacy `auth_service.create_user()` only checks for duplicate email. A duplicate username would cause an unhandled database `IntegrityError` (surfaced as a 500). Should the FastAPI service add an explicit check, or preserve the silent DB-level-only enforcement?

**Decision:** Add explicit 400 checks in the service for both email and username uniqueness, matching legacy error-handling style.

**Implementation:**  
In `fastapi-app/services/auth_service.py`:
```python
def create_user(db: Session, username: str, email: str) -> User:
    existing_email = db.scalar(select(User).where(User.email == email))
    if existing_email:
        raise ValueError("Email already registered")

    existing_username = db.scalar(select(User).where(User.username == username))
    if existing_username:
        raise ValueError("Username already taken")

    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```
Both checks raise `ValueError`, which is caught in the router and converted to `HTTPException(400)` per G1.

**Verified by smoke test:** `POST /auth/register` with a duplicate username returns `400 {"detail": "Username already taken"}`.

---

## G3 — `/users` Service Layer

**Contract question:**  
The legacy `GET /users` route queries `User.query.all()` directly in the route handler, bypassing the service layer entirely. Should the FastAPI port introduce a `list_users()` service function (consistent with other routes), or query the model directly in the router (preserving the legacy pattern)?

**Decision:** Introduce a `list_users()` service function for architectural consistency.

**Implementation:**  
Added to `fastapi-app/services/auth_service.py` (the user-domain service, since only `auth_service.py` and `product_service.py` were in the Phase B allowed-file list — no separate `user_service.py` was created):
```python
def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)).all())
```

`fastapi-app/routers/users.py` delegates to it:
```python
from services.auth_service import list_users

@router.get("", status_code=200, response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    return list_users(db)
```

**Known placement note:** `list_users()` lives in `auth_service.py` rather than a dedicated `user_service.py`. This is a naming incongruity. The contract's Phase B allowed-file list did not include `user_service.py`, so placing it in `auth_service.py` was the correct constraint-preserving choice. Extraction to `user_service.py` is a future option.

---

## G4 — Async vs Sync SQLAlchemy

**Contract question:**  
FastAPI supports both sync and async route handlers. Using async SQLAlchemy (`AsyncSession` + `aiosqlite`) is more idiomatic with FastAPI but adds complexity and a new dependency. Using standard sync `Session`/`sessionmaker` is simpler and requires no new dependencies, but FastAPI runs sync handlers in a threadpool.

**Decision:** Use standard synchronous `Session`/`sessionmaker`. No `aiosqlite`, no `AsyncSession`.

**Implementation:**  
In `fastapi-app/db/database.py`:
```python
engine = create_engine(
    "sqlite:///./legacy.db", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

All routers use `db: Session = Depends(get_db)`. FastAPI dispatches sync route functions in a thread pool, so the SQLite `check_same_thread=False` flag is required and is set.

---

## G5 — `price` Validation

**Contract question:**  
The legacy app accepts any float for `price`, including negative values. Should the migration add a `Field(gt=0)` Pydantic validator?

**Decision:** Preserve no validation — faithful port only.

**Implementation:**  
`fastapi-app/schemas/product.py` uses `price: float` with no `Field(...)` constraint. Negative and zero prices are accepted, matching legacy behaviour.

---

## G6 — Database File Location

**Contract question:**  
The legacy app writes `legacy.db` relative to its working directory (resolving to `legacy-flask-app/instance/`). The FastAPI app will write to wherever it is run from. Should they share a single physical database file, or use separate files?

**Decision:** Separate database files — the two apps do not share a physical SQLite file.

**Implementation:**  
`fastapi-app/db/database.py` uses `"sqlite:///./legacy.db"`, which resolves to `fastapi-app/legacy.db` when the app is started from the `fastapi-app/` directory. This file is independent of `legacy-flask-app/instance/legacy.db` (or wherever Flask wrote its file).

**Consequence:** Data entered via the Flask app is not visible to the FastAPI app and vice versa. This is the expected outcome for a parity migration of a demo repository with no shared production database.
