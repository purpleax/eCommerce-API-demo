from datetime import timedelta
from typing import Any

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import crud, schemas
from .auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password
from .database import SessionLocal, init_db, reset_database
from .dependencies import get_current_admin, get_current_user, get_db
from .seed_data import seed

app = FastAPI(title="API-Driven Commerce Demo", version="1.0.0")

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cache_control_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers.setdefault("Pragma", "no-cache")
    response.headers.setdefault("Expires", "0")
    return response


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


@app.post("/api/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> Any:
    try:
        user = crud.create_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user


@app.post("/api/auth/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)) -> schemas.Token:
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(
        subject=user.email, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return schemas.Token(access_token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@app.get("/api/users/me", response_model=schemas.UserRead)
def get_me(current_user=Depends(get_current_user)) -> Any:
    return current_user


@app.get("/api/products", response_model=list[schemas.ProductRead])
def list_products(db: Session = Depends(get_db)) -> Any:
    return crud.list_products(db)


@app.post("/api/products", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
) -> Any:
    _ = current_admin
    return crud.create_product(db, payload)


@app.put("/api/products/{product_id}", response_model=schemas.ProductRead)
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
) -> Any:
    _ = current_admin
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return crud.update_product(db, product, payload)


@app.delete("/api/products/{product_id}", response_class=Response)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
) -> Any:
    _ = current_admin
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    crud.delete_product(db, product)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/cart", response_model=schemas.CartSummary)
def get_cart(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    items = crud.get_cart_items(db, current_user)
    subtotal = crud.calculate_cart_total(items)
    return schemas.CartSummary(items=items, subtotal=subtotal)


@app.post("/api/cart/items", response_model=schemas.CartItemRead, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: schemas.CartItemCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return crud.add_cart_item(db, current_user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.put("/api/cart/items/{item_id}", response_model=schemas.CartItemRead)
def update_cart_item(
    item_id: int,
    payload: schemas.CartItemUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    cart_item = crud.get_cart_item(db, current_user, item_id)
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    try:
        return crud.update_cart_item(db, cart_item, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.delete("/api/cart/items/{item_id}", response_class=Response)
def delete_cart_item(
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    cart_item = crud.get_cart_item(db, current_user, item_id)
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    crud.delete_cart_item(db, cart_item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/orders", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    _: schemas.OrderCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    try:
        return crud.create_order_from_cart(db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/api/orders", response_model=list[schemas.OrderRead])
def list_orders(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    return crud.list_orders(db, current_user)


@app.post("/api/admin/reset", response_model=schemas.ResetResponse)
def reset_store(
    current_admin=Depends(get_current_admin), db: Session = Depends(get_db)
) -> Any:
    _ = current_admin
    db.close()
    reset_database()
    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()
    return schemas.ResetResponse()


@app.patch("/api/admin/users/{user_id}", response_model=schemas.UserRead)
def update_user_admin_status(
    user_id: int,
    payload: schemas.AdminUserUpdate,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Any:
    _ = current_admin
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_admin.id and not payload.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin access",
        )
    if user.is_admin and not payload.is_admin:
        remaining = crud.count_admins(db)
        if remaining <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one admin account must remain",
            )
    return crud.set_user_admin_status(db, user, payload.is_admin)


@app.get("/api/admin/users", response_model=list[schemas.UserRead])
def admin_list_users(current_admin=Depends(get_current_admin), db: Session = Depends(get_db)) -> Any:
    _ = current_admin
    return crud.list_users(db)


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
