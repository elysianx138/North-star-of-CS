# redis = get_redis()
# count = redis.incr(key)
# redis.expire(key,window)
from unittest.mock import Mock,patch

print("=== return value demo ===")
mock_redis = Mock()
mock_redis.incr.return_value = 1

print(mock_redis.incr("key"))
print(mock_redis.incr("key"))
print(mock_redis.incr("keys"))


print("=== side_effect demo ===")
mock_redis = Mock()
mock_redis.incr.side_effect = [1,2,3]

print(mock_redis.incr("key"))
print(mock_redis.incr("key"))
print(mock_redis.incr("keys"))

print("=== assert_called_once_with demo ===")
mock_redis = Mock()
mock_redis.set("user:100","alice")

mock_redis.set.assert_called_once_with("user:100","alice")

print("=== rate_limit_login ===")
mock_redis = Mock()
mock_redis.incr.side_effect = [1,2,3,4,5,6]
with patch("test_mock_three.Mock") as fake:
    pass

for i in range(6):
    count = mock_redis.incr("rate:login:127.0.0.1")

assert count == 6
print(f"count: {count}")
