from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth, models, schemas


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.scalar(select(models.User).where(models.User.email == email))


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    hashed_password = auth.get_password_hash(payload.password)
    db_user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hashed_password,
        is_admin=payload.is_admin,
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Email already registered") from exc
    db.refresh(db_user)
    return db_user


def list_products(db: Session) -> Iterable[models.Product]:
    return db.scalars(select(models.Product).where(models.Product.is_active == True)).all()  # noqa: E712


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.get(models.Product, product_id)


def create_product(db: Session, payload: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        inventory_count=payload.inventory_count,
        image_url=payload.image_url,
        is_active=payload.is_active,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(
    db: Session, product: models.Product, payload: schemas.ProductUpdate
) -> models.Product:
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(product, field, value)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: models.Product) -> None:
    db.delete(product)
    db.commit()


def get_cart_items(db: Session, user: models.User) -> list[models.CartItem]:
    return (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == user.id)
        .join(models.Product)
        .all()
    )


def add_cart_item(
    db: Session, user: models.User, payload: schemas.CartItemCreate
) -> models.CartItem:
    product = get_product(db, payload.product_id)
    if not product or not product.is_active:
        raise ValueError("Product not found")
    existing_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == user.id,
            models.CartItem.product_id == payload.product_id,
        )
        .first()
    )
    new_quantity = payload.quantity + (existing_item.quantity if existing_item else 0)
    if product.inventory_count < new_quantity:
        raise ValueError("Insufficient inventory")
    cart_item = existing_item
    if cart_item:
        cart_item.quantity = new_quantity
    else:
        cart_item = models.CartItem(
            user_id=user.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item(
    db: Session, cart_item: models.CartItem, payload: schemas.CartItemUpdate
) -> models.CartItem:
    product = cart_item.product
    if product.inventory_count < payload.quantity:
        raise ValueError("Insufficient inventory")
    cart_item.quantity = payload.quantity
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def delete_cart_item(db: Session, cart_item: models.CartItem) -> None:
    db.delete(cart_item)
    db.commit()


def get_cart_item(db: Session, user: models.User, item_id: int) -> Optional[models.CartItem]:
    return (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == user.id, models.CartItem.id == item_id)
        .first()
    )


def calculate_cart_total(items: Iterable[models.CartItem]) -> Decimal:
    total = Decimal("0.00")
    for item in items:
        total += Decimal(item.product.price) * item.quantity
    return total


def create_order_from_cart(db: Session, user: models.User) -> models.Order:
    cart_items = get_cart_items(db, user)
    if not cart_items:
        raise ValueError("Cart is empty")

    total = calculate_cart_total(cart_items)
    order = models.Order(user_id=user.id, total_amount=total)
    db.add(order)
    db.flush()

    for item in cart_items:
        if item.product.inventory_count < item.quantity:
            raise ValueError("Insufficient inventory for order")
        item.product.inventory_count -= item.quantity
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price,
        )
        db.add(order_item)
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, user: models.User) -> list[models.Order]:
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
