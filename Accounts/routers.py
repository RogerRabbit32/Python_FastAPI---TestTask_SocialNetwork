from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from oauth2 import get_current_user
from models import User
from schemas import UserOut

router = APIRouter()


@router.get("/user/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail=f"User with id {user_id} does not exist"
        )
    return user
