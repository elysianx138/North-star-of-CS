# DAY3: Redis Advanced Features — Expiry, Eviction, Pub/Sub, Pipeline, Lua Scripting
# DAY3: Redis 高级特性 — 过期策略、内存淘汰、发布订阅、管道、Lua 脚本

> **适合人群 / For You:**
> 学完 DAY2（五种数据类型实战）的同学，想深入了解 Redis 背后的**高级能力**——不只是存数据，而是如何管理数据、实时通信、批量加速、原子操作。
>
> **学习方式 / Learning Approach:**
> 概念先行 + 代码实操。每个主题都先理解"为什么"，再动手写 demo，最后对比场景。
>
> **中英双语 / Bilingual**

---

## 📋 目录 / Contents

1. [项目结构 / Project Structure](#-一项目结构--project-structure)
2. [⏳ 过期策略 & 内存淘汰 / Expiry & Eviction](#-二过期策略--内存淘汰)
3. 📡 [发布订阅 Pub/Sub](#-三发布订阅-pubsub)
4. 🚀 [Pipeline 批量操作](#-四pipeline-批量操作)
5. 🔒 [Lua 脚本（原子性）](#-五lua-脚本原子性)
6. [常见坑 & FAQ / Pitfalls & FAQ](#-六常见坑--faq)
7. [总结 / Key Takeaways](#-七总结--key-takeaways)

---

## 📁 一、项目结构 / Project Structure

```
Redis/DAY3/advanced-feat-of-redis/
├── Expiration_Eviction_Policy.py    # ⏳ 过期策略 + 内存淘汰
├── Sub.py                           # 📡 Pub/Sub 订阅者
├── Pub.py                           # 📡 Pub/Sub 发布者
├── pipeline.py                      # 🚀 Pipeline vs 普通模式性能对比
├── lua_demo.py                      # 🔒 Lua 入门 demo
└── lua_practice.py                  # 🔒 Lua 实战：原子点赞
```

### 连接池统一配置 / Shared Connection Pool

本章所有 demo 共用同一个连接池模式：

```python
from redis import Redis, ConnectionPool

pool = ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=10,
    decode_responses=True
)

def get_redis():
    return Redis(connection_pool=pool)
```

> **🔍 为什么用连接池？/ Why Connection Pool?**
> 每次 `Redis()` 都创建一个新 TCP 连接（三次握手），高并发下浪费资源。连接池**预先创建一批连接**，用的时候借、用完还，复用开销几乎为 0。这在 DAY3 的 Pipeline 和 Lua 批量操作中尤其重要。

---

## ⏳ 二、过期策略 & 内存淘汰 / Expiry & Eviction

### 文件 / File: `Expiration_Eviction_Policy.py`

### 2.1 基础 TTL / Basic TTL

#### 为什么需要 TTL？/ Why TTL?

**EN:** Cached data shouldn't live forever. If the source data changes, the cache should eventually reflect the update. TTL (Time-To-Live) is Redis's built-in "self-destruct" mechanism — set it and forget it.

**CN:** 缓存数据不能永远活着。源数据变了，缓存最终也得更新。TTL（存活时间）是 Redis 自带的"自动销毁"机制——设好就不用管了。

#### 核心代码 / Core Code

```python
redis.set("mykey", "value", ex=5)    # ← 5 秒后自动过期

for i in range(8):
    val = redis.get("mykey")
    ttl = redis.ttl("mykey")
    print(f"{i}s -> value:{val}, TTL:{ttl}")
    time.sleep(1)
```

#### 输出 / Output

```
0s -> value:value, TTL:5
1s -> value:value, TTL:4
...
5s -> value:value, TTL:-2      ← key 已消失
6s -> value:None,  TTL:-2
```

#### TTL 返回值解读 / TTL Return Values 🔍

| TTL 值 | 含义 | 场景 |
|--------|------|------|
| `正整数` | 还有多少秒过期 | 正常的 key |
| `-1` | key 存在，但**没有设置过期时间** | 持久数据，不会自动消失 |
| `-2` | key **不存在**（已过期或被删） | 过期了或被删了 |

```python
redis.ttl("mykey")  # → 5   还剩 5 秒
redis.ttl("mykey")  # → -2  已经没了
redis.persist("mykey")  # 去掉 TTL → ttl 变 -1
```

> **🕳️ 坑 / Pitfall:** `-1` 和 `-2` 容易搞混。记住：**-1 = 活着但永不超时，-2 = 已经不在了。**

---

### 2.2 惰性删除 & 定期删除 / Lazy Delete & Active Expire

#### 两种策略 / Two Strategies

Redis 过期 key 的清理**不是即时的**——TTL 到了不会立刻消失。而是靠两种策略配合：

```
惰性删除（Lazy Delete）                    定期删除（Active Expire）
    │                                           │
    │  "你不碰它，我就不删"                      │  "每隔 100ms 主动扫一波"
    │                                           │
    │  GET mykey → 检查 TTL → 过期就删           │ 随机抽取 20 个带 TTL 的 key
    │  SET mykey → 检查 TTL → 过期就删           │ 过期占比 > 25% → 继续扫
    │  你不操作 → 过期了也不删                    │  最多 25ms/次
    │                                           │
    └─────────── 两者互补 ───────────────────────┘
```

#### 核心代码 / Core Code

```python
redis.set("lazy_delete", "value", ex=3)
time.sleep(4)   # 等 4 秒，TTL 肯定过了

# 定期删除可能已经扫到了
print("Before GET:", redis.exists("lazy_delete"))
# 输出：0（定期删除已经清理了）或 1（还没被扫到）

redis.get("lazy_delete")  # ← 惰性删除触发
print("After GET:", redis.exists("lazy_delete"))
# 输出：0（get 触发惰性删除）
```

#### 关键理解 / Key Insight 🔍

```
时间线：
─┬────┬────┬────┬────┬────┬────┬────┬────→
 set   1s   2s   3s   4s   5s   6s   7s
ex=3        ↑               ↑
         TTL 到期      GET 触发惰性删除
                        （或定期删除提前扫到）
```

**EN:** Between second 3 and whenever you `GET`, there's a window where the key is "logically expired but physically alive." Lazy delete and active expire both try to close this window.

**CN:** 从 TTL 到期（第 3 秒）到你访问 key 之间，有一个"逻辑上已过期但物理上还活着"的时间窗口。惰性删除和定期删除共同缩小这个窗口。

> **🔍 面试重点：为什么需要两种策略？**
> - 只有惰性删除 → 你一直不访问的 key 永远占着内存（内存泄漏）
> - 只有定期删除 → 扫不到的热点 key 一直活着读到旧数据（数据不一致）
> - 两者互补：**惰性保 "别浪费 CPU" + 定期保 "别浪费内存"**

---

### 2.3 内存淘汰 / Memory Eviction

#### 为什么需要淘汰？/ Why Eviction?

**EN:** What happens when Redis runs out of memory? It can't just crash — it needs a policy to decide which keys to sacrifice. Think of it as Redis's "triage" system.

**CN:** Redis 内存满了怎么办？不能直接崩溃——它需要一个策略来决定**牺牲哪些 key 腾空间**。这就是 Redis 的"分诊系统"。

#### 8 种淘汰策略 / 8 Eviction Policies

| 策略 | 淘汰范围 | 淘汰算法 | 说人话 |
|------|---------|---------|--------|
| **noeviction** | — | 直接报错 | 满了就不让写（默认） |
| **allkeys-lru** | 所有 key | LRU | 删最近最少用的 |
| **allkeys-lfu** | 所有 key | LFU | 删访问最少的 |
| **allkeys-random** | 所有 key | 随机 | 随便删一个 |
| **volatile-lru** | 带 TTL 的 key | LRU | 只在快过期的里面删最久没用的 |
| **volatile-lfu** | 带 TTL 的 key | LFU | 只在快过期的里面删最少访问的 |
| **volatile-ttl** | 带 TTL 的 key | TTL 最短 | 删最快到期的 |
| **volatile-random** | 带 TTL 的 key | 随机 | 只在快过期的里面随便删 |

#### LRU vs LFU 对比 / LRU vs LFU 🔍

```
LRU（Least Recently Used）                    LFU（Least Frequently Used）
    │                                           │
    │  看"上次访问时间"                          │  看"访问频率"
    │                                           │
    │  场景：                                     │  场景：
    │  你突然访问了一下老文章 → LRU 误判为"常用"  │  新闻每小时一次批量访问 →
    │  LFU 只看频次，不受单次访问干扰              │  LRU 每次都淘汰掉它
    │                                           │
    │  适用：热点会在一段时间内密集访问             │  适用：冷热差异明显，但热不是突发
```

> **🔍 注意：Redis 的 LRU/LFU 是近似实现**
> Redis 不会扫描全部 key——那样太慢了。默认从 `maxmemory-samples 5` 个 key 里挑出最该淘汰的。这叫**采样近似 LRU/LFU**，效率和精度之间取平衡。

#### 核心代码 / Core Code

```python
# 设置淘汰策略为 noeviction
redis.config_set("maxmemory", 1024 * 1024 * 2)  # 限制 2MB
redis.config_set("maxmemory-policy", "noeviction")

count = 0
try:
    while True:
        redis.set(f"key{count}", "value")
        count += 1
except ResponseError as e:
    print(f"Full! Can't write! {count} keys: {e}")
```

#### 实验对比 / Experiment 🔍

| 策略 | `maxmemory=2MB` | 结果 |
|------|----------------|------|
| `noeviction` | 满 2MB 时报错 | 写入被拒绝 |
| `allkeys-lru` | 满 2MB 时删旧 key | 持续写入成功 |

#### 怎么选？/ How to Choose?

```
你的 Redis 缓存有 TTL 吗？
    │
    ├── 有 → 用 volatile-lru
    │       原因：TTL 本来就要过期的 key 优先淘汰，影响最小
    │
    └── 没有 → 用 allkeys-lru
            原因：所有 key 一视同仁，LRU 是最通用的选择
```

> **🕳️ 坑 / Pitfall:** 设置 `maxmemory` 时必须高于 Redis 当前已用内存（`INFO memory` 里的 `used_memory`）。设得太低（比如 1MB），Docker 里的 Redis 自身 baseline 就要几百 KB，一写就报错。

---

## 📡 三、发布订阅 Pub/Sub

### 文件 / Files: `Sub.py`（订阅者）, `Pub.py`（发布者）

### 3.1 概念 / Concept

**EN:** Pub/Sub (Publish/Subscribe) is Redis's built-in **messaging system**. Think of it as a radio station — the publisher broadcasts on a channel, and all subscribers tuned to that channel hear the message. Redis acts as the radio tower.

**CN:** Pub/Sub 是 Redis 自带的**消息系统**。想象成广播电台——发布者在某个频道上广播，订阅了这个频道的听众都能收到。Redis 就是那个信号塔。

```
                             ┌─────────────────┐
   Publisher ──PUBLISH──→    │    Redis 服务器    │    ←──SUBSCRIBE──  Subscriber A
   (Pub.py)                 │  (频道转发器)       │    ←──SUBSCRIBE──  Subscriber B
                             │  channel:          │
                             │  "event:test"      │
                             └─────────────────┘
```

### 3.2 核心命令 / Core Commands

```
SUBSCRIBE channel       ── 订阅频道
PUBLISH channel msg     ── 发布消息到频道
UNSUBSCRIBE channel     ── 退订频道
PSUBSCRIBE pattern      ── 模式匹配订阅（如 news:*）
```

### 3.3 订阅者代码 / Subscriber Code (`Sub.py`)

```python
def subscribe_channel():
    redis = get_redis()
    pubsub = redis.pubsub()             # 创建 PubSub 对象（收音机）
    pubsub.subscribe("event:test")      # 调频到 event:test 频道

    print("Waiting for messages...")
    for message in pubsub.listen():     # 一直监听
        print(message)                  # message 是一个 dict
        if message["type"] == "message":
            print(message["data"])      # 只打印真正的消息内容
```

#### message 结构 / Message Structure 🔍

```python
# 订阅成功的确认
{'type': 'subscribe', 'pattern': None, 'channel': 'event:test', 'data': 1}
#                                                               ↑ 订阅了几个频道

# 真正的消息
{'type': 'message', 'pattern': None, 'channel': 'event:test', 'data': 'Hello,World!'}
```

`data: 1` 是订阅确认，不是业务消息。Redis 内部用它告诉你"你目前听了 1 个频道"。

### 3.4 发布者代码 / Publisher Code (`Pub.py`)

```python
def publish_channel():
    redis = get_redis()
    redis.publish("event:test", "Hello,World!")   # 一句话发消息
```

**EN:** Publisher is dead simple — one `publish()` call and you're done. The message goes to Redis, Redis forwards it to all subscribers, and the publisher moves on (fire-and-forget).

**CN:** 发布者极其简单——一句 `publish()` 就结束了。消息发给 Redis，Redis 转发给所有订阅者，发布者继续干别的事（即发即忘）。

### 3.5 运行方式 / How to Run

```bash
# 终端 1：启动订阅者
python Redis/DAY3/advanced-feat-of-redis/Sub.py

# 终端 2：启动发布者（在另一个窗口）
python Redis/DAY3/advanced-feat-of-redis/Pub.py
```

#### 预期输出 / Expected Output

```
# 终端 1（Sub.py）:
Waiting for messages...
{'type': 'subscribe', 'channel': 'event:test', 'data': 1}  ← 订阅成功确认
{'type': 'message', 'channel': 'event:test', 'data': 'Hello,World!'}  ← 收到消息
Hello,World!  ← 只打印 data
```

### 3.6 Pub/Sub 三大特性 / 3 Key Properties

| 特性 | 说明 | 影响 |
|------|------|------|
| 🚫 **消息不持久** | 发出去，订阅者没在线就丢了 | ❌ 不适合重要业务消息 |
| 🧱 **订阅者阻塞** | `SUBSCRIBE` 后这个连接不能干别的 | ✅ 需要单独一个连接专门监听 |
| 📡 **即发即收** | 没有队列，没有积压 | ✅ 延迟极低（微秒级） |

### 3.7 Pub/Sub vs 消息队列 / Pub/Sub vs Message Queue

| | Redis Pub/Sub | RabbitMQ / Kafka |
|---|---|---|
| **消息持久化** | ❌ 不存，发完就丢 | ✅ 持久化到磁盘 |
| **订阅者离线** | ❌ 离线消息就丢 | ✅ 上线后还能消费 |
| **性能** | ⚡ 极高（微秒级） | 🐢 较高（毫秒级） |
| **适用场景** | 实时通知、广播、系统内事件 | 可靠消息、事务、事件驱动架构 |

> **🔍 什么时候用 Pub/Sub？**
> 你的系统里，服务 A 做了某件事，需要立即通知服务 B 和服务 C——比如"有新文章发布了，更新缓存 + 推送通知"。如果丢几条通知无所谓（不涉及钱），Pub/Sub 是最轻量的方案。

---

## 🚀 四、Pipeline 批量操作

### 文件 / File: `pipeline.py`

### 4.1 为什么需要 Pipeline？/ Why Pipeline?

**EN:** Every Redis command is a **network round trip**. If you send 1000 commands one by one, that's 1000 network waits. Pipeline **batches them into one** — send all, receive all at once.

**CN:** 每条 Redis 命令都是一次**网络往返**。发 1000 条命令就要等 1000 次网络。Pipeline **把它们攒成一包**——一次发完，一次收完。

```
普通模式（1000 次往返）:
  Client                    Server
    │                        │
    ├── SET key0 ──────────→ │
    │←── OK ────────────────┤  每次等回复
    ├── SET key1 ──────────→ │
    │←── OK ────────────────┤
    │       ... 999 more     │

Pipeline（1 次往返）:
    │                        │
    ├── SET key0 ──────────┐ │
    ├── SET key1 ──────────┤ │
    ├── ...                ├─┤  一次全发过去
    ├── SET key999 ────────┘ │
    │                        │
    │←── OK × 1000 ─────────┤  结果一次回来
```

### 4.2 核心代码 / Core Code

```python
# ❌ 不用 Pipeline：一条一条发
start = time.time()
for i in range(1000):
    redis.set(f"key::{i}", i)
normal_time = time.time() - start

# ✅ 用 Pipeline：攒一批发
start = time.time()
with redis.pipeline() as pipe:      # 创建 pipeline
    for i in range(1000):
        pipe.set(f"key::{i}", i)    # 只是"记下来"，还没发
    pipe.execute()                   # ← 一次性全部发送 + 执行
pipeline_time = time.time() - start
```

### 4.3 性能对比 / Performance Comparison 🔍

| 方法 | 耗时（1000 条 SET） | 倍率 |
|------|-------------------|:----:|
| 无 Pipeline | **~1.37s** | 1×（基准） |
| 有 Pipeline | **~0.02s** | **~65× 更快** 🚀 |

**EN:** The 65× speedup isn't from Redis executing faster — it's from eliminating 999 network round trips. The more commands you batch, the bigger the win.

**CN:** 这 65 倍的提升不是 Redis 执行变快了——而是省掉了 999 次网络往返。批得越多，省得越多。

> **🕳️ 坑 / Pitfall:** Pipeline 不是事务！
> Pipeline 里的命令仍然是按顺序执行的，但如果某条命令失败了，**后面的命令照常执行**。它只负责"批量发"，不保证"全成功或全失败"。需要原子性 → 用 Lua。

### 4.4 Pipeline 适用场景 / When to Use Pipeline

| 场景 | 用 Pipeline？ | 原因 |
|------|:-----------:|------|
| 缓存预热（启动时批量写入） | ✅ 强烈推荐 | 几千条 SET，一次搞定 |
| 批量查询多个 key | ✅ 推荐 | 多条 GET，一次往返 |
| 正常业务请求（一个点赞） | ❌ 没必要 | 就一条命令，用了没区别 |
| 同时 SET + EXPIRE | ✅ 推荐 | 两步操作，一次网络 |
| 需要原子性 | ❌ 用 Lua | Pipeline 不保证原子性 |

---

## 🔒 五、Lua 脚本（原子性）

### 文件 / Files: `lua_demo.py`, `lua_practice.py`

### 5.1 为什么需要 Lua？/ Why Lua?

**EN:** Redis is single-threaded — one command runs at a time. But **multiple commands** from the same client can be interrupted by other clients. Lua scripts wrap multiple Redis commands into one atomic unit — no other client can interleave.

**CN:** Redis 是单线程的——一条命令执行时没人能打断。但**多条命令之间**可能会有别的客户端插进来。Lua 脚本把多条 Redis 命令打包成一个原子操作——没人能插队。

```
普通 Python 代码（不原子）:
    Thread A: INCR article:1:likes        ← +1
    Thread B:              INCR article:1:likes   ← 也 +1（插队）
    Thread A: ZINCRBY hot:articles 1 1    ← 更新热搜
    
    → 问题：两个点赞，但热搜只 +1！数据不一致

Lua 脚本（原子）:
    Thread A: [INCR + ZINCRBY] 整体执行  ← 没人能插进来
    Thread B: 等 Thread A 全部执行完
    
    → 点赞数和热搜完全一致 ✅
```

### 5.2 Lua 入门 / Lua Basics for Redis

```lua
-- 你只需要这 4 样东西写 Redis Lua：

redis.call("命令", "参数1", "参数2", ...)   -- 执行 Redis 命令
KEYS[1]                                       -- 接收 key 参数
ARGV[1]                                       -- 接收普通参数
local x = 1                                   -- 声明变量
```

#### 一个最简单的 Lua 脚本

```python
# lua_demo.py
lua_script = """
local count = redis.call("GET", KEYS[1])
if not count then
    return "not_found"
end
return count
"""

result = redis.eval(lua_script, 1, "mykey")
print(f"Lua result: {result}")
```

### 5.3 KEYS vs ARGV 的区别 / KEYS vs ARGV 🔍

```python
result = redis.eval(script, 2, "key1", "key2", "val1", "val2")
                             ↑       ↑       ↑       ↑       ↑
                          数量=2   KEYS[1] KEYS[2] ARGV[1] ARGV[2]
```

| 放 KEYS | 放 ARGV |
|---------|---------|
| **Redis key 的名字** | **普通值** |
| `"article:1"`、`"hot:articles"` | `"1"`（文章 ID）、`60`（过期时间） |
| 数量需在第 2 个参数声明 | 剩下的全是 ARGV |

> **🔍 为什么分 KEYS 和 ARGV？** Redis 集群需要知道脚本操作了哪些 key 才能路由到正确的节点。如果 key 名写在脚本字符串里，Redis 就不知道了。所以 **key 名必须通过 KEYS 传**，让 Redis 看得到。

#### 两种执行方式 / Two Execution Styles

| 方式 | 写法 | 适合场景 |
|------|------|---------|
| `redis.eval()` | 每次传完整脚本字符串 | 一次性测试 |
| `redis.register_script()` | 注册后复用（SHA 调用） | 生产环境、重复调用 |

```python
# 方法 1：eval（每次传完整脚本）
result = redis.eval("...", 3, "k1", "k2", "k3", "a1")

# 方法 2：register_script（注册后复用）
script = redis.register_script("""
    redis.call("SET", KEYS[1], ARGV[1])
    return redis.call("GET", KEYS[1])
""")
result = script(keys=["name"], args=["shiko"])
```

### 5.4 实战：原子点赞 / Atomic Like (`lua_practice.py`)

#### 需求 / Requirement

点赞要同时做三件事，且必须**原子完成**：
1. 检查文章是否存在
2. 点赞数 +1
3. 更新热搜排行榜

#### Lua 脚本 / Lua Script

```lua
-- 注册的 Lua 脚本（作为 Python 字符串）
local exists = redis.call("EXISTS", KEYS[1])
if exists == 0 then
    return "Article not found"
end

local likes = redis.call("INCR", KEYS[2])
redis.call("ZINCRBY", KEYS[3], 1, ARGV[1])

return likes
```

#### Python 调用 / Python Invocation

```python
# 注册脚本
atomic_likes = redis.register_script("""
    -- ...上面的 Lua 代码...
""")

# 调用：keys 放 key 名，args 放普通参数
result = atomic_likes(
    keys=["article:1", "article:1:likes", "hot:articles"],
    args=["1"]
)
print(f"Likes: {result}")  # 1st call → 1, 2nd call → 2
```

#### 执行流程 / Execution Flow 🔍

```
Python 调用                         Redis 内部（单线程）
    │                                   │
    ├── atomic_likes(keys=...,           │
    │    args=["1"])                     │
    │                                   │
    │                 ─────eval SHA──→   │
    │                                   ├── EXISTS article:1          ← ① 检查存在
    │                                   ├── INCR article:1:likes      ← ② 点赞 +1
    │                                   ├── ZINCRBY hot:articles 1 1 ← ③ 更新热搜
    │                                   │    ↑ 这三步之间无人能插进来！
    │                 ←── return 2 ──── │
    │                                   │   → 下一个请求开始
    ▼                                   ▼
```

### 5.5 Lua 脚本的使用原则 / Lua Best Practices

| 原则 | 解释 |
|------|------|
| 🎯 **只包需要原子的行** | Lua 不是让你把所有代码写进去——只把"怕被插队"的那几行包装起来 |
| ⏱️ **脚本要短** | 脚本执行期间 Redis 被锁住（不处理其他请求）。长脚本 = 长阻塞 |
| 🚫 **别调外部资源** | Redis Lua 是沙箱——没有文件 IO、没有网络请求、没有 print |
| 🔄 **优先用 `register_script`** | 第一次注册后 Redis 存 SHA，后续调用省带宽 |
| ✅ **一个命令能搞定的不用 Lua** | `INCR` 本身就是原子的。Lua 只解决"多条命令"的原子性问题 |

---

## 🕳️ 六、常见坑 & FAQ / Pitfalls & FAQ

### 坑 1：ConnectionPool 语法错误 / ConnectionPool Syntax

```python
# ❌ 错误：用了字典语法
pool = ConnectionPool(
    "host": "localhost",    # ← 这是字典，不是函数参数！
    "port": 6379,
)

# ✅ 正确：用关键字参数
pool = ConnectionPool(
    host="localhost",
    port=6379,
)
```

### 坑 2：TTL 的 -1 和 -2 搞混 / TTL Confusion

| TTL | 含义 |
|-----|------|
| `-1` | Key **存在**，但没有 TTL（永生） |
| `-2` | Key **不存在**（已过期或被删除） |

```python
redis.ttl("no_such_key")   # → -2  ️
redis.set("alive", "x")
redis.ttl("alive")          # → -1  （没设 ex，永久有效）
```

### 坑 3：`KEYS *` 看不到数据就是没写进去？/ KEYS * Shows Empty?

**可能是连错了 Redis 实例！**

检查你的 Python 连的是哪个 Redis：

```python
info = redis.info("server")
print(f"PID: {info['process_id']}")
print(f"Version: {info['redis_version']}")
```

**坑因：** 你电脑上可能同时跑着 Windows 原生 Redis + Docker Redis，Python 连了其中一个，但你用 `redis-cli` (docker 的) 查另一个。两个实例数据不互通。

### 坑 4：Pub/Sub 订阅确认消息干扰 / Subscribe Confirmation

```python
for message in pubsub.listen():
    print(message)
    # 第一次循环输出：
    # {'type': 'subscribe', 'data': 1, ...}  ← 不是业务消息！
```

**解法：** 加 `type` 过滤：

```python
for message in pubsub.listen():
    if message["type"] == "message":     # 只处理真正的消息
        print(message["data"])
```

### 坑 5：Pipeline 不是事务 / Pipeline ≠ Transaction

```python
pipe.set("a", "1")
pipe.set("b", "2")
pipe.execute()
# 如果 SET a 成功但 SET b 失败 → a 已经写进去了！
```

需要**要么全成功要么全失败** → 用 Lua 脚本，不是 Pipeline。

### 坑 6：Lua 脚本阻塞 Redis / Lua Script Blocking

```lua
-- ❌ 不要这样写！ 
for i = 1, 1000000 do
    redis.call("SET", "key" .. i, "value")
end
```

**EN:** While a Lua script runs, Redis can't handle ANY other requests — not even reads from other clients. Keep scripts short (< 10ms execution time).

**CN:** Lua 脚本执行期间，Redis **不处理任何其他请求**——其他客户端的读请求也不行。脚本要短（执行时间 < 10ms）。

---

## 📝 七、总结 / Key Takeaways

### 四个高级特性一句话总结

| 特性 | 一句话总结 | 你的 demo |
|------|-----------|-----------|
| ⏳ **过期策略** | TTL 不是精确的——惰性+定期配合工作 | TTL 从 5 → -2 的过程 |
| 🗑️ **内存淘汰** | 满了不能写 → 选个策略删旧 key | noeviction 报错 vs allkeys-lru 自动删 |
| 📡 **Pub/Sub** | 消息不存，即发即收，广播通知 | Sub.py 等消息，Pub.py 发消息 |
| 🚀 **Pipeline** | 攒一批命令，一次网络往返 | 快 65×，但要注意不是事务 |
| 🔒 **Lua 脚本** | 多条命令打包成原子操作，没人能插队 | 原子点赞：检查+INCR+ZINCRBY |

### 什么时候用什么 / Decision Guide

```
你要做的事                            → 用什么
────────────────────────────────────────────────
检查 key 是否存在再操作               → Lua 脚本（原子性）
多个服务需要实时收到通知               → Pub/Sub
批量写入/读取大量数据                  → Pipeline
内存满了决定删什么                     → 配置淘汰策略（allkeys-lru）
上面的组合拳                          → Lua + Pipeline（!only Lua is atomic）
```

### 进阶思考 / Next Steps

- **DAY4**：高可用——主从复制、Sentinel、持久化 RDB/AOF
- **DAY5**：整合项目——把 fake_db 换成真实数据库，打通全栈

---

> **📝 关于本文 / About This Note**
>
> DAY3 覆盖了 Redis 的四个高级特性：从数据生命周期管理（过期+淘汰）到实时通信（Pub/Sub），从性能优化（Pipeline）到原子操作（Lua）。每一个概念都配了可运行的 demo 和对比实验。
>
> DAY3 covers four advanced Redis features: data lifecycle management (expiry + eviction), real-time messaging (Pub/Sub), performance optimization (Pipeline), and atomic operations (Lua scripting). Each comes with a runnable demo and comparison.
>
> 下一阶段 / Next: **DAY4 — Redis 高可用（主从复制、Sentinel、持久化）**
