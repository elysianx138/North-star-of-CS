# DAY2: Python + MySQL 实战 / Python + MySQL in Action

> **适合人群 / For You:**
> 已掌握 SQL 基础，想用 Python 操作 MySQL。
>
> **学习方式 / Learning Approach:**
> 从裸写 SQL → 连接池封装 → CRUD 工具类。**中英双语 / Bilingual**
>
> **目标 / Goal:**
> 写出可直接用于 FastAPI 项目的 `db.py` 工具模块。

---

## 📋 目录 / Contents

1. [环境准备 / Setup](#-一环境准备--setup)
2. [PyMySQL 连接 / Basic Connection](#-二pymysql-连接--basic-connection)
3. [连接池 / Connection Pool](#-三连接池--connection-pool)
4. [上下文管理器 / Context Manager](#-四上下文管理器--context-manager)
5. [DB 工具类 / DB Utility Class](#-五db-工具类--db-utility-class)
6. [CRUD 方法 / CRUD Methods](#-六crud-方法--crud-methods)
7. [异常处理 / Exception Handling](#-七异常处理--exception-handling)
8. [测试 / Testing](#-八测试--testing)

---

## 🔧 一、环境准备 / Setup

### 安装依赖 / Install Dependencies

```bash
pip install pymysql DBUtils
```

**EN:** If the MySQL container is not running, start it first.

**CN:** 如果 MySQL 容器没启动，先启动它。

```bash
docker start mysql-local
```

**EN:** Test that Python can connect to MySQL.

**CN:** 测试 Python 能否连上 MySQL。

```python
import pymysql
conn = pymysql.connect(host="localhost", port=3306, user="root", password="root123", database="blog")
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM articles")
    print(cursor.fetchall())
conn.close()
```

---

## 📡 二、PyMySQL 连接 / Basic Connection

### 参数化查询 / Parameterized Query

**EN:** Always use `%s` placeholders to prevent SQL injection. Never concatenate strings.

**CN:** **永远用 `%s` 占位符**，防止 SQL 注入。不要拼接字符串。

```python
# ✅ 安全 / Safe
cursor.execute("SELECT * FROM articles WHERE id = %s", (1,))

# ❌ 危险 / Dangerous
cursor.execute(f"SELECT * FROM articles WHERE id = {id}")
```

### fetchone vs fetchall

**EN:** `fetchone()` returns one row at a time (memory efficient for large data). `fetchall()` returns all rows at once (simple but may use lots of memory).

**CN:** `fetchone()` 一次拿一行，省内存，适合大数据。`fetchall()` 一次拿全部，简单但数据量大时占内存。

```python
# fetchone — 一行一行拿 / Row by row
cursor.execute("SELECT * FROM articles")
row = cursor.fetchone()    # 第一行 / First row
row = cursor.fetchone()    # 第二行 / Second row
row = cursor.fetchone()    # 第三行 / Third row
row = cursor.fetchone()    # None（没了 / No more）

# fetchall — 一次全拿 / All at once
cursor.execute("SELECT * FROM articles")
all_rows = cursor.fetchall()
print(f"共 {len(all_rows)} 行 / Total {len(all_rows)} rows")
```

**EN:** Use `fetchone` loop for large datasets (10k+ rows). Use `fetchall` for small results.

**CN:** 大数据用 `fetchone` 循环，小数据用 `fetchall` 省事。

---

## 🔌 三、连接池 / Connection Pool

### 为什么需要连接池？ / Why Connection Pool?

**EN:** Each database connection requires a TCP handshake + authentication. Creating a new connection for every request is slow. A connection pool pre-creates connections and reuses them.

**CN:** 每次数据库连接都要 TCP 握手 + 认证。每个请求都新建连接**太慢了**。连接池预创建一些连接，反复使用。

```python
from dbutils.pooled_db import PooledDB

pool = PooledDB(
    creator=pymysql,
    host="localhost", port=3306,
    user="root", password="root123",
    database="blog",
    maxconnections=5,   # 最多 5 个连接 / Max 5 connections
    mincached=2         # 预创建 2 个空闲 / Pre-create 2 idle
)

# 从池子里拿连接 / Get a connection from pool
conn = pool.connection()
conn.close()            # 用完还回去 / Return to pool
```

| 参数 / Param | 含义 / Meaning |
|:---|:---|
| `maxconnections` | 池子里最多几个连接 / Max connections in pool |
| `mincached` | 启动时预创建几个空闲连接 / Pre-created idle connections |

---

## 📦 四、上下文管理器 / Context Manager

### @contextmanager

**EN:** Turns a generator function (with `yield`) into a context manager, so it works with `with ... as`. Code before `yield` runs on enter, code after `yield` runs on exit.

**CN:** 让一个生成器函数（有 `yield`）支持 `with ... as` 语法。`yield` 前面是进入时执行，`yield` 后面是退出时执行。

```python
from contextlib import contextmanager

@contextmanager
def my_context():
    print("进入 / Enter")     # __enter__
    yield "hello"             # 暂停，返回给 as
    print("退出 / Exit")      # __exit__

with my_context() as x:
    print(f"拿到: {x}")

# 输出:
# 进入 / Enter
# 拿到: hello
# 退出 / Exit
```

### conn_cursor 生命周期 / Lifecycle

```
┌─ with db.conn_cursor() as cursor ────────────┐
│  ① conn = pool.connection()   ← 拿连接       │
│  ② yield cursor               ← 暂停，给你游标 │
│  ③ 你的 SQL 操作 / Your SQL                  │
│  ④ 退出 with → 继续 yield 后面               │
│     conn.commit() / conn.rollback()           │
│     conn.close()               ← 还连接       │
└───────────────────────────────────────────────┘
```

**EN:** The `yield` is the dividing line. Before it = entering `with`. After it = exiting `with`. This guarantees `conn.close()` always runs.

**CN:** `yield` 是分水岭。前面是进入 `with`，后面是退出 `with`。这保证 `conn.close()` **一定会被执行**。

---

## 🧰 五、DB 工具类 / DB Utility Class

**EN:** Wrap the connection pool and all operations into a class for reuse. Other files just `from db import db` and use it.

**CN:** 把连接池和所有操作封装成一个类。其他文件 `from db import db` 就能用。

```python
class DB:
    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql, host="localhost", port=3306,
            user="root", password="root123", database="blog",
            maxconnections=5, mincached=2, charset="utf8mb4"
        )

    @contextmanager
    def conn_cursor(self):
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

# 全局单例 / Global singleton — 其他文件直接 import
db = DB()
```

---

## ✍️ 六、CRUD 方法 / CRUD Methods

**EN:** Each method gets a connection from the pool, executes SQL, and returns the result.

**CN:** 每个方法从池子里拿连接，执行 SQL，返回结果。

```python
# 查一行 / Fetch one row
def fetch_one(self, sql, params=None):
    with self.conn_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()

# 查全部 / Fetch all rows
def fetch_all(self, sql, params=None):
    with self.conn_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()

# 插入 / Insert
def insert(self, sql, params=None):
    with self.conn_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.lastrowid   # 返回新数据的 id / Return new row id

# 更新 / Update
def update(self, sql, params=None):
    with self.conn_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.rowcount    # 返回影响行数 / Rows affected

# 删除 / Delete
def delete(self, sql, params=None):
    with self.conn_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.rowcount    # 返回影响行数 / Rows affected
```

### 返回值说明 / Return Values

| 方法 / Method | 返回 / Returns | 用途 / Purpose |
|:---|:---|:---|
| `fetch_one` | 一行 `(tuple)` 或 `None` | 查单条 / Single row query |
| `fetch_all` | 多行 `(tuple of tuples)` | 查全部 / All rows |
| `insert` | 自增 id `(int)` | 获取新数据 id / Get new row id |
| `update` | 影响行数 `(int)` | 判断是否更新成功 / Check if update succeeded |
| `delete` | 影响行数 `(int)` | 判断是否删除成功 / Check if delete succeeded |

---

## ⚠️ 七、异常处理 / Exception Handling

**EN:** The `conn_cursor` method catches exceptions to rollback and close the connection. If an error occurs, your data stays safe and the connection is returned to the pool.

**CN:** `conn_cursor` 捕获异常是为了回滚 + 关连接。出错了数据不会损坏，连接也会还回池子。

```python
@contextmanager
def conn_cursor(self):
    conn = self.pool.connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()          # 没报错 → 提交 / No error → commit
    except Exception as e:
        conn.rollback()        # 报错 → 回滚 / Error → rollback
        raise
    finally:
        conn.close()           # 不管怎样 → 关连接 / Always close
```

**EN:** The exception is re-raised (`raise`) so the caller knows something went wrong. Use try/except when calling db methods to handle errors gracefully.

**CN:** 异常会重新抛出（`raise`），调用者可以用 `try/except` 处理。

---

## 🧪 八、测试 / Testing

**EN:** Run a full CRUD test.

**CN:** 跑一遍完整的 CRUD 测试。

```python
from db import db

# 查 / Read
rows = db.fetch_all("SELECT * FROM articles")
print("所有文章 / All articles:", rows)

# 查单条 / Read one
row = db.fetch_one("SELECT * FROM articles WHERE id = %s", (1,))
print("id=1:", row)

# 插入 / Create
new_id = db.insert(
    "INSERT INTO articles (title, content, author_id) VALUES (%s, %s, %s)",
    ("New Article", "Content here", 1)
)
print(f"新文章 id / New article id = {new_id}")

# 更新 / Update
affected = db.update(
    "UPDATE articles SET title = %s WHERE id = %s",
    ("Updated Title", new_id)
)
print(f"更新了 / Updated {affected} row(s)")

# 删除 / Delete
deleted = db.delete("DELETE FROM articles WHERE id = %s", (new_id,))
print(f"删除了 / Deleted {deleted} row(s)")
```

---

## 📝 总结 / Summary

| 知识点 / Topic | 掌握程度 / Level |
|:---|:---:|
| PyMySQL 连接 / Connection | ✅ 理解 / Understand |
| 参数化查询 / Parameterized Query | ✅ 熟练 / Proficient |
| 连接池 / Connection Pool | ✅ 理解 / Understand |
| @contextmanager | ✅ 基本理解 / Basic Understanding |
| DB 类封装 / DB Class | ✅ 理解 / Understand |
| CRUD 方法 / CRUD Methods | ✅ 熟练 / Proficient |
| 异常处理 / Exception Handling | ✅ 理解 / Understand |

> **下一步 / Next Up:** DAY3 — FastAPI + MySQL，替换 fake_db / Replace fake_db with real MySQL
