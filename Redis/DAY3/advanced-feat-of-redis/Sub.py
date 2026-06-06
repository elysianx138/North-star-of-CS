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

def subscribe_channel():
    redis = get_redis()
    pubsub = redis.pubsub()
    # subscribe channel(event:test)
    pubsub.subscribe("event:test")

    print("Waiting for messages...")
    for message in pubsub.listen():
        # Recive message!
        print(message)
        if message["type"] == "message":
            print(message["data"])

def publish_channel():
    redis = get_redis()
    redis.publish("event:test","Hello,World!")

if __name__ == "__main__":
    
    subscribe_channel()


