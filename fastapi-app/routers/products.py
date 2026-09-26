from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.product import ProductCreate, ProductRead
from services.product_service import list_products, create_product

router = APIRouter()


@router.get("", status_code=200, response_model=list[ProductRead])
def get_products(db: Session = Depends(get_db)):
    return list_products(db)


@router.post("", status_code=201, response_model=ProductRead)
def add_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, payload.name, payload.price)
