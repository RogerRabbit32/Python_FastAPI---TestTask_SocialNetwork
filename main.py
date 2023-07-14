from fastapi import FastAPI

from database import engine
from posts.models import Base
from accounts.routers import router as accounts_router
from posts.routers import router as posts_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Social network")

app.include_router(accounts_router, prefix="/accounts")
app.include_router(posts_router, prefix="/posts")
