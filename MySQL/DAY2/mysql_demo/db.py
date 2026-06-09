import pymysql
from pymysql import err as pymysql_err
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager


class DB:
    # Connection Pool
    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,
            host="localhost",
            port=3306,
            user="root",
            password="root123",
            database="blog",
            maxconnections=5,
            mincached=2,
            charset="utf8mb4"
        )

    @contextmanager
    def conn_cursor(self):
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def fetch_one(self, sql, params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()

    def fetch_all(self, sql, params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

    def insert(self, sql, params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.lastrowid

    def update(self, sql, params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.rowcount

    def delete(self, sql, params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.rowcount
        
    def insert_many(self,sql,params_list):
        with self.conn_cursor() as cursor:
            cursor.executemany(sql,params_list)
            return cursor.rowcount

# Create DB instance
db = DB()
