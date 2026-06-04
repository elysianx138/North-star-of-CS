# DAY1
> For absolute beginners — from installation to writing your first Redis integration!
>
> **English**

---

## 🎁 Requirement

- Basic understanding of Python (variables, functions, API concepts)
- Familiarity with common Redis commands: `SET`, `GET`, `SETEX`, `DEL`, `SET NX`
- Awareness of the 5 Redis data types: String, Hash, List, Set, ZSet
- Docker installed (for running Redis)

---

## 📥 Step 1: Installation

### Run Redis with Docker

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### Verify Redis is running

```bash
docker ps
docker exec -it redis redis-cli ping
# → PONG
```

### Basic connection test

```bash
docker exec -it redis redis-cli
127.0.0.1:6379> SET hello world
OK
127.0.0.1:6379> GET hello
"world"
```

---

## 🔈 Step 2: Introduction

### What is this project?

This is a hands-on tutorial for beginners stepping into the world of **Redis caching** with **FastAPI (Python)**. Instead of boring theory, you'll write real code and see Redis work in action.

### DAY1 covers the famous "Three Major Caching Problems"

Every backend developer faces these in interviews and real-world projects:

| Problem | Chinese Name | What Happens |
|---------|-------------|--------------|
| **Cache Penetration** | 缓存穿透 | Requesting data that exists **nowhere** (not in cache, not in DB) — every request hits the database directly, like piercing through the cache layer |
| **Cache Breakdown** | 缓存击穿 | A **hot key** expires exactly at peak concurrency — thousands of requests flood the database at once |
| **Cache Avalanche** | 缓存雪崩 | A large batch of keys expire **simultaneously**, or Redis itself goes down — massive database pressure |

### What you built in DAY1

A FastAPI application with Redis connection pool that demonstrates all three protections:

| Feature | Redis Data Type | Protection Strategy |
|---------|----------------|-------------------|
| Article content API | String | Cache penetration → null value caching (`__NULL__`) |
| Hot data API | String + SET NX | Cache breakdown → distributed mutex lock with retry |
| TTL randomization | String | Cache avalanche → `base TTL + random offset` |

### Key Files

| File | Purpose |
|------|---------|
| `config.py` | Redis connection configuration (host, port, pool size) |
| `database.py` | Connection pool management — reuse Redis connections efficiently |
| `main.py` | FastAPI application with all three caching solutions |

### What is a Connection Pool?

Instead of creating a new Redis connection on every request (slow ❌), a connection pool keeps a set of reusable connections ready. Your app borrows one, uses it, and returns it — like a library lending books.

```
Request 1 ─┐
Request 2 ─┼──→ Connection Pool (max 20) ──→ Redis
Request 3 ─┘
```

---

## ⚔️ Step 3: Cache Penetration (缓存穿透)

### The Problem

```python
# User requests: GET /articles/nonexistent
# Data doesn't exist in cache OR database
# Every request hits the database → database overload 😵
```

### The Solution — Null Value Caching

When data is not found anywhere, cache a special `__NULL__` marker with a **short TTL** (60-120s). Next time the same key is requested, Redis returns the null marker immediately — the database is never touched.

```text
Request → Check Redis → Not found → Check DB → Not found
              ↓
        Cache __NULL__ (short TTL: 60+random s)
              ↓
Next request → Redis returns __NULL__ → Return 404 immediately ✅
```

---

## 🔥 Step 4: Cache Breakdown (缓存击穿)

### The Problem

A super hot article (millions of views) — the cache expires at exactly the wrong moment. Suddenly every user request hits the database trying to rebuild the cache.

### The Solution — Mutex Lock (SET NX)

Only **one request** is allowed to rebuild the cache. Others wait and retry.

```text
Request A ──→ SET NX lock:hot:1 → Got lock! ✅ → Rebuild cache → Done
Request B ──→ SET NX lock:hot:1 → Lock taken ❌ → Sleep & retry
Request C ──→ SET NX lock:hot:1 → Lock taken ❌ → Sleep & retry
```

Key Redis command:

```
SET lock:hot:1 "1" NX EX 10
```

- `NX` = "set only if key does NOT exist" (atomic lock acquisition)
- `EX 10` = auto-expire after 10s (prevent deadlock if the holder crashes)

---

## ❄️ Step 5: Cache Avalanche (缓存雪崩)

### The Problem

Massive key expiry (or Redis going offline) → every request rushes to the database at once.

### The Solution — TTL Randomization

Instead of `SETEX key 3600 value` (all keys expire at the same time), use:

```python
TTL = 3600 + random.randint(0, 300)  # Spreads expiry across 5 minutes
```

Other protection strategies (mentioned, not implemented in DAY1):
- **Redis Sentinel / Cluster** — high availability (automatic failover)
- **Multi-level cache** — local memory cache (e.g., Python LRU) as a second layer

---

## 🎯 What You Learned

| Concept | Status |
|---------|--------|
| Docker Redis setup | ✅ |
| Redis connection pool | ✅ |
| String data type (GET/SET/SETEX) | ✅ |
| Three caching problems + solutions | ✅ |
| Distributed mutex lock (SET NX) | ✅ |
| TTL randomization | ✅ |
| FastAPI + Redis integration | ✅ |

---

## 📚 Project Structure

```
Redis/DAY1/
└── redis-cache-demo/
    ├── config.py        # Redis config
    ├── database.py      # Connection pool
    ├── main.py          # FastAPI app + 3 caching protections
    └── README.md        # This file (your summary)
```

---

## 💡 Pro Tips

1. **Always use connection pool** — creating a new Redis connection per request is expensive
2. **Null value TTL should be short** — otherwise real data can't be cached when it becomes available
3. **Lock expiration > rebuild time** — if rebuilding takes 2s, set lock EX to at least 5s
4. **Redis is single-threaded for commands** — don't run slow operations (`KEYS *`) in production

---

## 🔗 Next Up: DAY2

> Practice all 5 Redis data types with a blog caching project (String, Hash, List, Set, ZSet)
