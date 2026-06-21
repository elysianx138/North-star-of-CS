from unittest.mock import Mock
mock_redis = Mock()

mock_redis.get.return_value = "alice"

result = mock_redis.get("user:123")
print(result)

assert result == "alice"
mock_redis.get.assert_called_once_with("user:123")