# API-Driven Commerce Demo

A self-contained ecommerce storefront for showcasing API discovery. The backend exposes a FastAPI-powered JSON API for authentication, product catalog, shopping cart, and order workflows. The frontend is a lightweight single-page site that invokes the API for every action.

## Features
- Token-based authentication with user registration and admin roles
- Product catalog CRUD endpoints with sample inventory seeding
- Persistent SQLite storage for users, products, carts, and orders
- Shopping cart APIs supporting add/update/remove with stock validation
- Order checkout flow that converts cart items into historical orders
- Vanilla JavaScript frontend that demonstrates API usage end-to-end
- Docker image that serves both the API and static frontend from one container

## Tech Stack
- Python 3.11, FastAPI, SQLAlchemy, Passlib, python-jose
- SQLite for persistence
- Vanilla HTML/CSS/JS frontend served by FastAPI StaticFiles
- Uvicorn ASGI server

## Getting Started (Local Python)
1. **Install dependencies**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Run the API + frontend**
   ```bash
   uvicorn app.main:app --reload
   ```
3. **Open the storefront** at [http://localhost:8000](http://localhost:8000). Login, browse products, and exercise the API-driven flows. The interactive docs are available at `/docs`.

> The startup routine seeds three demo products and an admin account (`admin@example.com` / `admin123`). Update the password by editing `ADMIN_PASSWORD` in `backend/app/seed_data.py`, and change `SECRET_KEY` in `backend/app/auth.py` before deploying anywhere non-demo.

## Docker Usage
```bash
docker build -t api-commerce-demo .
docker run --rm -p 8000:8000 api-commerce-demo
```
The container exposes the FastAPI app on port 8000 and serves the static frontend from `/`. Configure your CDN to forward `/api/*` to the container if desired.

### Automated UAT Simulation
Install the lightweight dependency once (`pip install requests`) and use the helper script to exercise the site end-to-end from a macOS (or any) terminal:

```bash
python3 scripts/uat_simulation.py --base-url http://localhost:8000/api --iterations 3 --users 3 --cart-actions 2
```

Flags let you control how many iterations, users (up to the three bundled accounts), how many cart additions occur before checking out, and optional delays between loops. Point `--base-url` at the externally reachable API when running against remote environments.

## API Overview
The full OpenAPI definition lives at `backend/openapi.yaml` for importing into discovery tools. FastAPI also serves the live schema at `/openapi.json` when the app is running.

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/api/auth/register` | Create a user account (optionally admin) |
| `POST` | `/api/auth/login` | Obtain a bearer token using email/password |
| `GET` | `/api/users/me` | Fetch the current profile |
| `GET` | `/api/products` | List active products |
| `POST` | `/api/products` | Create product (admin) |
| `PUT` | `/api/products/{id}` | Update product (admin) |
| `DELETE` | `/api/products/{id}` | Delete product (admin) |
| `GET` | `/api/cart` | Retrieve cart summary for the current user |
| `POST` | `/api/cart/items` | Add item to cart |
| `PUT` | `/api/cart/items/{id}` | Update cart item quantity |
| `DELETE` | `/api/cart/items/{id}` | Remove cart item |
| `POST` | `/api/orders` | Place order using current cart |
| `GET` | `/api/orders` | List order history |

All protected endpoints expect an `Authorization: Bearer <token>` header using the token from `/api/auth/login`.

## Frontend Notes
- The static app lives in `frontend/` and is bundled into the FastAPI container via `StaticFiles`.
- Override the API base URL by setting `window.API_BASE_URL` before loading `app.js` (useful when front and API live on different origins).
- Every UI interaction triggers a documented REST endpoint, making it ideal for API discovery demonstrations.

## Persistence & Data
- SQLite database file: `backend/app.db`
- SQLAlchemy models in `backend/app/models.py`
- Demo seed data defined in `backend/app/seed_data.py`

Resetting the demo is as simple as deleting `backend/app.db`; the next startup will recreate and reseed the database.
