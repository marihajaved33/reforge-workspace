from sqlalchemy.orm import Session
from sqlalchemy import select
from models.product import Product


def list_products(db: Session) -> list[Product]:
    """Return all products."""
    return list(db.scalars(select(Product)).all())


def create_product(db: Session, name: str, price: float) -> Product:
    """Create and persist a new product."""
    product = Product(name=name, price=price)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
