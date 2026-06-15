# DAY4: MySQL 实战补强 / Practical Reinforcement

> **目标 / Goal:**
> 把之前学过但没亲手练的——**事务、索引、缓存策略**——实操一遍。
> 不学新理论，就三个实战。

---

## 📋 目录 / Contents

1. [项目结构 / Project Structure](#-项目结构--project-structure)
2. [事务实操 / Transaction Practice](#-一事务实操--transaction-practice)
3. [索引实操 / Index EXPLAIN Practice](#-二索引实操--index-explain-practice)
4. [缓存模拟 / Cache Simulation](#-三缓存模拟--cache-simulation)

---

## 📁 项目结构 / Project Structure

```
MySQL/DAY4/
├── README.md                   # 本文档
└── scripts/
    ├── 01_transaction.py       # 实操一：事务回滚模拟
    └── 02_index_explain.py     # 实操二：索引性能对比
```

实操三（缓存模拟）直接用 curl 调博客 API，不需要单独脚本。

---

## 一、事务实操 / Transaction Practice

**运行脚本：** `python scripts/01_transaction.py`

### 场景 / Scenario

银行转账：**Alice 给 Bob 转 100 元**

```
Alice 账户: 1000 元  ──→  -100
                            ──→  Bob 账户: 500 元  ──→  +100
```

**关键：** 中间任何一步失败，钱不能丢（原子性）。

### 脚本包含三个演示

| 演示 | 说明 | 关键代码 |
|:--|:--|:--|
| **1.1 正常转账** | BEGIN → 扣钱 → 加钱 → COMMIT | `conn.commit()` |
| **1.2 崩溃回滚** | BEGIN → 扣钱 → ROLLBACK | `conn.rollback()` |
| **1.3 隔离性** | 两个连接同时看同一笔数据 | 开两个 `get_conn()` |

### 关键输出解读

```
实操 1.1：正常转账（COMMIT）
  ➡️  Alice 扣了 100 元（未提交）
  ➡️  Bob 加了 100 元（未提交）
  ✅ COMMIT 提交成功！
     Alice: ¥900
     Bob:   ¥600

实操 1.2：模拟崩溃回滚（ROLLBACK）
  ➡️  Alice 扣了 100 元
  💥 执行 ROLLBACK...
     Alice: ¥1000    ← 钱回来了！
     Bob:   ¥500

实操 1.3：验证隔离性
  ➡️  连接 1：Alice 扣了 100 元（未提交）
     连接 2：Alice: ¥1000    ← 没提交，看不到新值
  ➡️  连接 1 提交了事务
     连接 2：Alice: ¥900     ← 提交后，才能看到
```

---

## 二、索引实操 / Index EXPLAIN Practice

**运行脚本：** `python scripts/02_index_explain.py`

### 场景 / Scenario

一张表 10 万行，对比**有索引**和**没索引**的差距。

### 脚本做的事

```
① 创建 perf_test 表
② 插入 10 万行数据
③ 无索引查询 → 看 type=ALL（全表扫描）+ 计时
④ 创建索引
⑤ 有索引查询 → 看 type=ref（索引查找）+ 计时
⑥ 对比结果
⑦ 演示索引失效场景
```

### 关键输出解读

```
🔍 无索引查询：
    type:  ALL           ← 全表扫描
    rows:  100000        ← 翻了 10 万行
    耗时:  0.0450 秒

⏳ 正在创建索引...

🔍 有索引查询：
    type:  ref           ← 索引查找
    rows:  1             ← 只查了 1 行
    耗时:  0.0010 秒

📊 对比总结
   无索引: 0.0450 秒  (全表扫描 10 万行)
   有索引: 0.0010 秒  (B+ 树直接定位)
   差距:   约 45 倍
```

> **注意：** 第一次数据可能不太悬殊（数据全在内存里），但如果表数据大到内存装不下，差距会到**几百倍**。

### EXPLAIN 是什么意思？

```
EXPLAIN SELECT * FROM perf_test WHERE value2 = 88888;
```

`EXPLAIN` 不是真的执行查询，而是问 MySQL **"你打算怎么查？"**

| 输出列 | 含义 |
|:--|:--|
| `type` | ALL = 全表扫描，ref = 索引查找，const = 主键查找 |
| `rows` | MySQL 估计要扫描多少行 |
| `Extra` | 额外信息（Using where, Using index 等） |

### 索引失效场景

脚本也会演示：

| 场景 | 原因 |
|:--|:--|
| `WHERE value1 = 'xxx'` | 没给 value1 建索引 |
| `WHERE value2 LIKE '%8888'` | LIKE 以 % 开头 |
| `WHERE value2 + 1 = 88889` | 索引列上用了函数/运算 |

---

## 三、缓存模拟 / Cache Simulation

不需要脚本，直接用 curl + redis-cli 操作你的博客 API。

### 准备工作

确保你的博客 API 在运行：

```bash
# 启动服务
uvicorn app:app --reload

# 创建一篇文章
curl -X POST "http://127.0.0.1:8000/articles" \
  -H "Content-Type: application/json" \
  -d '{"title": "Cache Test", "content": "Testing caching", "tags": ["test"]}'
```

### 3.1 缓存穿透

**原理：** 查不存在的 ID → 没缓存 → 每次都打 MySQL

```bash
# 第一次查不存在的文章（缓存未命中 → 查 MySQL → 写 __NULL__）
curl "http://127.0.0.1:8000/articles/99999"

# 第二次查（命中 __NULL__ 缓存，挡在 Redis，不查 MySQL）
curl "http://127.0.0.1:8000/articles/99999"

# 直接看 Redis 里缓存了什么
redis-cli GET "article:99999"
```

> **现象：** 第一次回源 MySQL，第二次直接挡在 Redis。第一次 404，第二次也是 404，但第二次**没查数据库**。

### 3.2 缓存击穿

**原理：** 热点 key 过期的瞬间，大量请求同时涌入

```bash
# 1. 先访问一次，让缓存建立
curl "http://127.0.0.1:8000/articles/1"

# 2. 手动删缓存（模拟过期）
redis-cli DEL "article:1"

# 3. 同时发多个请求（模拟并发）
curl "http://127.0.0.1:8000/articles/1" & \
curl "http://127.0.0.1:8000/articles/1" & \
curl "http://127.0.0.1:8000/articles/1" &
```

> **现象：** 第一个请求抢到互斥锁 → 查 MySQL → 写缓存。后面的请求要么返回 429（没抢到锁），要么直接命中新缓存。**不会所有请求都打到 MySQL。**

### 3.3 缓存雪崩

**原理：** 大量 key 同时过期 → 集体回源 MySQL

```bash
# 查看缓存还有多久过期
redis-cli TTL "article:1"

# 手动设一个很短的 TTL（模拟即将过期）
redis-cli EXPIRE "article:1" 5
```

> **你的代码已经防了：**
> ```python
> redis.expire(key, 300 + random.randint(0, 120))
> ```
> 每个 key 的 TTL 不一样，不会同时过期。

---

## 📝 总结

| 实操 | 你学到了什么 |
|:--|:--|
| ✅ **事务** | BEGIN/COMMIT/ROLLBACK，未提交的数据其他连接看不到 |
| ✅ **索引** | `EXPLAIN` 看 `type` / `rows`，加索引前后差几十倍 |
| ✅ **缓存穿透** | 查不存在的数据 → `__NULL__` 空值缓存 |
| ✅ **缓存击穿** | 热点 key 过期 → 互斥锁 `SET NX` |
| ✅ **缓存雪崩** | 大量 key 同时过期 → TTL 随机化 |

> **下一步 / Next Up:** Security DAY1 — SQL 注入防御 + 密码安全 + 日志规范
