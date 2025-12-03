# Architecture Overview

## Summary
- **Purpose**: Demonstrates an end-to-end ecommerce experience where a FastAPI backend powers storefront, cart, and order workflows while a lightweight JavaScript frontend consumes the API in real time.
- **Runtime model**: A single Uvicorn process hosts both the JSON API under `/api/v1` and the static frontend assets at `/`, so deployments only need one container or process.
- **Data flow**: Requests enter FastAPI, which authenticates users with JWT bearer tokens, validates input via Pydantic schemas, and persists state through SQLAlchemy sessions backed by SQLite. Static assets are served directly by FastAPI’s `StaticFiles` mount.
- **Key personas**: Shoppers register, manage carts, and place orders; admins can reset seed data, promote users, and manage inventory over the same API surface.
- **Tooling**: A UAT simulation script (`scripts/uat_simulation.py`) exercises the API programmatically, optionally purchasing every product to validate catalog integrity.

## System Architecture

### Backend API
The backend lives in `backend/app/` as a FastAPI application. Key modules include:
- `main.py`: Configures the FastAPI app, registers routes, and mounts the frontend directory. Routes cover authentication, products, cart, orders, and admin utilities.
- `schemas.py`: Pydantic models that validate request/response payloads and drive automatic OpenAPI generation.
- `crud.py`: Encapsulates database operations for users, products, carts, and orders to keep route handlers thin.
- `database.py` & `models.py`: Define SQLAlchemy ORM models and session management. The default engine targets SQLite but can be swapped by adjusting environment variables.
- `seed_data.py`: Populates the catalog and creates an admin account on startup or reset.
- `auth.py` & `dependencies.py`: Handle password hashing, JWT token management, and reusable FastAPI dependency injection for authenticated contexts.

### Frontend
Static files under `frontend/` (`index.html`, `app.js`, `styles.css`) implement a basic SPA experience. The frontend calls the REST API for every mutation or data fetch, making it a working reference client for the backend contract. During startup, `main.py` mounts this directory with `StaticFiles(directory=FRONTEND_DIR, html=True)` so hitting `/` serves `index.html` alongside the API documentation at `/docs`.

### Persistence Layer
By default, the project uses SQLite (`backend/app.db`) for a self-contained demo. SQLAlchemy abstracts database access, so pointing to another RDBMS only requires updating the database URL. `crud.py` centralizes all create/read/update/delete logic to keep transactional boundaries consistent. Seed routines reset inventory levels to known values for reliable demos.

### Deployment Bundles
- **Docker**: The root `Dockerfile` builds a single image that installs backend dependencies, copies the frontend, and launches Uvicorn serving both API and static content.
- **Docker Compose**: `docker-compose.yml` orchestrates the image with sensible defaults for local testing.
- **Local Python**: The `README.md` documents a virtualenv-based setup for running the API directly.

### Supporting Scripts
- `scripts/uat_simulation.py`: Exercises core shopper flows, now supporting an "all products" purchase mode and per-product quantity overrides for regression testing.
- `scripts/admin_tools.py`: Provides command-line helpers for administrative tasks (refer to the script for details).

## Content Serving Model
FastAPI serves dynamic endpoints under `/api/v1/*`. The same ASGI application mounts the `frontend/` directory at the root path using `StaticFiles`, so requests to `/`, `/styles.css`, or `/app.js` are served directly from disk. This design keeps the deployment footprint minimal—no separate web server or CDN is required for the demo, though static assets can be offloaded in production by disabling the mount and hosting them elsewhere.

## Authentication & Session Flow
1. Shoppers register via `POST /api/v1/auth/register` or log in through `POST /api/v1/auth/login`.
2. Successful login returns a JWT access token stored client-side (frontend keeps it in memory/local storage; scripts hold it in memory).
3. Authenticated requests include `Authorization: Bearer <token>`; FastAPI dependencies validate the token, load the user, and enforce role-based checks (e.g., admin-only endpoints).
4. Cart and order operations run within database sessions managed by `dependencies.py`, ensuring consistent state even under concurrent requests.

## Technologies
- **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, Pydantic, Passlib, python-jose.
- **Frontend**: Vanilla HTML/CSS/JavaScript; no build step required.
- **Database**: SQLite by default (can be swapped with any SQLAlchemy-compatible RDBMS).
- **Tooling**: Docker/Docker Compose for containerization, Requests for scripted API interactions, Pydantic-generated OpenAPI spec (`backend/openapi.yaml`).

## API Documentation & Swagger Support
- FastAPI automatically exposes interactive docs at `/docs` (Swagger UI) and `/redoc`. These UIs are backed by the same OpenAPI definition generated from the route and schema declarations.
- The OpenAPI schema is also committed to source control (`backend/openapi.yaml`) so it can be imported into external tooling or kept in sync with contract testing suites.
- When deploying, no extra configuration is needed—Uvicorn serves the interactive documentation alongside the API and static frontend, making it simple for integrators to discover endpoints and sample payloads.

## Directory Structure
```
eCommerce-API-demo/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── auth.py
│       ├── crud.py
│       ├── database.py
│       ├── dependencies.py
│       ├── main.py
│       ├── models.py
│       ├── schemas.py
│       └── seed_data.py
├── frontend/
│   ├── _fs-ch-1T1wmsGaOgGaSxcX/
│   │   └── challenge.js
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── scripts/
│   ├── admin_tools.py
│   └── uat_simulation.py
├── backend/openapi.yaml
├── Dockerfile
├── docker-compose.yml
├── README.md
└── architecture.md
```

## Development & Testing Workflow
1. **Setup**: Create a virtual environment, install dependencies (`pip install -r backend/requirements.txt`), and run the API with `uvicorn app.main:app --reload` from `backend/`.
2. **Frontend**: Navigate to `http://localhost:8000` to load the SPA, which immediately interacts with the running API.
3. **Automated checks**: Use `scripts/uat_simulation.py` to validate shopping flows. Combine `--iterations` and `--purchase-mode all` to stress-check inventory handling across multiple cycles.
4. **Admin tasks**: Reset the database via `POST /api/v1/admin/reset` or the provided admin script when you need a clean slate.

Armed with this overview, an engineer can navigate the codebase, understand the runtime topology, and extend the platform—whether by adding new endpoints, enhancing the frontend, or integrating external services.
