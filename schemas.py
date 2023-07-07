from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserIn(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class PostOut(BaseModel):
    id: int
    title: str
    text: str
    author: str
    created_at: datetime

    class Config:
        orm_mode = True
