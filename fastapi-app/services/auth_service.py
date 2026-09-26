from sqlalchemy.orm import Session
from sqlalchemy import select
from models.user import User


def create_user(db: Session, username: str, email: str) -> User:
    """Create a new user. Raises ValueError on duplicate email or username."""
    existing_email = db.scalar(select(User).where(User.email == email))
    if existing_email:
        raise ValueError("Email already registered")

    existing_username = db.scalar(select(User).where(User.username == username))
    if existing_username:
        raise ValueError("Username already taken")

    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    """Return all users."""
    return list(db.scalars(select(User)).all())
