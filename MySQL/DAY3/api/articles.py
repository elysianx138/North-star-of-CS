from database import get_redis
from fastapi import APIRouter,HTTPException
from db import db
from pydantic import BaseModel
from utils.retry_and_sleep import retry_and_sleep
import random

router = APIRouter()

class Article(BaseModel):
    title:str
    content:str


# Post new article!
@router.post("/articles")
def post_articles(article:Article):
    redis = get_redis()
    article_id = db.insert("INSERT INTO articles (title,content,author_id) VALUES (%s,%s,%s)", (article.title,article.content,1))
    redis.hset(f"article:{article_id}",mapping={
        "title":article.title,
        "content":article.content
    })
    redis.expire(f"article:{article_id}",300+random.randint(0,120))
    return {"message":"Successfully created article","article_id":article_id}

# Get details of an article
@router.get("/articles/{article_id}")
def get_articles(article_id:int,retry:int=3):
    redis = get_redis()
    lock_key = f"lock:article:{article_id}"
    cache_key = f"article:{article_id}"

    # Check cache
    data = redis.hgetall(cache_key)
    if data:
        if "__NULL__" in data:
            raise HTTPException(status_code=404,detail="Article not found")
        return {"title":data.get("title"), "content":data.get("content")}
    
    # If cache is not hit, fetch from database
    else:
        try:
            locked = redis.set(lock_key,"1",nx=True,ex=10)
            if locked:
                article = db.fetch_one("SELECT title,content FROM articles WHERE id = %s", (article_id,))
                if article:
                    redis.hset(cache_key,mapping={
                        "title":article["title"],
                        "content":article["content"]
                    })
                    redis.expire(cache_key,300+random.randint(0,120))
                    return {"title":article["title"], "content":article["content"]}
                else:
                    redis.hset(cache_key,mapping={
                        "__NULL__":"1"
                    })
                    redis.expire(cache_key,120+random.randint(0,60))
                    raise HTTPException(status_code=404,detail="Article not found")
            else:
                raise HTTPException(status_code=429,detail="Too many requests")

        finally:
            redis.delete(lock_key)

