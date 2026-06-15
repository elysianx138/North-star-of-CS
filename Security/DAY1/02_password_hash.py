import hashlib
import bcrypt
import logging

logger = logging.getLogger(__name__)

logger.info("=== Plain text password: ===")
password = "123456"
print(password)

logger.info("SHA-256 hash:")
sha = hashlib.sha256(password.encode()).hexdigest()
print(f"SHA-256: {sha}")
print(f"SHA-256 length: {len(sha)}")

logger.info("bcrypt hash:salt + hash")
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode(), salt)
print(f"bcrypt: {hashed.decode()}")
print(f"bcrypt length: {len(hashed)}")

print(f"bcrypt 验证正确密码: {bcrypt.checkpw(password.encode(), hashed)}")
print(f"bcrypt 验证错误密码: {bcrypt.checkpw('wrong'.encode(), hashed)}")
