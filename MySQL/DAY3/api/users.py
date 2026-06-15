from database import get_redis
from fastapi import APIRouter,HTTPException
from db import db
from pydantic import BaseModel
import random,bcrypt,logging

logger = logging.getLogger(__name__)
router = APIRouter()

class User(BaseModel):
    username:str
    userpassword:str
    email:str


@router.post("/logup")
def logup(user:User):
    logger.info(f"Register attempt:{user.username}")
    redis = get_redis()
    # search username in User_db and Redis
    name = redis.hgetall(f"user:{user.username}")
    if name:
        logger.warning(f"Registration blocked:{user.username} already in Redis")
        raise HTTPException(status_code=409,detail="Username already exists")
    name = db.fetch_one("SELECT username FROM users WHERE username = %s",(user.username,))
    if name:
        logger.warning(f"Registration blocked:{user.username} already in DB")
        raise HTTPException(status_code=409,detail="Username already exists")
    
    hash_pwd = bcrypt.hashpw(user.userpassword.encode(),bcrypt.gensalt()).decode()
    new_id = db.insert("INSERT INTO users (username,userpassword,email) VALUES (%s,%s,%s)",(user.username,hash_pwd,user.email))

    redis.hset(f"user:{user.username}",mapping={
        "username":user.username,
        "email":user.email,
        "password":hash_pwd
    })
    redis.expire(f"user:{user.username}",300+random.randint(0,120))

    logger.info(f"User registered:{user.username},id={new_id}")
    return {"message":"User created successfully","id":new_id}
    
@router.post("/login")
def login(user:User):
    logger.info(f"Login attempt:{user.username}")
    redis = get_redis()
    
    usr = redis.hgetall(f"user:{user.username}")
    if usr and usr.get("password"):
        logger.warning(f"Login failed:wrong password for {user.username}")
        if not bcrypt.checkpw(user.userpassword.encode(),usr.get("password").encode()):
            raise HTTPException(status_code=404,detail="Password not correct")
        
        logger.info(f"Login successfully!{user.username} from cache")
        return {"username":usr.get("username")}
    if usr.get("__NULL__"):
        logger.warning(f"Login blocked:{user.username},querying DB")
        raise HTTPException(status_code=404,detail="User not found")
    
    if not usr:
        logger.info(f"Cache miss for {user.username},querying DB")
        row = db.fetch_one("SELECT username,userpassword FROM users WHERE username = %s",(user.username,))
        if not row:
            logger.warning(f"Login blocked:{user.username} not found in DB")
            redis.hset(f"user:{user.username}",mapping={"__NULL__":"1"})
            redis.expire(f"user:{user.username}",15+random.randint(0,20))
            raise HTTPException(status_code=404,detail="User not found")
        redis.hset(f"user:{user.username}",mapping={
            "username":user.username,
            "password":row["userpassword"]
        })
        redis.expire(f"user:{user.username}",300+random.randint(0,120))
        usr = redis.hgetall(f"user:{user.username}")
        logger.info(f"Login success:{user.username} (DB->cache)")
        return {"username":usr.get("username")}