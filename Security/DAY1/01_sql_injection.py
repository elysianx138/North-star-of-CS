import pymysql
import os
import logging

logger = logging.getLogger(__name__)

conn = pymysql.connect(
    host = os.getenv("MYSQL_HOST","localhost"),
    port = os.getenv("MYSQL_PORT",3306),
    user = os.getenv("MYSQL_USER","root"),
    password = os.getenv("MYSQL_PASSWORD","root123"),
    database = "security_practice",
    cursorclass=pymysql.cursors.DictCursor
)

def unsafe_login(username,password):
    logger.warning("⚠This's unsafe login function:String compose")
    sql = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    logger.info(f"[SQL] {sql}")
    with conn.cursor() as cursor:
        cursor.execute(sql)
        user = cursor.fetchone()
        if user:
            logger.info("Login successfully!")
            print(f"login successfully!Welcome {user['username']}")

        else:
            logger.error("Have failed!")
            print("username or password is wrong!")

print("Login now!")
unsafe_login("admin","supersecret")

# === Injection ===
print("SQL injection")
unsafe_login("admin' -- ","12344")

print("DROP TABLE")
unsafe_login("' ; DROP TABLE users; -- ","")
