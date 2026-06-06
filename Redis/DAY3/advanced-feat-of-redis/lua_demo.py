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

# Write a Lua scipt
redis = get_redis()
lua_script = """
local count = redis.call("GET",KEYS[1])
if not count then 
    return "not_found"
end
return count
"""

def demo_lua():
    redis = get_redis()
    redis.set("mykey","value")
    count = redis.eval(lua_script,1,"mykey")
    print(f"Lua result:{count}")

if __name__ == "__main__":
    demo_lua()
