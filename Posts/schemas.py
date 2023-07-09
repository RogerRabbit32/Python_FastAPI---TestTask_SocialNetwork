from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostIn(BaseModel):
    title: Optional[str]
    text: str
    author: str

    class Config:
        orm_mode = True


class PostOut(BaseModel):
    id: int
    title: str
    text: str
    author: str
    created_at: datetime

    class Config:
        orm_mode = True
