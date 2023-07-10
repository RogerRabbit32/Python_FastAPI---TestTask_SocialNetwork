from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from Accounts.schemas import UserIn, UserOut, Token
from Accounts.models import User
from Accounts.hashing import get_password_hash, verify_password
from Accounts.authorization import create_access_token


router = APIRouter(tags=["Users"])


@router.post("/signup", response_model=UserOut)
def register_user(request: UserIn, db: Session = Depends(get_db)):
    # Check if the login is unique
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(
            status_code=400, detail="Login already exists"
        )
    # Check if the email is unique
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(
            status_code=400, detail="Email already exists"
        )

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


@router.post("/login", response_model=Token)
def login_user(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check the user credentials
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=401,
            detail=f"Invalid credentials"
        )
    # Generate the JWT token for the user
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
