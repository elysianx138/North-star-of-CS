from redis import Redis,ConnectionPool

pool = ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=10,
    decode_responses=True
)

def get_redis():
    return Redis(connection_pool=pool)

lua_script = """
local exist = redis.call("EXISTS",KEYS[1])
if exist == 0 then
    return "Article not found"
end

local likes = redis.call("INCR",KEYS[2])

redis.call("ZINCRBY",KEYS[3],1,KEYS[4])

return likes


"""

def atomic_like():
    redis = get_redis()
    redis.set("article:1","Redis Lua Demo")
    result = redis.eval(lua_script,4,
        "article:1",
        "article:1:likes",
        "hot:articles",
        "article:1"
    )

    print(f"Result:{result}")


# Register a lua script
redis = get_redis()
atomic_likes = redis.register_script("""
local exists = redis.call("EXISTS",KEYS[1])
if exists == 0 then
    return "Article not found"
end
                                    
local likes = redis.call("INCR",KEYS[2])
redis.call("ZINCRBY",KEYS[3],1,ARGV[1])

return likes                                                                                        
""")

def ato_like():
    result = atomic_likes(keys=["article:1","article:1:likes","hot:articles"],args=["1"])
    print(result)
if __name__ == "__main__":
    atomic_like()
    ato_like()
