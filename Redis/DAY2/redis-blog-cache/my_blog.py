from fastapi import FastAPI,HTTPException
from database import get_redis
from pydantic import BaseModel
import random,time
app = FastAPI()

fake_db = {
    "1":"That's too crazy! Redis is an in-memory data structure store, used as a database, cache and message broker.",
    "2":"Do you know that Redis is a great caching solution?"
}

# === First:Article content caching ===
# === Learn String cache ===
# === Function: Detailed article content ===
@app.get("/articles/{article_id}")
def get_article_content(article_id:str,retry:int=3):
    redis = get_redis()
    cache_key = f"article:{article_id}"
    lock_key = f"lock:article:{article_id}"

    data = redis.get(cache_key)
    # Try to get data from cache first. If data is None, then fetch from "fake_db" and cache it.
    if data is not None:
        if data == "__NULL__":
            return {"data":None, "source":"cache"}
        return {"data":data, "source":"cache"}

    # cache miss. fetch from "fake_db"
    locked = redis.set(lock_key, "1", nx=True, ex=10)
    if locked:
        try:
            article = fake_db.get(article_id)
            if article:
                redis.setex(cache_key, 300 + random.randint(0, 120), article)
                return {"data":article, "source":"database"}
            else:
                redis.setex(cache_key, 120 + random.randint(0, 60), "__NULL__")
                return {"data":None, "source":"not_found"}
        finally:
            redis.delete(lock_key)
    else:
        if retry <= 0:
            return {"data":None, "source":"Timeout"}
        time.sleep(1)
        return get_article_content(article_id, retry - 1)

# === Function: Check the number of articles liked ===
@app.get("/articles/{article_id}/likes")
def get_article_likes(article_id:str):
    redis = get_redis()
    count = redis.get(f"article:{article_id}:likes")
    return {"likes":int(count) if count else 0}

# === Function: Post likes ===
@app.post("/articles/{article_id}/likes")
def post_article_likes(article_id:str):
    redis = get_redis()
    count = redis.incr(f"article:{article_id}:likes")
    return {"likes":int(count)}
# === First end ===


# === Second: User profile caching ===
# === Learn Hash cache ===
# === Function:User sign up and cache user data ===
User_db = {}
class User(BaseModel):
    username:str
    email:str
    password:str

@app.post("/signup")
def sign_up(user:User):
    redis = get_redis()
    if user.username in User_db:
        raise HTTPException(status_code=409,detail="Username already exists")

    # Store user data in "User_db" and cache it in Redis
    User_db[user.username] = {
        "username":user.username,
        "email":user.email,
        "password":user.password
    }

    # Cache user data in Redis
    redis.hset(f"user:{user.username}",mapping={
        "username":user.username,
        "email":user.email,
        "password":user.password
    })
    redis.expire(f"user:{user.username}",300+random.randint(0,120))

    return {"message":"User created successfully"}

@app.get("/users/{username}")
def get_user_profile(username:str,retry:int=3):
    redis = get_redis()
    cache_key = f"user:{username}"
    lock_key = f"lock:user:{username}"

    user_data = redis.hgetall(cache_key)

    # Try to get data from cache first.If data is None,then fetch from "User_db" and cache it!
    if user_data:
        if user_data.get("__NULL__"):
            return {"message":"User not found","source":"Not found"}
        return {"username":user_data.get("username"),"email":user_data.get("email"),"password":user_data.get("password")}
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)
        
        if locked:
            try:
                user = User_db.get(username)
                if user:
                    redis.hset(cache_key,mapping={
                        "username":user["username"],
                        "email":user["email"],
                        "password":user["password"]
                    })
                    redis.expire(cache_key,300+random.randint(0,120))
                    return {"username":user["username"],"email":user["email"],"password":user["password"],"source":"user_base"}
                else:
                    redis.hset(cache_key,mapping={
                        "__NULL__":"1"
                    })
                    redis.expire(cache_key,120+random.randint(0,60))
                    return {"message":"User not found","source":"Not found"}
            finally:
                redis.delete(lock_key)
        else:
            if retry<=0:
                return {"data":None,"source":"Timeout"}
            time.sleep(1)
            return get_user_profile(username,retry-1)
# === Second end ===

# === Third:Post issues and check the lastest issue
# === Learn list cache ===