from fastapi import FastAPI
from database import get_redis
import time,random
app = FastAPI()

# === mock data ===
fake_db = {
    "1":"First article:Redis is a powerful in-memory data structure store, used as a database, cache, and message broker.",
    "2":"Second article:Redis supports various data structures such as strings, hashes, lists, sets, and sorted sets.",
}

# === Cache penetration ===
@app.get("/articles/{article_id}")
def get_article(article_id:str):
    redis = get_redis()
    cache_key = f"article:{article_id}"

    # Check cache
    data = redis.get(cache_key)
    if data is not None:
        if data == "__NULL__":
            return {"data":None,"source":"cache"}
        return {"data":data,"source":"cache"}
    
    # Cache miss,fetch from "database"
    article = fake_db.get(article_id)
    if article:
        redis.setex(cache_key,3600+random.randint(0,60),article)
        return {"data":article,"source":"database"}
    else:
        # data not found,cache null value to prevent cache penetration 
        redis.setex(cache_key,60+random.randint(0,60),"__NULL__")
        return {"data":None,"source":"not_found"}
# ===========================

# === Cache breakdown ===
@app.get("/hot/{key}")
def get_hot_data(key:str,retry:int=3):
    redis = get_redis()
    cache_key = f"hot:{key}"
    lock_key = f"lock:hot:{key}"
    # 1.Check cache
    data = redis.get(cache_key)
    if data:
        return {"data":data,"source":"cache"}

    # 2.Try to acquire lock
    locked = redis.set(lock_key,"1",nx=True,ex=10)

    if locked:

        time.sleep(2) # Simulate data fetching delay

        if key == "1":
            result = "🔥This is a hot article!"
        else:
            result = f"hot data {key}"
        
        # Rebuild cache
        redis.setex(cache_key,300,result)
        # Release lock
        redis.delete(lock_key)
        return {"data":result,"source":"database"}

    else:
        if retry <= 0:
            return {"data":None,"source":"database_timeout"}
        # Failed to acquire lock,wait and retry
        time.sleep(0.1)

        return get_hot_data(key, retry-1)



