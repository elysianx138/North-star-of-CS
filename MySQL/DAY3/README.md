# DAY3: FastAPI + MySQL + Redis 实战 / Full-Stack Blog API

> **适合人群 / For You:**
> 已掌握 Python + MySQL 基础，想构建带缓存的真实 API。
>
> **学习方式 / Learning Approach:**
> 从项目结构 → 用户认证 → 文章 CRUD → 点赞热度 → 标签搜索。**中英双语 / Bilingual**
>
> **目标 / Goal:**
> 用 FastAPI + MySQL (连接池) + Redis (缓存/排行榜/锁) 构建一个完整的博客 API。

---

## 📋 目录 / Contents

1. [项目结构 / Project Structure](#-一项目结构--project-structure)
2. [环境配置 / Configuration](#-二环境配置--configuration)
3. [数据库连接 / Database Connections](#-三数据库连接--database-connections)
4. [用户模块 / Users API](#-四用户模块--users-api)
5. [文章模块 / Articles API](#-五文章模块--articles-api)
6. [点赞和热度 / Likes & Hot Ranking](#-六点赞和热度--likes--hot-ranking)
7. [标签系统 / Tags API](#-七标签系统--tags-api)
8. [缓存策略总结 / Caching Strategy](#-八缓存策略总结--caching-strategy)
9. [测试 / Testing](#-九测试--testing)

---

## 📁 一、项目结构 / Project Structure

```
MySQL/DAY3/
├── app.py              # FastAPI 入口 / App entry
├── config.py           # 配置 / Config (MySQL, Redis)
├── database.py         # Redis 连接池 / Redis connection pool
├── db.py               # MySQL 连接池 + CRUD 工具 / MySQL pool + CRUD
├── init.sql            # 建表语句 / Table schemas
├── requirements.txt    # 依赖 / Dependencies
└── api/
    ├── __init__.py
    ├── users.py        # 用户注册登录 / User register & login
    ├── articles.py     # 文章 CRUD + 标签 / Article CRUD + tags
    ├── likes.py        # 点赞 + 热度排行 / Likes + hot ranking
    └── tags.py         # 按标签搜索 / Search by tag
```

**EN:** Each API module has its own router, registered in `app.py`. `db.py` and `database.py` are shared utilities.

**CN:** 每个 API 模块有独立的路由，在 `app.py` 中统一注册。`db.py` 和 `database.py` 是全局共享的工具模块。

---

## ⚙️ 二、环境配置 / Configuration

### 依赖安装 / Install Dependencies

```bash
pip install fastapi uvicorn pymysql DBUtils redis python-dotenv
```

### 环境变量 / Environment Variables (`.env`)

```env
MYSQL_USER=root
MYSQL_PASSWORD=root123
MYSQL_DATABASE=blog
```

### 启动服务 / Start the Server

```bash
uvicorn app:app --reload
```

**EN:** Ensure MySQL and Redis are running before starting. Visit `http://127.0.0.1:8000/docs` for Swagger UI.

**CN:** 启动前确保 MySQL 和 Redis 在运行。访问 `http://127.0.0.1:8000/docs` 查看 Swagger 文档。

---

## 🔌 三、数据库连接 / Database Connections

### MySQL 连接池 / MySQL Connection Pool

**EN:** Reuses `db.py` from DAY2 — a `PooledDB` wrapper with auto-commit, rollback, and connection return.

**CN:** 复用 DAY2 的 `db.py` — 使用 `PooledDB` 连接池，自动提交/回滚/归还连接。

```python
from db import db

# 查单条 / Fetch one
user = db.fetch_one("SELECT * FROM users WHERE id = %s", (1,))

# 查全部 / Fetch all
articles = db.fetch_all("SELECT * FROM articles")

# 插入 / Insert
uid = db.insert("INSERT INTO users (username, userpassword) VALUES (%s, %s)", ("alice", "pwd123"))

# 批量插入 / Batch insert
db.insert_many("INSERT INTO article_tags (article_id, tag) VALUES (%s, %s)",
               [(1, "python"), (1, "redis")])
```

### Redis 连接池 / Redis Connection Pool

**EN:** A global `ConnectionPool` so every API call reuses connections instead of creating new ones.

**CN:** 全局 `ConnectionPool`，所有 API 调用复用连接，不重复创建。

```python
from redis import Redis, ConnectionPool

pool = ConnectionPool(
    host="localhost", port=6379, db=0,
    max_connections=10, decode_responses=True
)

def get_redis():
    return Redis(connection_pool=pool)
```

| 参数 / Param | 含义 / Meaning |
|:---|:---|
| `max_connections` | 池子里最多几个连接 / Max connections |
| `decode_responses` | 自动把 bytes 转 str / Auto decode bytes to str |

---

## 👤 四、用户模块 / Users API

### 注册 / Register (`POST /logup`)

**EN:** Hash the password with SHA-256, insert into MySQL, cache the user data in Redis.

**CN:** SHA-256 加密密码，写入 MySQL，同时缓存到 Redis。

```python
@router.post("/logup")
def logup(username: str, email: str, userpassword: str):
    hashed_pwd = hashlib.sha256(userpassword.encode()).hexdigest()
    uid = db.insert(
        "INSERT INTO users (username, email, userpassword) VALUES (%s, %s, %s)",
        (username, email, hashed_pwd)
    )
    redis.hset(f"user:{uid}", mapping={
        "username": username,
        "email": email,
        "userpassword": hashed_pwd
    })
    redis.expire(f"user:{uid}", 3600)
    return {"message": "Successfully registered", "user_id": uid}
```

### 登录 / Login (`POST /login`)

**EN:** Check cache first (Redis Hash), fallback to MySQL. Verify password hash. Null cache for non-existent users.

**CN:** 先查 Redis 缓存，未命中则回源 MySQL。校验密码哈希。不存在则缓存空值防穿透。

```python
@router.post("/login")
def login(username: str, userpassword: str):
    hashed_pwd = hashlib.sha256(userpassword.encode()).hexdigest()
    redis_key = f"user_name:{username}"
    lock_key = f"lock:user_name:{username}"

    data = redis.hgetall(redis_key)
    if data:
        if "__NULL__" in data:
            raise HTTPException(status_code=404, detail="User not found")
        if data.get("userpassword") != hashed_pwd:
            raise HTTPException(status_code=400, detail="Wrong password")
        return {"message": "Login successful", "user_id": int(data["id"])}

    # Mutex lock for cache breakdown protection
    locked = redis.set(lock_key, "1", nx=True, ex=10)
    if locked:
        try:
            user = db.fetch_one(
                "SELECT id, userpassword FROM users WHERE username = %s", (username,)
            )
            if user:
                # ... cache and verify ...
            else:
                redis.hset(redis_key, mapping={"__NULL__": "1"})
                redis.expire(redis_key, 120)
                raise HTTPException(status_code=404, detail="User not found")
        finally:
            redis.delete(lock_key)
```

### 关键点 / Key Points

| 概念 / Concept | 说明 / Explanation |
|:---|:---|
| SHA-256 | 密码不能明文存，哈希后存储 / Never store plaintext passwords |
| Null Cache | 用 `__NULL__` 标记空值，防缓存穿透 / Prevents cache penetration |
| Mutex Lock | `redis.set(lock_key, "1", nx=True, ex=10)` 防缓存击穿 / Prevents cache breakdown |

---

## 📝 五、文章模块 / Articles API

### 端点一览 / Endpoints

| 方法 / Method | 路径 / Path | 功能 / Function |
|:---|:---|:---|
| `POST` | `/articles` | 创建文章（支持标签）/ Create article (with tags) |
| `GET` | `/articles/{id}` | 查文章详情（含标签）/ Get article detail (with tags) |
| `GET` | `/article/latest` | 查最新文章 / Get latest article |
| `GET` | `/articles/{id}/tags` | 查文章标签列表 / Get article tags |

### 创建文章 / Create Article

**EN:** Insert into MySQL, cache as Redis Hash, also cache tags as Redis Set.

**CN:** 写入 MySQL，缓存到 Redis Hash，标签单独存 Redis Set。

```python
class Article(BaseModel):
    title: str
    content: str
    tags: list[str] = []

@router.post("/articles")
def post_articles(article: Article):
    article_id = db.insert(
        "INSERT INTO articles (title, content, author_id) VALUES (%s, %s, %s)",
        (article.title, article.content, 1)
    )
    # 缓存文章 / Cache article
    redis.hset(f"article:{article_id}", mapping={"title": article.title, "content": article.content})
    redis.expire(f"article:{article_id}", 300 + random.randint(0, 120))

    # 缓存标签 / Cache tags
    if article.tags:
        db.insert_many("INSERT INTO article_tags (article_id, tag) VALUES (%s, %s)",
                       [(article_id, t) for t in article.tags])
        redis.sadd(f"article:{article_id}:tags", *article.tags)
        redis.expire(f"article:{article_id}:tags", 300 + random.randint(0, 120))
```

### 查文章详情 / Get Article Detail

**EN:** Read from Redis Hash first. If missing, fallback to MySQL with mutex lock. Also fetches tags.

**CN:** 先读 Redis Hash，未命中则用互斥锁回源 MySQL，同时查标签。

```
请求 / Request:  GET /articles/5

① Redis Hash:  "article:5" ──→ 命中 → 返回 title + content
                               │
                               未命中
                               │
② 互斥锁:      SET lock:article:5 NX EX 10
               抢到锁 → 查 MySQL → 写回 Redis → 释放锁
               没抢到 → 429 Too Many Requests

③ Redis Set:   "article:5:tags" → SMEMBERS 拿到 ["python", "redis"]
```

### 缓存更新策略 / Cache Update Strategy

**EN:** Cache-aside (lazy loading). Cache is written on read (with lock) and on write (without lock because Redis is single-threaded).

**CN:** Cache-aside 懒加载模式。读时写缓存（加锁），写时也写缓存（不用锁，Redis 单线程保证原子性）。

---

## ❤️ 六、点赞和热度 / Likes & Hot Ranking

### 端点一览 / Endpoints

| 方法 / Method | 路径 / Path | 功能 / Function |
|:---|:---|:---|
| `POST` | `/articles/{id}/likes` | 点赞 / Like an article |
| `GET` | `/articles/{id}/likes` | 查点赞数 / Get like count |
| `GET` | `/articles/hot` | 热度排行榜 Top 10 / Hot ranking |

### 点赞的原子性 / Atomic Like

**EN:** Use Redis Lua script to atomically increment the like count AND update the hot ranking ZSet. No race condition possible.

**CN:** 用 Redis Lua 脚本原子地**同时**增加点赞数和更新热度排行榜 ZSet，没有竞态条件。

```python
lua_script = """
    local likes = redis.call("INCR", KEYS[1])
    redis.call("ZINCRBY", KEYS[2], 1, KEYS[3])
    return likes
"""

redis.eval(lua_script, 3, "article:5:likes", "article:hot", "5")
# KEYS[1] = "article:5:likes"    ← 点赞数 key
# KEYS[2] = "article:hot"        ← 热度排行榜 key
# KEYS[3] = "5"                  ← ZSet member (article_id)
```

**EN:** Lua guarantees INCR and ZINCRBY execute as one atomic unit. The MySQL UPDATE runs separately (Lua can't access MySQL).

**CN:** Lua 保证 INCR 和 ZINCRBY 作为一个原子单元执行。MySQL UPDATE 单独运行（Lua 无法访问 MySQL）。

### 热度排行榜 / Hot Ranking

**EN:** Uses Redis Sorted Set (ZSet) with `ZREVRANGE` to get the top 10 articles by like count.

**CN:** 用 Redis Sorted Set (ZSet)，`ZREVRANGE` 按点赞数降序取前 10。

```python
@router.get("/articles/hot")
def get_article_hot():
    # Try cache first
    data = redis.zrevrange("article:hot", 0, 9, withscores=True)
    if data:
        return {"articles": [{"article_id": aid, "likes": int(score)}
                            for aid, score in data], "source": "cache"}

    # Fallback to MySQL with mutex lock
    result = db.fetch_all("SELECT id, likes FROM articles ORDER BY likes DESC LIMIT 10")
    for item in result:
        redis.zadd("article:hot", {item["id"]: item["likes"]})
    redis.expire("article:hot", 300 + random.randint(0, 120))
    return {"articles": [{"article_id": item["id"], "likes": item["likes"]}
                        for item in result], "source": "database"}
```

### 为什么 MySQL 不需要锁？ / Why No Lock on MySQL?

**EN:** `redis.eval(Lua)` is atomic — INCR and ZINCRBY always match. The MySQL `UPDATE articles SET likes = likes+1` is also atomic at the SQL level. A small inconsistency between Redis and MySQL likes is acceptable (eventual consistency).

**CN:** Lua 脚本保证 Redis 里点赞数和排行版**绝对一致**。MySQL 的 `likes = likes+1` 本身也是原子的。Redis 和 MySQL 之间少量不一致是可接受的（最终一致性）。

---

## 🏷️ 七、标签系统 / Tags API

### 端点一览 / Endpoints

| 方法 / Method | 路径 / Path | 功能 / Function |
|:---|:---|:---|
| `GET` | `/articles?tag=xxx` | 按标签搜索文章 / Search articles by tag |
| `GET` | `/articles/{id}/tags` | 查某文章的所有标签 / Get tags of an article |

### 数据模型 / Data Model

**EN:** Many-to-many relationship via `article_tags` table. Tag column has an index for fast lookup.

**CN:** 通过 `article_tags` 表实现多对多关系。`tag` 列建有索引，查询快。

```sql
CREATE TABLE article_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL,
    tag VARCHAR(50) NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    INDEX idx_tag (tag)
);
```

### 按标签搜索 / Search by Tag

**EN:** Cache the list of article IDs in a Redis Set keyed by tag name. Fallback to a JOIN query.

**CN:** 缓存结果到 Redis Set，key 是标签名。回源时 JOIN 查询。

```
请求 / Request:  GET /articles?tag=python

① Redis:  SMEMBERS "tags:python" ──→ ["1", "3", "7"]
                                       │
                                       │ 未命中
                                       ▼
② MySQL:  SELECT a.id, a.title
           FROM articles a
           JOIN article_tags t ON a.id = t.article_id
           WHERE t.tag = "python"
           ORDER BY a.created_at DESC
```

### Null Cache 保护 / Null Cache Protection

**EN:** If no article has that tag, cache `__NULL__` with a short TTL to prevent cache penetration.

**CN:** 如果标签没有文章，缓存 `__NULL__` + 短 TTL，防止穿透。

```python
rows = db.fetch_all("SELECT article_id FROM article_tags WHERE tag = %s", (tag,))
if rows:
    article_ids = [row["article_id"] for row in rows]
    redis.sadd(cache_key, *article_ids)
else:
    redis.sadd(cache_key, "__NULL__")      # 空缓存 / Null cache
    redis.expire(cache_key, 120 + random.randint(0, 60))
```

---

## 🧠 八、缓存策略总结 / Caching Strategy

### 五种缓存模式 / Five Caching Patterns

| 模式 / Pattern | 数据结构 / Data Structure | 用途 / Use Case | 示例 / Example |
|:---|:---|:---|:---|
| **Hash** | `HSET` / `HGETALL` | 对象缓存 / Object cache | 文章、用户详情 |
| **Set** | `SADD` / `SMEMBERS` | 列表缓存 / List cache | 文章标签、按标签搜文章 |
| **String** | `SET` / `GET` | 计数器 / Counter | 点赞数 |
| **Sorted Set** | `ZINCRBY` / `ZREVRANGE` | 排行榜 / Leaderboard | 热度排行 Top 10 |
| **Hash** | `HSET` | 最新文章 / Latest item | 最新文章缓存 |

### 三大缓存问题 / Three Cache Problems

| 问题 / Problem | 原因 / Cause | 解决方案 / Solution |
|:---|:---|:---|
| **穿透 / Penetration** | 查不存在的数据，每次都打 MySQL | `__NULL__` 空值缓存 + 短 TTL |
| **击穿 / Breakdown** | 热点 key 过期瞬间，大量请求打 MySQL | 互斥锁 `SET NX EX` |
| **雪崩 / Avalanche** | 大量 key 同时过期 | TTL 加随机偏移 `random.randint(0, 120)` |

### 互斥锁流程 / Mutex Lock Flow

```
请求 1 ──→ 缓存未命中 ──→ SET NX 抢到锁 ──→ 查 MySQL ──→ 写缓存 ──→ 删锁 ──→ 返回
请求 2 ──→ 缓存未命中 ──→ SET NX 没抢到 ──→ 429 Too Many Requests
请求 3 ──→ 缓存已命中 ──→ 直接返回
```

**EN:** Only one request hits MySQL when the cache expires. Others either wait (429) or hit the new cache.

**CN:** 缓存过期时只有一个请求打到 MySQL，其他的要么返回 429，要么命中新缓存。

### Lua 脚本原子性 / Lua Script Atomicity

```python
# ✅ Redis 内部原子：INCR + ZINCRBY 同时成功或同时不成功
# ✅ Atomic within Redis: INCR + ZINCRBY succeed or fail together
likes = redis.eval(lua_script, 3, cache_key, "article:hot", str(article_id))

# ❌ MySQL 在 Lua 外面，无法保证和 Redis 一起原子
# ❌ MySQL runs outside Lua, can't be atomic with Redis
db.update("UPDATE articles SET likes = likes+1 WHERE id = %s", (article_id,))
```

---

## 🧪 九、测试 / Testing

**EN:** Test all endpoints end-to-end. Start the server and use curl or Swagger UI.

**CN:** 端到端测试所有接口。启动服务后用 curl 或 Swagger UI。

### 1. 注册 / Register

```bash
curl -X POST "http://127.0.0.1:8000/logup?username=alice&email=alice@test.com&userpassword=123456"
```

### 2. 登录 / Login

```bash
curl -X POST "http://127.0.0.1:8000/login?username=alice&userpassword=123456"
```

### 3. 创建文章（带标签）/ Create Article with Tags

```bash
curl -X POST "http://127.0.0.1:8000/articles" \
  -H "Content-Type: application/json" \
  -d '{"title": "Redis Guide", "content": "Learn Redis", "tags": ["redis", "database"]}'
```

### 4. 查看文章 / Get Article

```bash
curl "http://127.0.0.1:8000/articles/1"
```

### 5. 点赞 / Like

```bash
curl -X POST "http://127.0.0.1:8000/articles/1/likes"
```

### 6. 热度排行 / Hot Ranking

```bash
curl "http://127.0.0.1:8000/articles/hot"
```

### 7. 按标签搜索 / Search by Tag

```bash
curl "http://127.0.0.1:8000/articles?tag=redis"
```

---

## 📝 总结 / Summary

| 知识点 / Topic | 掌握程度 / Level |
|:---|:---:|
| FastAPI + MySQL + Redis 项目结构 / Project Structure | ✅ 理解 / Understand |
| 连接池封装 / Connection Pool Encapsulation | ✅ 熟练 / Proficient |
| Redis Hash 缓存 / Redis Hash Cache | ✅ 熟练 / Proficient |
| Redis Set 缓存 / Redis Set Cache | ✅ 理解 / Understand |
| Redis ZSet 排行榜 / Redis Sorted Set Leaderboard | ✅ 理解 / Understand |
| Lua 脚本原子性 / Lua Script Atomicity | ✅ 基本理解 / Basic Understanding |
| 互斥锁防击穿 / Mutex Lock for Breakdown | ✅ 理解 / Understand |
| 空值缓存防穿透 / Null Cache for Penetration | ✅ 理解 / Understand |
| TTL 随机化防雪崩 / TTL Randomization for Avalanche | ✅ 理解 / Understand |
| 标签多对多关系 / Many-to-Many Tags | ✅ 理解 / Understand |

> **下一步 / Next Up:** DAY4 — 进阶优化，连接池调优，读写分离，慢查询
