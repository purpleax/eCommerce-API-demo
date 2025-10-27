from sqlalchemy.orm import Session

from . import models
from .auth import get_password_hash


SAMPLE_PRODUCTS = [
    {
        "name": "Ayrton Senna Scale Helmet",
        "description": "1985 Ayrton Senna 1:2 Scale Helmet with box",
        "price": 250.00,
        "inventory_count": 15000,
        "image_url": "https://i.ibb.co/XZGH8VNj/ayrton-senna-12-scale-helmet-1985-6002297-600.jpg",
    },
    {
        "name": "Nigel Mansell Scale Helmet",
        "description": "Nigel Mansell 1:2 Scale Helmet!",
        "price": 199.00,
        "inventory_count": 100000,
        "image_url": "https://i.ibb.co/xtp5t96V/Mansell.jpg",
    },
    {
        "name": "Alain Prost Helmet",
        "description": "Alain Prost 1:2 Scale Helmet",
        "price": 149.00,
        "inventory_count": 4087770,
        "image_url": "https://i.ibb.co/DfK0LkjC/Prost-Helmet.jpg",
    },
    {
        "name": "Alan Jones Helmet",
        "description": "Alan Jones 1:2 Scale Helmet",
        "price": 149.00,
        "inventory_count": 67870,
        "image_url": "https://i.ibb.co/hJzhrCCT/Alan-Jones.jpg",
    },
    {
        "name": "Daniel Ricciardo Helmet",
        "description": "Daniel Ricciardo 1:2 scale helmet",
        "price": 199.00,
        "inventory_count": 367885,
        "image_url": "https://i.ibb.co/jZvtrG2r/Daniel-Ricciardo.jpg",
    },
    {
        "name": "Michael Schumacher Helmet",
        "description": "Michael Schumacher 1:2 Scale Helmet",
        "price": 189.00,
        "inventory_count": 7788725,
        "image_url": "https://i.ibb.co/Lzx9p7KD/schumacher.jpg",
    },
    {
        "name": "Max Verstappen Helmet",
        "description": "Max Verstappen 1:2 Scale Helmet",
        "price": 449.00,
        "inventory_count": 277880,
        "image_url": "https://i.ibb.co/8LfW8zWf/Verstappen.png",
    },
    {
        "name": "Mika Hakkinen Helmet",
        "description": "Mika Hakkinen 1:2 Scale Helmet",
        "price": 389.00,
        "inventory_count": 57860,
        "image_url": "https://i.ibb.co/Y7JWPJNH/Hakkinen.jpg",
    },
    {
        "name": "Fernando Alonso Helmet",
        "description": "Fernando Alonso 1:2 Scale Helmet",
        "price": 250.00,
        "inventory_count": 16778,
        "image_url": "https://i.ibb.co/bRvnHKHK/fernando-alonso-2025-saudi-arabian-gp-mini-hemet-bell-1-2-scale.jpg",
    },
    {
        "name": "Sebastian Vettel Helmet",
        "description": "Sebastian Vettel 1:2 scale helmet",
        "price": 179.00,
        "inventory_count": 30777,
        "image_url": "https://i.ibb.co/HptjxWnj/casque-helmet-12-sebastian-vettel-f1-2020-arai.jpg",
    },
    {
        "name": "Charles Leclerc Helmet",
        "description": "Charles Leclerc 1:2 scale helmet",
        "price": 279.00,
        "inventory_count": 677880,
        "image_url": "https://i.ibb.co/mCkq7dgV/charles-leclerc-scuderia-ferrari-autographed-1-2-scale-formula-1-mini-helmet.jpg",
    },
    {
        "name": "Oscar Piastri Helmet",
        "description": "Oscar Piastri 1:2 Scale Helmet",
        "price": 329.00,
        "inventory_count": 27772,
        "image_url": "https://i.ibb.co/fYY0JcSS/Piastri.jpg",
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
