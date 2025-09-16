from sqlalchemy.orm import Session

from . import models
from .auth import get_password_hash


SAMPLE_PRODUCTS = [
    {
        "name": "Acme Rocket Skates",
        "description": "High-speed skates for stylish escapes.",
        "price": 199.99,
        "inventory_count": 12000,
        "image_url": "https://picsum.photos/seed/rocket-skates/400/300",
    },
    {
        "name": "Invisibility Cloak",
        "description": "Disappear in plain sight with this premium cloak.",
        "price": 349.50,
        "inventory_count": 50000,
        "image_url": "https://picsum.photos/seed/invisibility-cloak/400/300",
    },
    {
        "name": "Quantum Coffee Maker",
        "description": "Brew the perfect cup by collapsing the waveform of flavor.",
        "price": 129.00,
        "inventory_count": 200000,
        "image_url": "https://picsum.photos/seed/quantum-coffee/400/300",
    },
]


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Store Admin"


def seed(db: Session) -> None:
    if not db.query(models.User).filter(models.User.email == ADMIN_EMAIL).first():
        db.add(
            models.User(
                email=ADMIN_EMAIL,
                full_name=ADMIN_NAME,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_admin=True,
            )
        )

    if db.query(models.Product).count() == 0:
        for data in SAMPLE_PRODUCTS:
            db.add(models.Product(**data))

    db.commit()
