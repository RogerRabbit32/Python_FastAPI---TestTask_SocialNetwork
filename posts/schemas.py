from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr


class PostIn(BaseModel):
    title: Optional[str]
    text: constr(min_length=1)


class PostUpdate(BaseModel):
    title: Optional[str]
    text: Optional[constr(min_length=1)]


class PostOut(BaseModel):
    id: int
    title: Optional[str]
    text: str
    author_id: int
    created_at: datetime

    class Config:
        orm_mode = True
