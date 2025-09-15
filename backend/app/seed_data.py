from sqlalchemy.orm import Session

from . import models


SAMPLE_PRODUCTS = [
    {
        "name": "Acme Rocket Skates",
        "description": "High-speed skates for stylish escapes.",
        "price": 199.99,
        "inventory_count": 12,
        "image_url": "https://picsum.photos/seed/rocket-skates/400/300",
    },
    {
        "name": "Invisibility Cloak",
        "description": "Disappear in plain sight with this premium cloak.",
        "price": 349.50,
        "inventory_count": 5,
        "image_url": "https://picsum.photos/seed/invisibility-cloak/400/300",
    },
    {
        "name": "Quantum Coffee Maker",
        "description": "Brew the perfect cup by collapsing the waveform of flavor.",
        "price": 129.00,
        "inventory_count": 20,
        "image_url": "https://picsum.photos/seed/quantum-coffee/400/300",
    },
]


ADMIN_USER = {
    "email": "admin@example.com",
    "full_name": "Store Admin",
    "hashed_password": "$2b$12$zC8b9H4dJ8nAJfJ6q7OQuuDVV/znLWMSM.V/S1P5ITuyK9V40zdHy",
    "is_admin": True,
}
# The hashed password corresponds to "admin123"


def seed(db: Session) -> None:
    if not db.query(models.User).filter(models.User.email == ADMIN_USER["email"]).first():
        db.add(models.User(**ADMIN_USER))

    if db.query(models.Product).count() == 0:
        for data in SAMPLE_PRODUCTS:
            db.add(models.Product(**data))

    db.commit()
