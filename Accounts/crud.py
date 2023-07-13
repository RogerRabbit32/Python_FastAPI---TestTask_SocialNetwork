from fastapi import HTTPException
from sqlalchemy.orm import Session

from Accounts.schemas import UserIn
from Accounts.models import User
from Accounts.hashing import get_password_hash


async def verify_unique_login(db: Session, username: str):
    # Check if the provided login is unique
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Login already exists")


async def verify_unique_email(db: Session, email: str):
    # Check if the provided email is unique
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")


async def create_new_user(request: UserIn, db: Session):
    hashed_password = get_password_hash(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        password=hashed_password,
        full_name=request.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
