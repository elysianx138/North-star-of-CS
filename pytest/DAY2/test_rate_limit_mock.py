from unittest.mock import Mock,patch

def rate_limit_login(mock_redis,client_ip,max_count=5):
    count =  mock_redis.incr(f"rate:login:{client_ip}")
    if count == 1:
        mock_redis.expire(f"rate:login:{client_ip}",60)
    if count > max_count:
        return 429
    return 200

def test_rate_limit_under_threehold():
    mock_redis = Mock()
    mock_redis.incr.side_effect = [1,2,3]
    result = None
    for i in range(3):
        result = rate_limit_login(mock_redis,"127.0.0.1")
    assert result == 200

def test_rate_limit_exceeded():
    mock_redis = Mock()
    mock_redis.incr.side_effect = [1,2,3,4,5,6]
    result = None
    for i in range(6):
        result = rate_limit_login(mock_redis,"127.0.0.1")
    assert result == 429