from redis import Redis,ConnectionPool
from redis.exceptions import ResponseError
import time

pool = ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=20,
    decode_responses=True
)
def get_redis():
    return Redis(connection_pool=pool)

# === Step1:Basic TTL ===
def basic_ttl():
    redis = get_redis()
    redis.set("mykey","value",ex=5)

    for i in range(8):
        val = redis.get("mykey")
        ttl = redis.ttl("mykey")
        print(f"{i}s -> value:{val},TTL:{ttl}")
        time.sleep(1)

# === Step2: Lazy Delete ===
def lazy_delete():
    redis = get_redis()
    redis.set("lazy_delete","value",ex=3)
    time.sleep(4)
    # sleep 4s until TTL expires
    # Maybe output:0 or 1
    print("Before GET:")
    print(redis.exists("lazy_delete"))
    redis.get("lazy_delete")
    print("After GET:")
    print(redis.exists("lazy_delete"))

# === Step3: Memory Delete ===
def memory_delete():
    redis = get_redis()
    print(f"Before FlushDB:{redis.dbsize()}")
    info = redis.info("server")
    print(f"Redis ID: {info['process_id']}")
    print(f"Redis Version: {info['redis_version']}")
    print(f"Redis dbs: {redis.dbsize()}")

    redis.flushdb()


    # === Check Config ===
    print(f"Eviction Policy:")
    print(redis.config_get("maxmemory-policy"))
    print(f"Max Memory:")
    print(redis.config_get("maxmemory"))

    # ====================
    old_policy = redis.config_get("maxmemory-policy")["maxmemory-policy"]
    old_maxmem = redis.config_get("maxmemory")["maxmemory"]

    redis.config_set("maxmemory",1024*1024*2) # 2MB
    redis.config_set("maxmemory-policy","noeviction")
    print(f"Eviction Policy:")
    print(redis.config_get("maxmemory-policy"))
    print(f"Max Memory:")
    print(redis.config_get("maxmemory"))

    # === Write Key Crazily ===
    count = 0
    try:
        while True:
            redis.set(f"key{count}","value")
            count += 1
            print(f"Wrote key{count}")

    except ResponseError as e:
        print(f"Full! Can't write!{count} keys:{e}")

    for i in range(count):
        redis.delete(f"key{count}")
    
    # # === Recovery ===
    redis.config_set("maxmemory-policy",old_policy)
    redis.config_set("maxmemory",old_maxmem)

if __name__ == "__main__":
    # basic_ttl()
    # Output:
    # 0s -> value:value,TTL:5
    # 1s -> value:value,TTL:4
    # ...
    # 5s -> value:value,TTL:-2  --> TTL expired,meaning the key doesn't exist
    # if TTL = -1,mean the key never expire

    print("\n === Lazy Delete Demo ===")
    # lazy_delete()
    # Output:
    # Before GET:
    # 0 or 1
    # After GET:
    # 0

    print("\n === Memory Delete Demo ===")
    memory_delete()