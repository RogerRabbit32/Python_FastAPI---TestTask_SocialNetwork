from fastapi import FastAPI

from database import engine
from Posts.models import Base
from Accounts.routers import router as accounts_router
from Posts.routers import router as posts_router

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(accounts_router, prefix="/accounts")
app.include_router(posts_router, prefix="/posts")
