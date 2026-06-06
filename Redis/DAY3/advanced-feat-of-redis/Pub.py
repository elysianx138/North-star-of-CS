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

def publish_channel():
    
    redis = get_redis()
    redis.publish("event:test","Hello,World!")

if __name__ == "__main__":
    publish_channel()
    