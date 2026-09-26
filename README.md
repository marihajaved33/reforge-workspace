# ReForge
Autonomous Repository Migration Workbench

## Problem
Legacy migration is repetitive, cross-file and risky. Engineers must manually map routes, translate ORM patterns, update test fixtures, resolve version incompatibilities, and produce audit-grade documentation — all while preserving exact API behavior. One missed import or misread schema column breaks production.

## Solution
ReForge uses IBM Bob to understand, plan, refactor, validate and document a controlled Flask → FastAPI migration. Bob reads the entire legacy codebase, identifies dead code and defects, produces a binding migration contract, executes each phase against that contract, and generates a full audit trail — without human prompting between steps.

## Demo
## Demo
* **Live Evidence Dashboard:** [ReForge Streamlit Dashboard](https://reforge-workspace-6f22rpobxnnfjzqimvgwwe.streamlit.app/)
* **Video Walkthrough:** https://drive.google.com/file/d/1SUitHyVKZm3cGRfqmmzkj7MFhTjMa64f/view?usp=drive_link

## Architecture

```
reforge-workspace/
├── legacy-flask-app/          # Source: Flask + Flask-SQLAlchemy + SQLite
│   ├── app.py                 # create_app() factory, Blueprint registration
│   ├── db/database.py         # SQLAlchemy singleton (Flask-SQLAlchemy)
│   ├── models/                # User, Product ORM models
│   ├── routes/                # auth_bp (/auth), users_bp (/users), products_bp (/products)
│   ├── services/              # create_user(), list_products(), create_product()
│   └── tests/                 # pytest suite (was partially broken at project start)
│
├── fastapi-app/               # Target: FastAPI + SQLAlchemy 2.x + Pydantic v2 + SQLite
│   ├── main.py                # FastAPI app, lifespan (create_all), router mounts
│   ├── db/database.py         # Engine, SessionLocal, Base, get_db() dependency
│   ├── models/                # User, Product — exact schema parity with legacy
│   ├── schemas/               # UserCreate/Read, ProductCreate/Read (Pydantic v2)
│   ├── routers/               # auth (/auth), users (/users), products (/products)
│   ├── services/              # create_user(), list_users(), list_products(), create_product()
│   └── tests/                 # Full pytest suite via TestClient + StaticPool in-memory SQLite
│
└── reforge/                   # Bob-generated migration audit trail
    ├── recon.md               # Full codebase analysis before any changes
    ├── migration_contract.md  # Binding invariants, phase boundaries, forbidden changes
    ├── baseline.md            # Initial legacy state and defects
    ├── migration_log.md       # Chronological phase-by-phase execution record
    ├── human_review.md        # All G1–G6 architectural decisions and their implementations
    └── validation_report.md  # Final test counts, route parity, schema parity, audit
```

**4 endpoints migrated. 0 paths changed. 0 methods changed. 10/10 tests passing.**

## How it works

**Understand** → Bob reads every file in the legacy app, maps the import graph, identifies dead code (`config.py`), finds the broken test fixture, and documents the full endpoint/schema/service inventory in `reforge/recon.md`.

**Contract** → Bob produces `reforge/migration_contract.md`: non-negotiable invariants (exact paths, response shapes, column names), phase boundaries with allowed-file lists, forbidden changes, per-phase acceptance criteria, and a list of architectural decisions that require human sign-off before implementation begins.

**Refactor** → Bob implements each phase strictly within the contract's allowed-file boundary — data layer first (no HTTP), then routes and services, then the entry point, then tests. Each phase verifies its acceptance criteria before proceeding.

**Test** → Tests are ported 1-for-1 against the legacy assertions using `TestClient` + `dependency_overrides` + `StaticPool` in-memory SQLite. Legacy tests remain green throughout.

**Prove** → Bob runs a post-migration audit: full pytest suite, import smoke test, OpenAPI route verification, endpoint smoke tests, schema parity check, Flask-import leak scan, and legacy `.query` usage scan. Results are written to `reforge/validation_report.md`.

## Setup

**Run the legacy Flask app:**
```bash
cd legacy-flask-app
pip install flask flask-sqlalchemy pytest
python app.py
# Starts on http://localhost:5000
```

**Run the migrated FastAPI app:**
```bash
cd fastapi-app
pip install fastapi==0.141.1 sqlalchemy==2.0.52 pydantic==2.13.4 uvicorn==0.49.0 httpx2
uvicorn main:app --reload
# Starts on http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

**Run the test suites:**
```bash
# Legacy (must run from legacy-flask-app/)
cd legacy-flask-app
pytest tests/ -v

# FastAPI (must run from fastapi-app/)
cd fastapi-app
pytest tests/ -v
```

**Endpoints (both apps):**
```
POST /auth/register    body: {"username": "...", "email": "..."}
GET  /users
GET  /products
POST /products         body: {"name": "...", "price": 0.0}
```

## Evidence

All migration evidence is in [`reforge/`](reforge/):

| File | Contents |
|---|---|
| [`reforge/recon.md`](reforge/recon.md) | Pre-migration analysis: file inventory, dependency map, endpoint inventory, risk list, deprecated patterns |
| [`reforge/migration_contract.md`](reforge/migration_contract.md) | Binding contract: invariants, phase boundaries, allowed files, forbidden changes, acceptance criteria, rollback points, human-review items |
| [`reforge/baseline.md`](reforge/baseline.md) | Initial legacy state: directory structure, schema, known defects, pre- and post-fix test runs |
| [`reforge/human_review.md`](reforge/human_review.md) | Architectural decisions G1–G6 with exact implementations and verification evidence |
| [`reforge/migration_log.md`](reforge/migration_log.md) | Chronological execution log: every file created or modified per phase, every acceptance check output |
| [`reforge/validation_report.md`](reforge/validation_report.md) | Final audit: 10/10 tests, 4/4 routes, column-level schema parity, smoke test results, known deviations |

## Limitations
MVP supports the synthetic Flask → FastAPI benchmark only. The migration contract, phase structure, and test infrastructure are hand-designed for this specific codebase. Extension to arbitrary repositories would require Bob to generate the contract and phase plan dynamically from a broader recon pass.

## Bob report
The full IBM Bob session transcript for this migration is exported at [`bob-task-1df4de6f1cfef73f7c58c0bfafbf1c34-2026-09-26.md`](bob-task-1df4de6f1cfef73f7c58c0bfafbf1c34-2026-09-26.md). It contains the complete conversation: recon, contract authoring, Phases A–D implementation, cross-phase review, post-migration audit, and documentation generation.
