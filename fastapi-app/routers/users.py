from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.user import UserRead
from services.auth_service import list_users

router = APIRouter()


@router.get("", status_code=200, response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)):
    return list_users(db)
