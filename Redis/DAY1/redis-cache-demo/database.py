from redis import ConnectionPool,Redis
from config import REDIS_CONFIG


# Create a Redis connection pool
pool = ConnectionPool(
    host=REDIS_CONFIG["host"],
    port=REDIS_CONFIG["port"],
    db=REDIS_CONFIG["db"],
    max_connections=REDIS_CONFIG["max_connections"],
    decode_responses=REDIS_CONFIG["decode_responses"]
)

def get_redis():
    return Redis(connection_pool=pool)