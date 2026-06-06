# DAY2: Redis 5 Data Types in Action — Blog Caching System
# DAY2: Redis 五种数据类型实战 — 博客缓存系统

> **适合人群**：学完 DAY1（String 缓存三兄弟）的同学，想了解 Redis 全部五种数据类型在实际项目中怎么用。
>
> **学习方式**：跟着 API 接口走，边写边理解，每个数据类型对应一个真实场景。
>
> **中英双语 / Bilingual**

---

## 📋 目录 / Contents

1. [项目结构概览 / Project Overview](#-一项目结构概览--project-overview)
2. [String — 文章内容 & 点赞 / Article Content & Likes](#-二string--文章内容--点赞)
3. [Hash — 用户信息 / User Profile](#-三hash--用户信息)
4. [List — 最新文章 / Latest Articles](#-四list--最新文章)
5. [Set — 标签系统 / Tag System](#-五set--标签系统)
6. [ZSet — 热门排行榜 / Hot Ranking](#-六zset--热门排行榜)
7. [贯穿所有接口的防护模式 / Cache Protection Patterns](#-七贯穿所有接口的防护模式)
8. [常见坑 & FAQ / Pitfalls & FAQ](#-八常见坑--faq)
9. [如何运行 / How to Run](#-九如何运行--how-to-run)

---

## 📁 一、项目结构概览 / Project Overview

### 项目文件 / Project Files

```
Redis/DAY2/redis-blog-cache/
├── my_blog.py          # 主文件，所有 API 和缓存逻辑
├── database.py         # Redis 连接配置
├── config.py           # 项目配置
└── __pycache__/        # Python 缓存（自动生成）
```

### 关于 fake_db / About fake_db

**EN:** We use a simple in-memory Python dict (`fake_db`) instead of a real database. This keeps the focus on **Redis caching logic**, not SQL. In DAY5, we'll replace `fake_db` with SQLite/MySQL.

**CN:** 我们用 Python 字典 `fake_db` 模拟数据库，目的是把注意力集中在 **Redis 缓存逻辑** 上。DAY5 会换成真实数据库。

```python
# 模拟数据库 / Simulated database
fake_db = {
    "1": {
        "content": "That's too crazy! Redis is an in-memory data structure store...",
        "tags": [],
        "likes": 0
    },
    "2": {
        "content": "Do you know that Redis is a great caching solution?",
        "tags": [],
        "likes": 0
    }
}
```

### 五种数据类型总览 / 5 Data Types Overview

| # | 类型 Type | 应用场景 Use Case | 为什么用 Why This Type |
|---|--------|-----------------|---------------------|
| 1️⃣ | **String** | 文章内容、点赞计数 | 最简单的键值对，`INCR` 原子自增 |
| 2️⃣ | **Hash** | 用户信息 | 对象型数据，字段级读写 |
| 3️⃣ | **List** | 最新文章列表 | 按插入顺序排列，`LPUSH + LTRIM` 固定长度 |
| 4️⃣ | **Set** | 文章标签 | 无重集合，交集/并集/差集运算 |
| 5️⃣ | **ZSet** | 热门排行榜 | 带分数的有序集合，天然适合排名 |

---

## 🔴 二、String — 文章内容 & 点赞 / Article Content & Likes

### 为什么用 String？/ Why String?

**EN:** String is the most basic Redis data type — a key-value pair where the value can be any string (text, JSON, serialized object). It's perfect for:
- **Simple value storage**: article content, HTML fragments
- **Counters**: `INCR` / `DECR` are atomic — no race conditions
- **Distributed locks**: `SET NX` (key doesn't exist → create, or fail)

**CN:** String 是最基础的 Redis 数据类型，就是一个 key-value 对，value 可以是任何字符串。它最适合：
- **简单值存储**：文章内容、HTML 片段
- **计数器**：`INCR` / `DECR` 原子操作，不担心并发冲突
- **分布式锁**：`SET NX`（key 不存在才设置成功）

### 接口 1：获取文章内容 / GET /articles/{id}

```python
@app.get("/articles/{article_id}")
def get_article_content(article_id: int, retry: int = 3):
    redis = get_redis()
    article_id = str(article_id)
    cache_key = f"article:{article_id}"
    lock_key = f"lock:article:{article_id}"

    # Step 1: Try cache first / 先查缓存
    data = redis.get(cache_key)
    if data is not None:
        if data == "__NULL__":
            return {"data": None, "source": "cache"}
        return {"data": data, "source": "cache"}

    # Step 2: Cache miss → try to lock / 没命中 → 抢锁
    locked = redis.set(lock_key, "1", nx=True, ex=10)
    if locked:
        try:
            article_data = fake_db.get(article_id)
            if article_data:
                redis.setex(cache_key, 300 + random.randint(0, 120), article_data["content"])
                return {"data": article_data["content"], "source": "database"}
            else:
                redis.setex(cache_key, 120 + random.randint(0, 60), "__NULL__")
                return {"data": None, "source": "not_found"}
        finally:
            redis.delete(lock_key)
    else:
        # Step 3: Missed lock → retry / 没抢到 → 重试
        if retry <= 0:
            return {"data": None, "source": "Timeout"}
        time.sleep(1)
        return get_article_content(article_id, retry - 1)
```

#### 逐行解读 / Line-by-Line Explanation 🔍

```python
article_id: int
```

> **EN:** We declare `article_id` as `int`, not `str`. Why? Because `/articles/latest` is a static route. If `article_id` were `str`, FastAPI would match "latest" as an `article_id` and the `GET /articles/latest` endpoint would never be reached! By declaring `int`, "latest" fails the type check and falls through to the correct route.
>
> **CN:** 把 `article_id` 声明为 `int` 而不是 `str`。为什么？因为还有一个 `/articles/latest` 路由。如果 `article_id` 是 `str`，FastAPI 会把 "latest" 当成一个 article_id 捕获，`GET /articles/latest` 就永远走不到了！声明为 `int`，"latest" 类型不匹配，自动跳到正确的路由。

```python
data = redis.get(cache_key)
if data is not None:
    if data == "__NULL__":
        return {"data": None, "source": "cache"}
    return {"data": data, "source": "cache"}
```

> **EN:** Standard cache-aside pattern. First check Redis cache. `__NULL__` is our sentinel for "this article doesn't exist" — it prevents cache penetration (see section 7).
>
> **CN:** 标准的 cache-aside 模式。先查 Redis 缓存。`__NULL__` 是"这篇文章不存在"的空值标记——用来防穿透（详见第七节）。

```python
locked = redis.set(lock_key, "1", nx=True, ex=10)
```

> **EN:** `SET NX` = "set if not exists". This is a distributed lock. Only one process gets the lock, the rest retry. `ex=10` = auto-release after 10 seconds (safety net in case of crash).
>
> **CN:** `SET NX` = "不存在才设置"。这是一个分布式锁，保证只有一个进程去查数据库，其他进程等重试。`ex=10` = 10 秒自动释放（防止崩溃后锁永远不释放）。

```python
redis.setex(cache_key, 300 + random.randint(0, 120), ...)
```

> **EN:** `SETEX` = set value + TTL atomically. `300 + random(0, 120)` = base TTL plus a random offset. This prevents cache avalanche — if all keys expire at the same time, the database gets hammered.
>
> **CN:** `SETEX` = 设置值和过期时间，原子操作。`300 + random(0, 120)` = 基础过期时间加上随机偏移。这是为了防雪崩——如果所有 key 同时过期，数据库会被打爆。

```python
finally:
    redis.delete(lock_key)
```

> **EN:** Always release the lock in `finally`. If an exception occurs before `delete`, the lock stays locked and all future requests for this article will timeout. `finally` guarantees the lock is released no matter what.
>
> **CN:** 务必在 `finally` 中释放锁。如果 `try` 里异常了没走到 `delete`，这个锁就会一直存在，以后所有请求这篇文章的都会超时。`finally` 保证锁一定能释放。

### 接口 2-3：点赞系统 / Like System

```python
# Get like count / 获取点赞数
@app.get("/articles/{article_id}/likes")
def get_article_likes(article_id: str):
    redis = get_redis()
    count = redis.get(f"article:{article_id}:likes")
    return {"likes": int(count) if count else 0}

# Like an article / 点赞
@app.post("/articles/{article_id}/likes")
def post_article_likes(article_id: str):
    redis = get_redis()
    count = redis.incr(f"article:{article_id}:likes")
    redis.zincrby("hot:articles", 1, article_id)

    if article_id in fake_db:
        fake_db[article_id]["likes"] = count
    return {"likes": int(count)}
```

#### 为什么点赞用 String 而不是其他类型？/ Why String for Likes?

| 方案 | 问题 | 结论 |
|------|------|------|
| `INCR` (String) | 原子操作，一行搞定 | ✅ 最佳方案 |
| Hash field | 一个 Hash 存所有文章的点赞数，但操作某个 field 也要 O(1) | ❌ 没必要，过度设计 |
| ZSet 直接 replace | 单独点赞也要操作 ZSet，但 ZSet 适合排名的聚合查询 | ❌ 职责分离：String 管个体，ZSet 管全局 |

**EN:** Like count is a simple counter — String + INCR is the most natural and atomic choice. `GET` is O(1), `INCR` is atomic, no locks needed.

**CN:** 点赞数就是一个计数器——String + `INCR` 是最直观且原子的选择。`GET` 复杂度 O(1)，`INCR` 原子的，不需要额外加锁。

> 🕳️ **注意 / Note:** 这里 `zincrby` 同时更新 ZSet 排行榜，依赖关系在第六节解释。
> `zincrby` also updates the ZSet hot ranking — see Section 6 for the dependency.

---

## 🟡 三、Hash — 用户信息 / User Profile

### 为什么用 Hash？/ Why Hash?

**EN:** Hash stores field-value pairs inside one key. Think of it as a nested map: `user:alice → {username, email, password}`. It's ideal for objects because:
- Read/write individual fields without fetching the whole object
- `HGETALL` gives you the entire object
- More memory efficient than storing JSON strings for frequently updated fields

**CN:** Hash 在一个 key 里存多个 field-value 对。可以理解成嵌套的 map：`user:alice → {username, email, password}`。它适合对象型数据因为：
- 单独读写某个字段不用拿整个对象
- `HGETALL` 一次取出全部字段
- 比存 JSON 字符串更省内存（特别是经常只更新个别字段的情况）

### 接口 4-5：用户注册 & 查询 / Signup & Profile

```python
# Register / 注册
@app.post("/signup")
def sign_up(user: User):
    redis = get_redis()
    if user.username in User_db:
        raise HTTPException(status_code=409, detail="Username already exists")

    User_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "password": user.password
    }

    # Hash cache / Hash 缓存
    redis.hset(f"user:{user.username}", mapping={
        "username": user.username,
        "email": user.email,
        "password": user.password
    })
    redis.expire(f"user:{user.username}", 300 + random.randint(0, 120))
    return {"message": "User created successfully"}

# Get profile / 查询用户信息
@app.get("/users/{username}")
def get_user_profile(username: str, retry: int = 3):
    redis = get_redis()
    cache_key = f"user:{username}"
    lock_key = f"lock:user:{username}"

    user_data = redis.hgetall(cache_key)
    if user_data:
        if user_data.get("__NULL__"):
            return {"message": "User not found", "source": "Not found"}
        return {"username": user_data.get("username"), "email": user_data.get("email"), ...}
    else:
        # Lock + fallback to User_db
        locked = redis.set(lock_key, "1", nx=True, ex=10)
        if locked:
            try:
                user = User_db.get(username)
                if user:
                    redis.hset(cache_key, mapping={...})
                    redis.expire(cache_key, 300 + random.randint(0, 120))
                    return {"username": user["username"], ...}
                else:
                    redis.hset(cache_key, mapping={"__NULL__": "1"})
                    redis.expire(cache_key, 120 + random.randint(0, 60))
                    return {"message": "User not found", "source": "Not found"}
            finally:
                redis.delete(lock_key)
        else:
            # Retry logic...
```

#### Hash 的特殊之处 / Hash Specifics 🔍

```python
redis.hset(f"user:{username}", mapping={...})
redis.expire(f"user:{username}", 300 + random.randint(0, 120))
```

> **EN:** Note that `EXPIRE` applies to the **entire** Hash key, not individual fields. You can't set different TTLs for `username` vs `email` — they share the same expiry.
>
> **CN:** 注意 `EXPIRE` 是设置**整个 Hash key** 的过期时间，不是单独某个 field。`username` 和 `email` 共享同一个过期时间，不能分别设置。

```python
redis.hset(cache_key, mapping={"__NULL__": "1"})
```

> **EN:** For Hash, null-cache stores one dummy field. Why not a plain String? Because the GET endpoint uses `hgetall` — if the cache is a String type but we try `hgetall`, Redis would throw a type error. Consistent type = no surprise.
>
> **CN:** Hash 的空值缓存用 `hset` 一个假字段。为什么不用 String？因为 GET 接口用的是 `hgetall`——如果缓存里存的是 String 类型却调 `hgetall`，Redis 会报类型错误。保持类型一致，不出意外。

#### String 存 JSON vs Hash 存字段 / String JSON vs Hash Fields

| 方面 | String + JSON | Hash |
|------|-------------|------|
| 读一个字段 | 反序列化整个 JSON | `HGET` 直接取 |
| 更新一个字段 | 读 → 反序列化 → 改 → 序列化 → 写 | `HSET field new_value` |
| 内存效率 | 冗余的 JSON 括号和引号 | 更紧凑 |
| **推荐场景** | 不常修改的完整对象 | 频繁修改部分字段的对象 |

---

## 🟢 四、List — 最新文章 / Latest Articles

### 为什么用 List？/ Why List?

**EN:** List maintains insertion order — `LPUSH` adds to the head, `RPUSH` adds to the tail. Combined with `LTRIM`, it's a perfect **fixed-size latest-N list**.

**CN:** List 保持插入顺序——`LPUSH` 从左边插入，`RPUSH` 从右边插入。配合 `LTRIM`，它就是完美的**固定长度最新 N 条列表**。

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| `LPUSH` | O(1) | 从头部插入 |
| `LINDEX` | O(1) | 按索引访问 |
| `LTRIM` | O(N) | 裁剪到指定范围 |
| `LRANGE 0 -1` | O(N) | ⚠️ 取出全部元素，N 很大时慢 |

### 接口 6-7：发布文章 & 获取最新 / Publish & Latest

```python
# Publish article / 发布文章
@app.post("/articles")
def post_articles(article: Article):
    redis = get_redis()
    new_id = str(len(fake_db) + 1)
    fake_db[new_id] = {"content": article.content, "tags": [], "likes": 0}

    redis.lpush("articles:latest", new_id)
    redis.ltrim("articles:latest", 0, 9)      # keep only 10 latest
    redis.expire("articles:latest", 300 + random.randint(0, 120))
    return {"article_id": new_id}

# Get latest article / 获取最新文章
@app.get("/articles/latest")
def get_latest_articles(retry: int = 3):
    redis = get_redis()
    cache_key = "articles:latest"
    lock_key = "lock:articles:latest"

    latest = redis.lindex(cache_key, 0)       # get newest article ID
    if latest is not None:
        if latest == "__NULL__":
            return {"article_id": None, "source": "cache"}
        return {"article_id": latest, "source": "cache"}
    else:
        # Lock + fallback...
```

#### 为什么 List 只存 ID？/ Why List Stores Only IDs?

> **EN:** List stores article IDs, not the full content. Article content is cached via String (Section 2). If we stored everything in the List, every article publish would push megabytes of content into Redis. The List's job is just to maintain order — IDs are tiny (< 100 bytes).
>
> **CN:** List 只存文章 ID，不存文章内容。文章内容由 String 缓存（第二节）。如果把完整内容放进 List，每发一篇文章就 push 几 KB 内容进 Redis。List 的任务只是维持顺序——ID 很小（不到 100 字节）。

```python
redis.lpush("articles:latest", new_id)
redis.ltrim("articles:latest", 0, 9)
```

> **EN:** `LPUSH` pushes to the head → index 0 is always the newest. `LTRIM` keeps only the first 10 elements. Together they form a sliding window: every new article pushes the oldest one out.
>
> **CN:** `LPUSH` 从头部插入 → index 0 永远是最新的。`LTRIM` 只保留前 10 个。两者组合就是一个滑动窗口：每发一篇新文章，最老的一篇被挤出去。

#### 场景对比 / Use Case Comparison

| 场景 | 方案 | 原因 |
|------|------|------|
| 最新 10 条文章 | List + `LPUSH` + `LTRIM` | 天然固定长度，O(1) 插入 |
| 分页查询所有文章 | ZSet + `ZRANGE` | ZSet 支持范围查询 + 分页 |
| 消息队列 | List + `BLPOP` / `BRPOP` | 阻塞式弹出，天然队列 |

---

## 🟣 五、Set — 标签系统 / Tag System

### 为什么用 Set？/ Why Set?

**EN:** Set is an unordered collection of unique elements. Perfect for tags because:
- Tags are unique (you don't tag "Python" twice)
- Set operations: `SINTER` (intersection), `SUNION` (union), `SDIFF` (difference)
- Bidirectional index: article→tags AND tag→articles

**CN:** Set 是无序不重复集合。完美适合标签系统因为：
- 标签不能重复（不能打两个"Python"标签）
- 集合运算：`SINTER`（交集）、`SUNION`（并集）、`SDIFF`（差集）
- 双向索引：文章→标签 和 标签→文章

### 双向索引设计 / Bidirectional Index Design

```
┌──────────────────────────────────────────────────────┐
│                   Forward Index                      │
│                   正向索引                            │
│                                                       │
│   SADD articles:1:tags  Python  Redis  →  文章1有标签 │
│   SADD articles:2:tags  Redis  Docker  →  文章2有标签 │
└──────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────┐
│                  Reverse Index                       │
│                  反向索引                             │
│                                                       │
│   SADD tags:Python  1       →  Python标签下有文章1    │
│   SADD tags:Redis   1  2    →  Redis标签下有文章1,2  │
│   SADD tags:Docker  2       →  Docker标签下有文章2   │
└──────────────────────────────────────────────────────┘
        │                                                      
        ▼                                                      
   SINTER tags:Python tags:Redis → {"1"}  ← 同时有Python和Redis的文章
```

### 接口 8-10：标签系统三个接口 / Tag System 3 Endpoints

```python
# POST — Tag an article / 打标签
@app.post("/articles/{article_id}/tags")
def post_article_tags(body: Tagsbody, article_id: str):
    redis = get_redis()
    tags = body.tags

    # Forward index: article → tags / 正向
    redis.sadd(f"articles:{article_id}:tags", *tags)
    redis.expire(f"articles:{article_id}:tags", 300 + random.randint(0, 120))

    # Sync to fake_db / 同步到 fake_db
    article_data = fake_db.get(article_id)
    if article_data:
        for tag in tags:
            if tag not in article_data["tags"]:
                article_data["tags"].append(tag)

    # Reverse index: tag → articles / 反向（常驻内存）
    for tag in tags:
        redis.sadd(f"tags:{tag}", article_id)
        # No expire on reverse index — stays in memory permanently
        # 反向索引不过期，常驻内存

    return {"message": f"Message {article_id} has been tagged with {tags}"}

# GET 1 — Get tags of an article / 查文章有哪些标签
@app.get("/articles/{article_id}/tags")
def get_article_tags(article_id: str, retry: int = 3):
    redis = get_redis()
    tags = redis.smembers(f"articles:{article_id}:tags")

    if tags:
        if "__NULL__" in tags:
            return {"tags": None, "source": "cache"}
        return {"tags": list(tags), "source": "cache"}
    else:
        # Lock + fallback...

# GET 2 — Filter articles by tags / 按标签筛选文章
@app.get("/articles")
def get_articles_by_tags(tags: str = None):
    redis = get_redis()

    if not tags:
        return {"articles": list(fake_db.keys()), "source": "all"}

    tag_list = tags.split(",")
    cache_keys = [f"tags:{tag}" for tag in tag_list]

    # SINTER finds articles with ALL requested tags
    # SINTER 找同时包含所有标签的文章
    article_ids = redis.sinter(cache_keys)
    if article_ids:
        return {"articles": list(article_ids), "source": "cache"}

    # Fallback: traverse fake_db
    result = []
    for aid, data in fake_db.items():
        if all(tag in data["tags"] for tag in tag_list):
            result.append(aid)
    return {"articles": result, "source": "database"}
```

#### 反向索引为什么常驻内存？/ Why Keep Reverse Index in Memory? 🕳️

> **EN:** Imagine the reverse index (`tags:Python`) expires. When a user searches for "Python" articles:
> 1. `SMEMBERS tags:Python` → empty (expired)
> 2. Fallback to fake_db → traverse all articles, check if any has "Python" tag
> 3. Rebuild `tags:Python` with the results
>
> This O(N) rebuild is expensive when you have thousands of articles. Keeping the reverse index in memory is **space for time** — a few extra keys in Redis is worth the query speed.
>
> **CN:** 想象反向索引 `tags:Python` 过期了。用户搜索 "Python" 文章时：
> 1. `SMEMBERS tags:Python` → 空了（过期了）
> 2. 回退到 fake_db → 遍历所有文章，检查哪些有 "Python" 标签
> 3. 重新构建 `tags:Python`
>
> 这个 O(N) 的重建在文章很多时非常慢。让反向索引常驻内存是**以空间换时间**——Redis 里多几个 key 换来查询速度。

#### 管理反向索引的两种策略 / Two Strategies for Reverse Index

| 策略 | 做法 | 优点 | 缺点 |
|------|------|------|------|
| **常驻内存** | 反向索引不设 expire | 查询永远 O(1)，没有重建开销 | 占用内存，但 Set 很省（存 ID 而已） |
| **设 TTL + 重建** | expire 300s + fallback 时重建 | 节省内存 | 查询慢，重建复杂，TTL 到的时候就慢一次 |

**结论 / Verdict:** 对于标签这种数据量不大、ID 也很小的场景，常驻内存是正确选择。

### `SINTER` 的工作原理 / How SINTER Works

```
redis.sinter(["tags:Python", "tags:Redis", "tags:Docker"])
                │              │              │
                ▼              ▼              ▼
           {"1", "3"}     {"1", "2", "3"}  {"2", "3"}
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                          SINTER → {"3"}
                     (只有文章3同时有这三个标签)
```

---

## 🔵 六、ZSet — 热门排行榜 / Hot Ranking

### 为什么用 ZSet？/ Why ZSet?

**EN:** ZSet (Sorted Set) is like a Set but every member has a **score**. Redis sorts members by score automatically:
- `ZINCRBY` — increment score atomically
- `ZREVRANGE` — get Top N by score descending
- `ZRANGE` — get Bottom N or paginate

This is exactly what a hot ranking needs: each "like" increments the score, and we ask "who's in the top 10?"

**CN:** ZSet（有序集合）像 Set 但每个成员有**分数**。Redis 自动按分数排序：
- `ZINCRBY` — 原子递增分数
- `ZREVRANGE` — 取分数最高的 Top N（降序）
- `ZRANGE` — 取分数最低的或分页

这正是排行榜需要的：每次点赞加一分，然后问"谁是前十？"

### 接口 11：热门排行榜 / GET /articles/hot

```python
@app.get("/articles/hot")
def get_hot_articles(retry: int = 3):
    redis = get_redis()
    cache_key = "hot:articles"
    lock_key = "lock:hot:articles"

    # ZREVRANGE: get Top 10 by score descending
    hot_articles = redis.zrevrange(cache_key, 0, 9, withscores=True)

    if hot_articles:
        result = [{"article_id": aid, "likes": int(score)} for aid, score in hot_articles]
        return {"articles": result, "source": "cache"}
    else:
        locked = redis.set(lock_key, "1", nx=True, ex=10)
        if locked:
            try:
                # Sort fake_db by likes descending, take top 10
                articles = sorted(fake_db.items(),
                                  key=lambda x: x[1]["likes"],
                                  reverse=True)[:10]
                for aid, data in articles:
                    if data["likes"] > 0:
                        redis.zadd(cache_key, {aid: data["likes"]})
                redis.expire(cache_key, 300 + random.randint(0, 120))
                result = [{"article_id": aid, "likes": data["likes"]}
                          for aid, data in articles]
                return {"articles": result, "source": "database"}
            finally:
                redis.delete(lock_key)
        else:
            if retry <= 0:
                return {"articles": None, "source": "Timeout"}
            time.sleep(1)
            return get_hot_articles(retry - 1)
```

#### 点赞时的依赖关系 / Like-time Dependency

```python
# POST /articles/{id}/likes — 点赞时同时更新两个数据
def post_article_likes(article_id: str):
    count = redis.incr(f"article:{article_id}:likes")   # ① String: 个体点赞数
    redis.zincrby("hot:articles", 1, article_id)         # ② ZSet: 全局热度排名
    if article_id in fake_db:
        fake_db[article_id]["likes"] = count             # ③ fake_db: 持久化
    return {"likes": int(count)}
```

**EN:** Two data structures, one `INCR`. The String stores "how many likes does article 1 have?", the ZSet stores "what's the ranking of all articles?" They share the same increment — `INCR` returns the new count, `ZINCRBY` adds 1 to the score. Data stays in sync because they're updated together in one request.

**CN:** 两个数据结构，共享一次 `INCR`。String 存"文章1有多少赞"，ZSet 存"所有文章的排名"。它们共享同一次点赞操作——`INCR` 返回新计数，`ZINCRBY` 加 1 分。数据保持一致因为它们在同一个请求里一起更新。

#### 为什么不用 List 做排行榜？/ Why Not List for Rankings?

| 方案 | 插入新数据 | 获取 Top N | 排序 |
|------|-----------|-----------|------|
| List | `LPUSH` O(1) | `LRANGE 0 9` O(N) | ❌ 自己维护顺序 |
| **ZSet** | `ZADD` O(log N) | `ZREVRANGE 0 9` O(log N + N) | ✅ Redis 自动排序 |

> **EN:** You could sort a List with fake_db and push the sorted order, but every new like would need a re-sort. ZSet handles this automatically — scores update in-place, ranking adjusts in O(log N). For "Top N" queries, ZSet is the only correct choice among Redis data types.
>
> **CN:** 可以用 List + fake_db 排序后推入，但每点一次赞就要重新排序。ZSet 自动处理——分数原地更新，排名 O(log N) 调整。对于"Top N"查询，ZSet 是五种数据类型里唯一正确的选择。

---

## 🛡️ 七、贯穿所有接口的防护模式 / Cache Protection Patterns

**EN:** Every endpoint in DAY2 follows the same protection pattern. It's repetitive by design — once you've seen one, you've seen them all, and you'll never forget.

**CN:** DAY2 的所有接口都遵循同一套防护模式。看起来重复，但这是故意的——看懂一个就看懂了全部，永远忘不掉。

### 防护流程图 / Protection Flowchart

```
                          ┌──────────┐
                          │  Request  │
                          └────┬─────┘
                               │
                          ┌────▼─────┐
                          │  Redis   │  ← 1️⃣ 先查缓存
                          │  Cache   │
                          └────┬─────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
               ✅ HIT                  ❌ MISS
                    │                     │
              ┌─────▼──────┐       ┌──────▼──────┐
              │ Return     │       │  SETNX Lock │  ← 2️⃣ 抢分布式锁
              │ data       │       │  (ex=10s)   │
              └────────────┘       └──────┬──────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                          ✅ Got lock             ❌ Missed
                              │                       │
                        ┌─────▼──────┐         ┌─────▼──────┐
                        │ fake_db    │         │ Retry × 3  │  ← 3️⃣ 重试
                        │ (database) │         │ sleep 1s   │
                        └─────┬──────┘         └─────┬──────┘
                              │                      │
                        ┌─────▼──────┐         ┌─────▼──────┐
                        │ Set cache  │         │ Return     │
                        │ + TTL      │         │ Timeout    │
                        └─────┬──────┘         └────────────┘
                              │
                        ┌─────▼──────┐
                        │ finally:   │
                        │ del lock   │  ← 4️⃣ 释放锁（防死锁）
                        └─────┬──────┘
                              │
                        ┌─────▼──────┐
                        │ Return     │
                        │ data       │
                        └────────────┘
```

### 三种攻击/异常及解法 / 3 Threats and Their Solutions

| 问题 | 示意图 | 解法 | 代码体现 |
|------|--------|------|----------|
| 🔍 **穿透 / Penetration**<br>疯狂请求不存在的 key | `查不存在的ID → 每次都穿到DB` | 空值缓存 | `setex(key, 120, "__NULL__")` |
| 💥 **击穿 / Breakdown**<br>热点 key 到期 + 高并发 | `1个key过期 → 1000个请求同时打DB` | 分布式锁 | `SET NX lock` + 重试机制 |
| 🏔️ **雪崩 / Avalanche**<br>大量 key 同时到期 | `所有key一起过期 → DB被打垮` | 随机 TTL | `300 + random(0, 120)` |
| 💀 **Redis 宕机 / Outage** | `Redis挂了 → 服务全挂` | 本地 fallback | `fake_db.get()` 兜底 |

#### 常见误区 / Common Misconception 🕳️

> **EN:** "Should I also add null-cache for ZSet hot ranking?" No. An empty hot ranking is a valid state (no articles have likes yet). Null-cache is only for "this key doesn't exist and will never exist" scenarios. Zero likes = empty ZSet = valid, not a cache miss.
>
> **CN:** "ZSet 热门排行榜也要防穿透吗？"不需要。空的排行榜是有效状态（还没文章被点赞）。空值缓存只针对"这个 key 不存在且永远不会存在"的场景。零赞 = ZSet 为空 = 有效状态，不是缓存穿透。

---

## 🕳️ 八、常见坑 & FAQ / Pitfalls & FAQ

### 坑 1：路由冲突 / Route Conflict

**问题 / Problem:** FastAPI 按声明顺序匹配路由。如果 `GET /articles/{article_id}` 写在 `GET /articles/latest` 前面，"latest" 会被当成 `article_id` 捕获，`/articles/latest` 永远返回文章 "latest" 的内容。

**解法 / Fix:** 把 `article_id` 的类型从 `str` 改为 `int`：

```python
# ❌ Before: route conflict
def get_article_content(article_id: str):  # "latest" becomes article_id!

# ✅ After: type-safe routing
def get_article_content(article_id: int):  # "latest" fails type check → routes correctly
```

### 坑 2：`finally` 放错位置 / Misplaced finally Block

**问题 / Problem:** `try/finally` 被错误地放在 `if fake_db:` 分支内部，导致数据库为空时锁不释放。

```python
# ❌ Wrong: lock never released when fake_db is empty
if locked:
    try:
        if fake_db:
            ...
    finally:
        redis.delete(lock_key)  # Only in the `if fake_db` branch!

# ✅ Correct: finally wraps the entire locked block
if locked:
    try:
        ...
    finally:
        redis.delete(lock_key)  # Always executed
```

### 坑 3：`zrevrange` 返回值类型 / ZREVRANGE Return Type

**问题 / Problem:** `zrevrange` 返回的是空 list `[]` 而不是 `None`。所以 `if hot_articles is not None:` 永远是 True，即使没有数据。

```python
# ❌ Wrong: empty list is not None
hot_articles = redis.zrevrange(cache_key, 0, 9, withscores=True)
if hot_articles is not None:  # Always True!

# ✅ Correct: check truthiness of the list
hot_articles = redis.zrevrange(cache_key, 0, 9, withscores=True)
if hot_articles:  # False when list is empty
```

---

## 🚀 九、如何运行 / How to Run

### 前置条件 / Prerequisites

```bash
# 1. Install Redis 安装 Redis
#    Windows: Redis-x64-xxx.msi
#    macOS: brew install redis
#    Linux: sudo apt install redis-server

# 2. Start Redis 启动 Redis
redis-server

# 3. Verify Redis is running 验证 Redis 已启动
redis-cli ping
# Output: PONG

# 4. Install Python dependencies 安装 Python 依赖
pip install fastapi uvicorn redis
```

### 启动 API 服务 / Start the API Server

```bash
cd Redis/DAY2/redis-blog-cache
uvicorn my_blog:app --reload
```

输出应该看到 / You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 测试所有接口 / Test All Endpoints

```bash
# === String — 文章内容 / Article Content ===
curl http://localhost:8000/articles/1
# {"data":"That's too crazy! Redis is...","source":"database"}
# 第二次请求会走缓存 / Second request goes through cache
curl http://localhost:8000/articles/1
# {"data":"That's too crazy! Redis is...","source":"cache"}

# === String — 点赞 / Likes ===
curl -X POST http://localhost:8000/articles/1/likes
# {"likes":1}
curl http://localhost:8000/articles/1/likes
# {"likes":1}

# === Hash — 用户注册 & 查询 / User Signup & Profile ===
curl -X POST http://localhost:8000/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'
# {"message":"User created successfully"}

curl http://localhost:8000/users/alice
# {"username":"alice","email":"alice@example.com","password":"secret123","source":"user_base"}

# === List — 发布文章 & 取最新 / Publish & Get Latest ===
curl -X POST http://localhost:8000/articles \
  -H "Content-Type: application/json" \
  -d '{"content":"My first article!"}'
# {"article_id":"3"}

curl http://localhost:8000/articles/latest
# {"article_id":"3","source":"database"}
# 第二次 / Second request:
# {"article_id":"3","source":"cache"}

# === Set — 标签系统 / Tag System ===
# 打标签 / Tag articles
curl -X POST http://localhost:8000/articles/1/tags \
  -H "Content-Type: application/json" \
  -d '{"tags":["Python","Redis"]}'

# 查文章标签 / Get article tags
curl http://localhost:8000/articles/1/tags
# {"tags":["Python","Redis"],"source":"database"}

# 按标签筛选 / Filter by tags
curl "http://localhost:8000/articles?tags=Python,Redis"
# {"articles":["1"],"source":"cache"}

# === ZSet — 热门排行榜 / Hot Ranking ===
# 给文章 1 和 2 点赞（让它们有热度）
curl -X POST http://localhost:8000/articles/1/likes
curl -X POST http://localhost:8000/articles/2/likes
curl -X POST http://localhost:8000/articles/2/likes

# 查看排行榜 / Check hot ranking
curl http://localhost:8000/articles/hot
# {"articles":[{"article_id":"2","likes":2},{"article_id":"1","likes":2}],"source":"cache"}
```

---

## 📝 学习要点总结 / Key Takeaways

1. **每种数据类型都有明确的适用场景**
   - String: 简单值、计数器、锁
   - Hash: 对象/实体数据
   - List: 队列、最新列表、消息流
   - Set: 标签、集合运算、去重
   - ZSet: 排行榜、带权排序、分页

2. **缓存保护是套路，不是魔法**
   - 穿透 → 空值缓存
   - 击穿 → 分布式锁 + 重试
   - 雪崩 → 随机 TTL 偏移
   - 这三种模式在所有接口中高度一致

3. **缓存设计的关键问题**
   - 是否要缓存 null？（防穿透）
   - 过期时间设多久？（平衡数据新鲜度和命中率）
   - 要不要加随机偏移？（防雪崩）
   - 缓存 Redis 挂了怎么办？（fallback 到 DB）
   - 反向索引要不要常驻？（空间换时间）

4. **生产环境注意**
   - 这些防护模式可以封装为装饰器（但 DAY2 先不封，让你看熟）
   - DAY5 会把 fake_db 换成真正的 SQLite/MySQL
   - DAY4 会讲 Redis 高可用（主从复制 + Sentinel）

---

> **📝 关于本文 / About This Note**
>
> DAY2 完整实现了 Redis 五种数据类型在博客系统中的实战应用，覆盖了完整的缓存保护模式。
> DAY2 completes a hands-on implementation of all 5 Redis data types in a blog caching system with full cache protection.
>
> 下一阶段 / Next: **DAY3 — Redis 高级特性（过期策略、Pub/Sub、Pipeline、Lua 脚本）**
