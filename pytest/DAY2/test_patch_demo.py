def get_redis():
    import redis
    return redis.Redis(host="localhost", port=6379)

def get_user_name(user_id):
    """真函数：从 Redis 取用户名"""
    r = get_redis()
    return r.get(f"user:{user_id}")

from unittest.mock import Mock,patch
def test_get_user_name_with_patch():
    fake_redis = Mock()
    fake_redis.get.return_value = "alice"

    with patch("test_patch_demo.get_redis", return_value=fake_redis):
        result = get_user_name(100)

        assert result == "alice"
        