import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST","localhost"),
    port=os.getenv("MYSQL_PORT",3306),
    user=os.getenv("MYSQL_USER","root"),
    password=os.getenv("MYSQL_PASSWORD","root123"),
    database="practice_db",
    autocommit=False,
     cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS accounts")
    cursor.execute("""CREATE TABLE accounts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        balance DECIMAL(10,2)
    )""")
    cursor.executemany("INSERT INTO accounts (name, balance) VALUES (%s, %s)", [("Alice", 1000),("Bob",500)])
conn.commit()


# Alice → Bob 100
with conn.cursor() as cur:
    cur.execute("UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice'")
    cur.execute("UPDATE accounts SET balance = balance + 100 WHERE name = 'Bob'")
conn.commit()

conn.rollback()

# ===== 实操 1.2：回滚演示 =====
print("实操 1.2：回滚演示")
print("------------------")
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM accounts")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  转账前: {row['name']} → {row['balance']}")

    # Alice 扣钱，但不提交
    cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE name = 'Alice'")
    print("  Alice 扣了 100（未提交）")

    # 回滚
    conn.rollback()
    print("  执行 ROLLBACK")

    # 再查
    cursor.execute("SELECT * FROM accounts")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  回滚后: {row['name']} → {row['balance']}")

