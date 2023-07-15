from sqlalchemy.orm import Session

from accounts.schemas import UserIn
from accounts.models import User
from accounts.hashing import get_password_hash


async def verify_unique_login(username: str, db: Session):
    """ Checks if the provided login is unique for the DB """
    return True if db.query(User).filter(User.username == username).first() is None else False


async def verify_unique_email(email: str, db: Session):
    """ Checks if the provided email is unique for the DB """
    return True if db.query(User).filter(User.email == email).first() is None else False


async def create_new_user(request: UserIn, db: Session):
    """ Creates new user with the provided credentials in the DB """
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


def get_user_by_username(username: str, db: Session):
    """ Retrieves user from the DB by username """
    return db.query(User).filter(User.username == username).first()
