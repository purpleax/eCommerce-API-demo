from sqlalchemy.orm import Session

from . import models
from .auth import get_password_hash


SAMPLE_PRODUCTS = [
    {
        "name": "Ayrton Senna Helmet",
        "description": "1985 Ayrton Senna 1:2 Scale Helmet with box",
        "price": 199.00,
        "inventory_count": 15,
        "image_url": "https://ibb.co/svX7Htkb",
    },
    {
        "name": "Velocity GT Race Suit",
        "description": "Ultra-light triple layer Nomex® suit with stretch panels for elite endurance comfort.",
        "price": 1199.00,
        "inventory_count": 10,
        "image_url": "https://picsum.photos/seed/velocity-suit/640/480",
    },
    {
        "name": "Ignition Nomex Gloves",
        "description": "Pre-curved palms, seams outside, and silicone grip zones keep control precise under pressure.",
        "price": 149.00,
        "inventory_count": 40,
        "image_url": "https://picsum.photos/seed/ignition-gloves/640/480",
    },
    {
        "name": "Trackline Flameproof Balaclava",
        "description": "Dual-layer soft knit balaclava with flatlock seams to keep heat out and comfort in.",
        "price": 49.00,
        "inventory_count": 60,
        "image_url": "https://picsum.photos/seed/trackline-balaclava/640/480",
    },
    {
        "name": "Grid Pro Driving Shoes",
        "description": "Featherweight leather upper and thin oil-resistant sole for ultimate pedal feel.",
        "price": 199.00,
        "inventory_count": 35,
        "image_url": "https://picsum.photos/seed/grid-shoes/640/480",
    },
    {
        "name": "Pitlane Crew Jacket",
        "description": "Weatherproof softshell with reflective piping and removable hood for team duty.",
        "price": 189.00,
        "inventory_count": 25,
        "image_url": "https://picsum.photos/seed/pitlane-jacket/640/480",
    },
    {
        "name": "Sprint Series Kart Suit",
        "description": "CIK-FIA Level 2 certified, abrasion resistant panels, and breathable mesh zones.",
        "price": 449.00,
        "inventory_count": 20,
        "image_url": "https://picsum.photos/seed/sprint-suit/640/480",
    },
    {
        "name": "AeroFlow Cooling Undershirt",
        "description": "Moisture-wicking compression top with mapped ventilation for long stints.",
        "price": 89.00,
        "inventory_count": 50,
        "image_url": "https://picsum.photos/seed/aeroflow-shirt/640/480",
    },
    {
        "name": "Nightshift Rain Shell",
        "description": "Fully seam sealed pit wall shell with packable design and hi-vis accents.",
        "price": 159.00,
        "inventory_count": 18,
        "image_url": "https://picsum.photos/seed/nightshift-shell/640/480",
    },
    {
        "name": "Apex Fuelproof Duffel",
        "description": "Tarpaulin-lined gear duffel with ventilated compartments for suits and helmets.",
        "price": 129.00,
        "inventory_count": 30,
        "image_url": "https://picsum.photos/seed/apex-duffel/640/480",
    },
    {
        "name": "Podium Team Polo",
        "description": "Moisture control team polo with contrast taping and sponsor-ready sleeves.",
        "price": 79.00,
        "inventory_count": 60,
        "image_url": "https://picsum.photos/seed/podium-polo/640/480",
    },
    {
        "name": "Telemetry Smartwatch",
        "description": "Race engineer wearable with live stint timing, heart rate telemetry, and pit alert modes.",
        "price": 329.00,
        "inventory_count": 22,
        "image_url": "https://picsum.photos/seed/telemetry-watch/640/480",
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
