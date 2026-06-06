from redis import Redis,ConnectionPool
import time
pool = ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=10,
    decode_responses=True
)

def get_redis():
    return Redis(connection_pool=pool)

def have_pipeline():
    redis = get_redis()
    redis.flushdb()
    pipe = redis.pipeline()
    start = time.time()
    for i in range(10):
        pipe.set(f"key::{i}",i)

    pipe.execute()
    total_time = time.time() - start
    print("Have finished")
    print(f"Have pipeline's time: {total_time}")

def none_pipeline():
    redis = get_redis()
    redis.flushdb()
    start = time.time()
    for i in range(10):
        redis.set(f"key::{i}",i)

    total_time = time.time() - start
    print("Have finished")
    print(f"None pipeline's time: {total_time}")


if __name__ == "__main__":
    have_pipeline()
    none_pipeline()