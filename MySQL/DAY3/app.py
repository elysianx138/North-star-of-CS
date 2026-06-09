from fastapi import FastAPI
from contextlib import asynccontextmanager
from config import CONFIG as config
from datetime import datetime
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

@app.get("/")
def root():
    return {"message":"Hello World!"}