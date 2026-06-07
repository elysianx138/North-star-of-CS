# This's a demo that connects to MySQL database,testing the connection!
# If you don't have MySQL installed on your computer, you can use Docker to run a MySQL container.
# Then you can use this script to connect to the database.
import pymysql
from dbutils.pooled_db import PooledDB

pool = PooledDB(
    creator=pymysql,
    host="localhost",
    port=3306,
    user="root",
    password="root123",
    database="blog",
    maxconnections=5,
    mincached=2
)

conn = pool.connection()

with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM articles WHERE id = %s", (1,))
    row = cursor.fetchone()
    print(row)

conn.close()