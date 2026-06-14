from fastapi import FastAPI
from contextlib import asynccontextmanager
from config import CONFIG as config
from datetime import datetime
from api.users import router as users_router
from api.articles import router as articles_router
from api.likes import router as likes_router
from api.tags import router as tags_router
import logging

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("="*60)
    logger.info("✔Start up successfully!")
    logger.info(f"🌏name:{config.name};version:{config.version};⏰Start time:{datetime.now()};")
    yield
    logger.info("="*60)
    logger.info("✔Shut down successfully!")

app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(articles_router)
app.include_router(likes_router)
app.include_router(tags_router)

@app.get("/")
def root():
    return {"message":"Hello World!"}
