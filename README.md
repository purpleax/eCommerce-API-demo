# API-Driven Commerce Demo

A self-contained ecommerce storefront for showcasing API discovery, themed as **Apex Motorsport Outfitters**. The backend exposes a FastAPI-powered JSON API for authentication, product catalog, shopping cart, and order workflows. The frontend is a lightweight single-page site that invokes the API for every action.

## Features
- Token-based authentication with user registration and admin roles
- Product catalog CRUD endpoints with sample motorsport apparel and pit-lane gear
- Admin console includes datastore reset, user promotion controls, and live user registry views
- Persistent SQLite storage for users, products, carts, and orders
- Shopping cart APIs supporting add/update/remove with live stock validation and checkout enforcement
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

> The startup routine seeds three demo products and an admin account (`admin@example.com` / `admin123`). Update the password by editing `ADMIN_PASSWORD` in `backend/app/seed_data.py`, and change `SECRET_KEY` in `backend/app/auth.py` before deploying anywhere non-demo. All self-registered accounts start as shoppers; promote them from the Admin Tools panel when needed.

## Docker Usage
```bash
docker build -t api-commerce-demo .
docker run --rm -p 8000:8000 api-commerce-demo
```
The container exposes the FastAPI app on port 8000 and serves the static frontend from `/`. Configure your CDN to forward `/api/v1/*` to the container if desired.

Or run with Docker Compose:

```bash
docker compose up --build
```

### Automated UAT Simulation
Install the lightweight dependency once (`pip install requests`) and use the helper script to exercise real API flows from any terminal:

```bash
python3 scripts/uat_simulation.py --base-url http://localhost:8000/api/v1 --iterations 3 --users 3 --cart-actions 2
```

The script signs in with the bundled demo users, fills carts, and completes checkout to mimic real shoppers. Key options:

| Flag | Default | Description |
| ---- | ------- | ----------- |
| `--base-url` | `http://shop.exampledomain.com/api/v1` | Root API endpoint (include `/api/v1`). Point this at your deployed environment when testing remotely. |
| `--iterations` | `1` | Number of times to repeat the full simulation loop. Useful for burn-in smoke tests. |
| `--users` | `3` | How many of the bundled accounts to exercise (`1-3`). |
| `--delay` | `0.0` | Seconds to wait between iterations. |
| `--cart-actions` | `2` | When paired with `--purchase-mode random`, controls how many random add-to-cart operations happen before checkout. |
| `--purchase-mode` | `random` | `random` keeps the legacy behavior, picking random products per user. `all` adds every product that currently has inventory. |
| `--default-product-quantity` | `1` | Baseline quantity to add for each item when `--purchase-mode all` is active. Must be a positive integer. |
| `--product-quantity KEY=QTY` | _repeatable_ | Override the default quantity for a specific product in all-products mode. Use either the product id (`12=4`) or the exact name (`"carbon helmet"=2`). Repeat the flag for multiple overrides. |

Example: add every product once, but buy four of product id `5` and three of the item named "Trackside Gloves":

```bash
python3 scripts/uat_simulation.py \
  --base-url http://localhost:8000/api/v1 \
  --purchase-mode all \
  --default-product-quantity 1 \
  --product-quantity 5=4 \
  --product-quantity "Trackside Gloves"=3
```

The script automatically caps requested quantities at remaining inventory and logs any 400-level responses (such as insufficient stock) so you can spot issues quickly.

## API Overview
The full OpenAPI definition lives at `backend/openapi.yaml` for importing into discovery tools. FastAPI also serves the live schema at `/openapi.json` when the app is running.

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/api/v1/auth/register` | Create a user account (optionally admin) |
| `POST` | `/api/v1/auth/login` | Obtain a bearer token using email/password |
| `GET` | `/api/v1/users/me` | Fetch the current profile |
| `GET` | `/api/v1/products` | List active products |
| `POST` | `/api/v1/products` | Create product (admin) |
| `PUT` | `/api/v1/products/{id}` | Update product (admin) |
| `DELETE` | `/api/v1/products/{id}` | Delete product (admin) |
| `GET` | `/api/v1/cart` | Retrieve cart summary for the current user |
| `POST` | `/api/v1/cart/items` | Add item to cart |
| `PUT` | `/api/v1/cart/items/{id}` | Update cart item quantity |
| `DELETE` | `/api/v1/cart/items/{id}` | Remove cart item |
| `POST` | `/api/v1/orders` | Place order using current cart |
| `GET` | `/api/v1/orders` | List order history |
| `POST` | `/api/v1/admin/reset` | Reset and reseed the datastore (admin) |
| `GET` | `/api/v1/admin/users` | List registered users (admin) |

All protected endpoints expect an `Authorization: Bearer <token>` header using the token from `/api/v1/auth/login`.

## Frontend Notes
- The static app lives in `frontend/` and is bundled into the FastAPI container via `StaticFiles`.
- A bot challenge script (`frontend/_fs-ch-1T1wmsGaOgGaSxcX/challenge.js`) is included as a placeholder to resolve loading errors in the frontend. This should be replaced with a proper bot protection solution if needed.
- Override the API base URL by setting `window.API_BASE_URL` before loading `app.js` (useful when front and API live on different origins).
- Every UI interaction triggers a documented REST endpoint, making it ideal for API discovery demonstrations.

## Persistence & Data
- SQLite database file: `backend/app.db`
- SQLAlchemy models in `backend/app/models.py`
- Demo seed data defined in `backend/app/seed_data.py`
  - Includes a curated catalog of 12 motorsport apparel & gear items for demos

Resetting the demo is as simple as deleting `backend/app.db`; the next startup will recreate and reseed the database.
You can also call the admin-only endpoint `POST /api/v1/admin/reset` to drop and reseed the database without filesystem access.
