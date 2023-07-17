import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from accounts.schemas import UserIn, UserOut, Token
from accounts.hashing import verify_password
from accounts.authorization import create_access_token
from accounts.crud import verify_unique_login, verify_unique_email, create_new_user, get_user_by_username
from accounts.externalapis import verify_email, enrich_email


router = APIRouter(tags=["Users"])

HUNTER_KEY = os.environ.get('HUNTER_API_KEY', '')
CLEARBIT_KEY = os.environ.get('CLEARBIT_API_KEY', '')


@router.post("/signup", response_model=UserOut)
async def register_user(request: UserIn, db: Session = Depends(get_db)):
    # Username and email uniqueness verification
    login_is_unique = await verify_unique_login(request.username, db)
    if login_is_unique is False:
        raise HTTPException(status_code=400, detail="Login already exists")
    email_is_unique = await verify_unique_email(request.email, db)
    if email_is_unique is False:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Email existence verification, using hunter.io API call
    try:
        email_verification_status = await verify_email(request.email, HUNTER_KEY)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email verification unavailable. {str(e)}")

    if email_verification_status is None:
        pass  # Bypass email verification if required fields are not present in the API response
    elif email_verification_status == "invalid":
        raise HTTPException(status_code=400, detail="Email existence verification failed. "
                                                    "Please provide a valid email")

    # Get more data on user, using Clearbit API call
    additional_data = await enrich_email(request.email, CLEARBIT_KEY)
    if request.full_name is None and additional_data is not None:
        # We'll get the user's full name if it wasn't provided
        request.full_name = additional_data.get("name", {}).get("fullName", request.full_name)

    # Create new user in the DB
    new_user = await create_new_user(request, db)
    return new_user


@router.post("/login", response_model=Token)
def login_user(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check the user credentials
    user = get_user_by_username(request.username, db)
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail=f"Invalid credentials")
    # Generate the JWT token for the user
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
