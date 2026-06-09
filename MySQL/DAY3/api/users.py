from database import get_redis
from fastapi import APIRouter,HTTPException
from db import db
from pydantic import BaseModel

router = APIRouter()

class User(BaseModel):
    username:str
    userpassword:str
    email:str


@router.post("/logup")
def logup(user:User):
    redis = get_redis()
    name = db.fetch_one("SELECT username FROM users WHERE username = %s",(user.username,))

    if name:
        raise HTTPException(status_code=409,detail="Username already exists")
    
