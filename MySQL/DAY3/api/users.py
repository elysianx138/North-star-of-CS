from database import get_redis
from fastapi import APIRouter,HTTPException
from db import db
from pydantic import BaseModel
import random

router = APIRouter()

class User(BaseModel):
    username:str
    userpassword:str
    email:str


@router.post("/logup")
def logup(user:User):
    redis = get_redis()

    # search username in User_db and Redis
    name = redis.hgetall(f"user:{user.username}")
    if name:
        raise HTTPException(status_code=409,detail="Username already exists")
    name = db.fetch_one("SELECT username FROM users WHERE username = %s",(user.username,))
    if name:
        raise HTTPException(status_code=409,detail="Username already exists")
    
    new_id = db.insert("INSERT INTO users (username,userpassword,email) VALUES (%s,%s,%s)",(user.username,user.userpassword,user.email))

    redis.hset(f"user:{user.username}",mapping={
        "username":user.username,
        "email":user.email,
        "password":user.userpassword
    })
    redis.expire(f"user:{user.username}",300+random.randint(0,120))

    return {"message":"User created successfully","id":new_id}
    
@router.post("/login")
def login(user:User):
    redis = get_redis()
    
    usr = redis.hgetall(f"user:{user.username}")
    if usr.get("__NULL__"):
        raise HTTPException(status_code=404,detail="User not found")
    if not usr:
        row = db.fetch_one("SELECT username,userpassword FROM users WHERE username = %s AND userpassword = %s",(user.username,user.userpassword))
        if not row:
            redis.hset(f"user:{user.username}",mapping={"__NULL__":"1"})
            redis.expire(f"user:{user.username}",15+random.randint(0,20))
            raise HTTPException(status_code=404,detail="User not found")
        redis.hset(f"user:{user.username}",mapping={
            "username":user.username,
            "password":user.userpassword
        })
        redis.expire(f"user:{user.username}",300+random.randint(0,120))
        usr = redis.hgetall(f"user:{user.username}")
    return {"username":usr.get("username"),"password":usr.get("password")}