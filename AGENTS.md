# Repository Guidelines

## Project Structure & Module Organization
- `backend/app/` holds the FastAPI service: `main.py` wires routes, `auth.py` manages JWTs, `crud.py` wraps SQLAlchemy queries, and `schemas.py` defines Pydantic contracts. Keep new modules under this package to reuse shared dependencies from `dependencies.py`.
- `frontend/` contains the static storefront served via `StaticFiles`; update assets here when adjusting UI demos or branding.
- `backend/openapi.yaml` mirrors the live schema for tooling imports, and `scripts/uat_simulation.py` provides scripted shopper flows. SQLite state lives in `backend/app.db`, so delete the file or call `/api/v1/admin/reset` to reseed.

## Build, Test, and Development Commands
- `cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`: bootstrap the API environment.
- `uvicorn app.main:app --reload`: run the API plus static frontend locally with auto-reload.
- `docker compose up --build`: build and serve the combined app via Docker with port 8000 exposed.
- `python3 scripts/uat_simulation.py --base-url http://localhost:8000/api/v1 --iterations 3`: simulate logged-in shoppers end-to-end; useful before merging API changes.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indentation, descriptive snake_case for Python identifiers, and keep module-level constants (e.g., `API_PREFIX`) uppercase.
- Prefer FastAPI type annotations and Pydantic models for request/response validation; extend existing schemas rather than creating ad-hoc dicts.
- Keep SQLAlchemy models and CRUD helpers stateless; pass explicit `Session` objects instead of relying on globals, and format code consistently before committing.

## Testing Guidelines
- There is no bundled unit-test suite yet; add or expand pytest-based checks under `backend/tests/` whenever you introduce non-trivial behavior.
- For regression checks today, rely on `scripts/uat_simulation.py` plus targeted manual calls to `/docs` or `backend/openapi.yaml`-driven clients, and record the scenarios exercised in your PR.
- Seed logic (`seed_data.py`) runs at startup, so regenerate demo data between runs when a change touches inventory or auth flows.

## Commit & Pull Request Guidelines
- Recent history uses concise, imperative messages such as “Added API versioning”; follow that tone and lead with the affected area (`auth: tighten token expiry`).
- Each PR should describe API/DB impacts, include reproduction or test evidence (command output, screenshots of the admin console, or UAT script logs), and link any tracking issues.
- Call out security-sensitive edits (e.g., secret management) and ensure new environment variables are documented in `README.md` or inline comments before requesting review.
