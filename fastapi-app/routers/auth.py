from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.user import UserCreate, UserRead
from services.auth_service import create_user

router = APIRouter()


@router.post("/register", status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, payload.username, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "message": "User created successfully",
        "user": UserRead.model_validate(user).model_dump(),
    }
