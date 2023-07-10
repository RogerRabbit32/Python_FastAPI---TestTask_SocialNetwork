from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostIn(BaseModel):
    title: Optional[str]
    text: str


class PostUpdate(BaseModel):
    title: Optional[str]
    text: Optional[str]


class PostOut(BaseModel):
    id: int
    title: Optional[str]
    text: str
    author_id: int
    created_at: datetime

    class Config:
        orm_mode = True
