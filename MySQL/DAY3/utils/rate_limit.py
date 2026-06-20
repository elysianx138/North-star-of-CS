from database import get_redis
from fastapi import Request,HTTPException

def rate_limit_login(request: Request,key:str="rate:login",window:int=60,max_count:int=5,detail="Too many requests"):
    client_ip = request.client.host
    redis = get_redis()
    # Get the count of login attempts
    count = redis.incr(f"{key}:{client_ip}")
    if count == 1:
        redis.expire(f"{key}:{client_ip}", window)

    if count>max_count:
        raise HTTPException(status_code=429,detail=f"{detail}")

def rate_limit_user(user_id,key:str="rate:user",window:int=60,max_count:int=5,detail="Too many requests"):
    redis = get_redis()
    count = redis.incr(f"{key}:{user_id}")
    if count == 1:
        redis.expire(f"{key}:{user_id}",window)
    if count>max_count:
        raise HTTPException(status_code=429,detail=f"{detail}")