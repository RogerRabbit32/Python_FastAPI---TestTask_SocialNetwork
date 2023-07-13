from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from Accounts.schemas import UserIn, UserOut, Token
from Accounts.models import User
from Accounts.hashing import verify_password
from Accounts.authorization import create_access_token
from Accounts.crud import verify_unique_login, verify_unique_email, create_new_user
from Accounts.external_apis import verify_email, enrich_email


router = APIRouter(tags=["Users"])

HUNTER_KEY = "e8731105dfbeb32b50948bb25f4bf832d9cf1b08"
CLEARBIT_KEY = "sk_76c74f169b3ab6746933737eb9535c1e"


@router.post("/signup", response_model=UserOut)
async def register_user(request: UserIn, db: Session = Depends(get_db)):
    await verify_unique_login(db, request.username)
    await verify_unique_email(db, request.email)

    # Email existence verification, using hunter.io API call
    email_verification = await verify_email(request.email, HUNTER_KEY)
    if not email_verification["data"]["status"] or "status" not in email_verification["data"]:
        # Bypass email verification if required fields are not present in the API response
        pass
    elif email_verification["data"]["status"] == "invalid":
        raise HTTPException(status_code=400, detail="Email existence verification failed")

    # Get more data on user, using Clearbit API call
    additional_data = await enrich_email(request.email, CLEARBIT_KEY)
    if additional_data:
        # We'll get the user's full name if it wasn't provided
        user_data = additional_data.get("person", {})
        if user_data and not request.full_name:
            request.full_name = user_data.get("name", {}).get("fullName", request.full_name)

    new_user = await create_new_user(request, db)
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
