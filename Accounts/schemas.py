from pydantic import BaseModel, Field, EmailStr, validator


login_regex = r"^[a-zA-Z0-9]+$"
password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?!.*\s).+$"


class UserIn(BaseModel):
    username: str = Field(..., regex=login_regex)
    email: EmailStr
    password: str = Field(..., regex=password_regex)
    full_name: str | None = None

    @validator('username')
    def username_requirements(cls, value):
        if len(value) < 4 or len(value) > 20:
            raise ValueError("Username must be between 4 and 20 characters long")
        return value

    @validator('password')
    def password_requirements(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
