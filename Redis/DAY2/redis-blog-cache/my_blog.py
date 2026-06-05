from fastapi import FastAPI,HTTPException
from database import get_redis
from pydantic import BaseModel
import random,time
app = FastAPI()

fake_db = {
    "1": {
        "content":"That's too crazy! Redis is an in-memory data structure store, used as a database, cache and message broker.",
        "tags":[]
    },
    "2": {
        "content":"Do you know that Redis is a great caching solution?",
        "tags":[]
    }
}

# === First:Article content caching ===
# === Learn String cache ===
# === Function: Detailed article content ===
@app.get("/articles/{article_id}")
def get_article_content(article_id:int,retry:int=3):
    redis = get_redis()
    article_id = str(article_id)
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
            article_data = fake_db.get(article_id)
            if article_data:
                redis.setex(cache_key, 300 + random.randint(0, 120), article_data["content"])
                return {"data":article_data["content"], "source":"database"}
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
# === Function:Post issues and check the lastest issue ===
class Article(BaseModel):
    content:str

@app.post("/articles")
def post_articles(article:Article):
    redis = get_redis()
    new_id = str(len(fake_db) + 1)
    fake_db[new_id] = {
        "content": article.content,
        "tags": []
    }

    redis.lpush("articles:latest",new_id)
    redis.ltrim("articles:latest",0,9)
    redis.expire("articles:latest",300+random.randint(0,120))
    
    return {"article_id":new_id}
# === Function: Get the lastest issue and cache it ====
@app.get("/articles/latest")
def get_latest_articles(retry:int=3):
    redis = get_redis()
    cache_key = "articles:latest"
    lock_key = "lock:articles:latest"

    latest = redis.lindex(cache_key,0)
    if latest is not None:
        if latest == "__NULL__":
            return {"article_id":None,"source":"cache"}
        return {"article_id":latest,"source":"cache"}
    
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)

        if locked:
            try:
                # === Check the database ===
                if fake_db:
                    # fetch the lastest id form "fake_db"
                    latest_id = sorted(fake_db.keys(),key=int,reverse=True)[0]

                    # cache the lastest id
                    redis.lpush(cache_key,latest_id)
                    redis.ltrim(cache_key,0,9)
                    redis.expire(cache_key,300+random.randint(0,120))
                    return {"article_id":latest_id,"source":"database"}
                else:
                    # === If the database is empty, cache null value to reduce redundant queries ===
                    redis.lpush(cache_key,"__NULL__")
                    redis.ltrim(cache_key,0,9)
                    redis.expire(cache_key,120+random.randint(0,60))
                    return {"article_id":None,"source":"not_found"}
            finally:
                redis.delete(lock_key)

        else:
            if retry<=0:
                return {"article_id":None,"source":"Timeout"}
            time.sleep(1)
            return get_latest_articles(retry-1)

# === Third end ===

# === Fourth:Filter articles by tag
# === Learn set cache ===
# === Function:post articles' tags ===
class Tagsbody(BaseModel):
    tags:list[str]

@app.post("/articles/{article_id}/tags")
def post_article_tags(body:Tagsbody, article_id:str):
    redis = get_redis()
    tags = body.tags

    # Add tags for articles
    redis.sadd(f"articles:{article_id}:tags", *tags)
    redis.expire(f"articles:{article_id}:tags", 300 + random.randint(0, 120))
    article_data = fake_db.get(article_id)
    if article_data:
        for tag in tags:
            if tag not in article_data["tags"]:
                article_data["tags"].append(tag)

    # Check tags from articles_id
    for tag in tags:
        redis.sadd(f"tags:{tag}",article_id)
        # I think this is not necessary
        # When the cache of tags expires, the time consumed for reverse reconstruction is too long. Therefore, I think it is necessary for the tag cache to be resident.
        # But you also can write this code
        # redis.expire(f"tags:{tag}",300+random.randint(0,120))

    return {"message":f"Message {article_id} has been tagged with {tags}"}

# === Function:get articles' tags ===
@app.get("/articles/{article_id}/tags")
def get_article_tags(article_id:str,retry:int=3):
    redis = get_redis()
    lock_key = f"lock:articles:{article_id}:tags"
    tags = redis.smembers(f"articles:{article_id}:tags")

    if tags:
        if "__NULL__" in tags:
            return {"tags":None,"source":"cache"}
        return {"tags":list(tags),"source":"cache"}
    else:
        locked = redis.set(lock_key,"1",nx=True,ex=10)

        if locked:
            try:
                article_data = fake_db.get(article_id)
                if article_data:
                    tags = article_data["tags"]
                    redis.sadd(f"articles:{article_id}:tags", *tags)
                    redis.expire(f"articles:{article_id}:tags", 300 + random.randint(0, 120))
                    return {"tags":list(tags),"source":"database"}
                else:
                    redis.sadd(f"articles:{article_id}:tags","__NULL__")
                    redis.expire(f"articles:{article_id}:tags", 120 + random.randint(0, 60))
                    return {"tags":None,"source":"not_found"}

            finally:
                redis.delete(lock_key)

        else:
            if retry<=0:
                return {"tags":None,"source":"Timeout"}
            time.sleep(1)
            return get_article_tags(article_id,retry-1)


# === Function:get what tags are related to the article ===
@app.get("/articles")
def get_articles_by_tags(tags:str = None):
    redis = get_redis()

    if not tags:
        return {"articles":list(fake_db.keys()),"source":"all"}

    tag_list = tags.split(",")
    cache_keys = [f"tags:{tag}" for tag in tag_list]

    article_ids = redis.sinter(cache_keys)
    if article_ids:
        return {"articles":list(article_ids),"source":"cache"}

    # fallback: traverse fake_db
    result = []
    for aid,data in fake_db.items():
        if all(tag in data["tags"] for tag in tag_list):
            result.append(aid)

    return {"articles":result,"source":"database"}
                




