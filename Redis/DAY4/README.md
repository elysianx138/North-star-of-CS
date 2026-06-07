# DAY4: Redis Persistence, Replication & Sentinel
# DAY4: Redis 持久化、主从复制与哨兵

> **适合人群 / For You:**
> 学完 DAY1-3，想了解 Redis 在生产环境如何保证数据不丢、如何高可用的同学。
>
> **学习方式 / Learning Approach:**
> Docker 操作 Redis 配置文件 + 命令行实验，不写 Python 代码。
>
> **中英双语 / Bilingual**

---

## 📋 目录 / Contents

1. [为什么要学这些？ / Why Learn This?](#-一为什么要学这些--why-learn-this)
2. [RDB 持久化 — 快照模式 / Snapshot Persistence](#-二rdb-持久化--快照模式)
3. [AOF 持久化 — 追加模式 / Append-only Persistence](#-三aof-持久化--追加模式)
4. [RDB vs AOF — 怎么选？ / Which One to Use?](#-四rdb-vs-aof--怎么选)
5. [主从复制 — 读写分离 / Master-Slave Replication](#-五主从复制--读写分离)
6. [Sentinel — 自动故障转移 / Automatic Failover](#-六sentinel--自动故障转移)
7. [常见坑 & FAQ / Pitfalls & FAQ](#-七常见坑--faq)

---

## 🔍 一、为什么要学这些？ / Why Learn This?

### 核心问题 / The Core Question

> **"Redis 是内存数据库，如果服务器宕机了，数据怎么办？"**
>
> **"Redis stores data in memory — what happens if the server crashes?"**

| 场景 / Scenario | 风险 / Risk | 解决方案 / Solution |
|:----|:----|:--------|
| 宕机重启 / Crash Restart | 内存数据全部丢失 | **持久化 / Persistence**：存到磁盘 |
| 单点故障 / Single Point Failure | 一台 Redis 挂了就不能用了 | **主从复制 / Replication**：备机顶上 |
| 自动切换 / Auto Switch | 主挂了需要手动切从 | **Sentinel / Sentinel**：自动故障转移 |

**EN:** DAY1-3 taught you how to USE Redis. DAY4 teaches you how to make Redis **reliable in production**.

**CN:** DAY1-3 教你用 Redis，DAY4 教你让 Redis **可靠地运行**。

---

## 📸 二、RDB 持久化 — 快照模式 / Snapshot Persistence

### 2.1 什么是 RDB？ / What is RDB?

**EN:** RDB (Redis Database) — takes a **snapshot** of all in-memory data at a given interval and writes it to disk.

**CN:** RDB 就是定时把内存中的数据**生成快照**写入磁盘。

```
Memory Data ──Snapshot──→ dump.rdb (disk file)
                            ↑
           SAVE / BGSAVE / Auto-trigger
```

### 2.2 触发方式 / Trigger Methods

| 方式 / Method | 命令 / Command | 特点 / Characteristic |
|:----|:----|:----|
| 手动同步 / Sync | `SAVE` | Blocks Redis until done (**never use in production**) |
| 手动异步 / Async | `BGSAVE` | Forks child process, main process continues ✅ |
| 自动触发 / Auto | Config `save` rules | e.g. 10000 writes in 60s → auto BGSAVE |

### 2.3 Docker 动手实验 / Hands-on Demo

```bash
# 1. Start a Redis container (disable AOF for RDB-only observation)
docker run -d --name redis-rdb -p 6379:6379 redis:7.4 redis-server --save "" --appendonly no

# 2. Write some data
docker exec -it redis-rdb redis-cli
```

```redis
SET user:1 "alice"
SET user:2 "bob"
SADD tags "redis" "docker"
```

```bash
# 3. Manually trigger BGSAVE
docker exec -it redis-rdb redis-cli BGSAVE

# 4. Check the RDB file
docker exec -it redis-rdb ls -la /data
# You should see dump.rdb

# 5. Check last save time
docker exec -it redis-rdb redis-cli LASTSAVE
# Returns a Unix timestamp
```

🔍 **Observations / 实验观察：**
- `BGSAVE` updates `LASTSAVE` to the current time
- RDB file is named `dump.rdb` by default, located in Redis working directory
- File is small (a few KB) — binary compressed format

### 2.4 RDB 配置 / RDB Configuration

```conf
# Auto-trigger rules (OR logic — any rule matched triggers BGSAVE)
save 60 10000     # 60s with ≥10000 writes
save 300 100      # 300s with ≥100 writes
save 3600 1       # 3600s with ≥1 write

# RDB filename
dbfilename dump.rdb

# Compress RDB (default yes, saves disk space)
rdbcompression yes

# Stop accepting writes if RDB fails (prevents data inconsistency)
stop-writes-on-bgsave-error yes
```

> **EN:** Multiple `save` rules use OR logic — satisfying ANY one triggers BGSAVE.
>
> **CN:** 多个 save 规则是"或"的关系，满足任一就触发。

### 2.5 RDB 优缺点 / Pros & Cons

| Pros / 优点 | Cons / 缺点 |
|:----|:----|
| ✅ Small file, great for backup/transfer | ❌ May lose data since last snapshot |
| ✅ Fast restart (load file directly) | ❌ `fork()` can be slow with large data |
| ✅ Minimal performance impact (BGSAVE) | ❌ Cannot guarantee real-time data safety |

---

## 📝 三、AOF 持久化 — 追加模式 / Append-only Persistence

### 3.1 什么是 AOF？ / What is AOF?

**EN:** AOF (Append Only File) — appends **every write command** to a file. On restart, Redis replays all commands to recover data.

**CN:** 把每一条**写命令**追加到文件末尾。重启时重新执行这些命令来恢复数据。

```
SET user:1 "alice"  ──→ appendonly.aof
SET user:2 "bob"    ──→ appendonly.aof
                      ...
Restart → Replay all commands → Data recovered
```

### 3.2 三种 fsync 策略 / Three fsync Strategies

| 策略 / Strategy | Config | Behavior | Data Safety | Performance |
|:----|:------|:----|:--------|:----:|
| 每秒一次 / Every Sec | `everysec` (default) | Flush to disk every 1s | Lose at most 1s data | ⭐⭐⭐ |
| 每次写入 / Always | `always` | Flush on every write | Nearly zero data loss | ⭐ |
| 由 OS 决定 / OS decides | `no` | OS decides when to flush | May lose seconds of data | ⭐⭐⭐⭐ |

> 🚩 **Production recommendation / 生产推荐：`everysec`**
>
> **EN:** The balance between performance and safety — Redis official default.
>
> **CN:** 性能和安全的平衡点，Redis 官方也默认这个。

### 3.3 Docker 动手实验 / Hands-on Demo

```bash
# 1. Start a Redis with AOF enabled (no RDB)
docker run -d --name redis-aof -p 6380:6379 redis:7.4 redis-server --save "" --appendonly yes --appendfsync everysec

# 2. Write some data
docker exec -it redis-aof redis-cli
```

```redis
SET article:1 "Redis AOF demo"
SET article:2 "How persistence works"
INCR counter:page_views
```

```bash
# 3. View AOF file content (human-readable!)
docker exec -it redis-aof cat /data/appendonly.aof
```

🔍 **You'll see something like / 你会看到类似：**
```
*2
$6
SELECT
$1
0
*3
$3
SET
...
```

**EN:** This is the **RESP protocol format** — each command is stored as `*arg_count\r\n$arg_length\r\narg_value\r\n`.

**CN:** 这就是 **Redis 协议格式 (RESP)**——每条命令按 `*参数个数\r\n$参数长度\r\n参数值\r\n` 存储。

### 3.4 AOF 重写（瘦身）/ AOF Rewrite

**EN:** The AOF file grows forever. If you `INCR counter` 1 million times, AOF stores 1 million commands.

**CN:** AOF 文件会越来越大。比如 `INCR counter` 执行了 100 万次，AOF 里就有 100 万条命令。

**Solution / 解决方案：`BGREWRITEAOF`** — rebuilds AOF from current in-memory data.

```bash
# Manually trigger rewrite
docker exec -it redis-aof redis-cli BGREWRITEAOF
```

**Rewrite effect / 重写效果：**
```
Before: INCR counter -> INCR counter -> INCR counter -> ...
                      |
                      v Rewrite
After:  SET counter 1000000       ← merged into one command
```

> **Auto-rewrite config / 自动重写配置：**
> ```conf
> # Rewrite when AOF grows 100% since last rewrite
> auto-aof-rewrite-percentage 100
> # Only rewrite when AOF is at least 64MB
> auto-aof-rewrite-min-size 64mb
> ```

### 3.5 AOF 优缺点 / Pros & Cons

| Pros / 优点 | Cons / 缺点 |
|:----|:----|
| ✅ Safer (at most 1s data loss with everysec) | ❌ Larger file than RDB |
| ✅ Human-readable text | ❌ Slower restart than RDB |
| ✅ Rewrite prevents unbounded growth | ❌ More disk I/O than RDB |

---

## ⚖️ 四、RDB vs AOF — 怎么选？ / Which One to Use?

### 4.1 对比表 / Comparison Table

| 特性 / Feature | RDB | AOF |
|:----|:---:|:---:|
| Content / 存储内容 | Data snapshot (binary) | Write commands (RESP) |
| File size / 文件大小 | Small | Large |
| Restore speed / 恢复速度 | ⚡ Fast | 🐢 Slow |
| Data safety / 数据安全 | Lose data since last snapshot | everysec: lose ≤1s data |
| Performance impact / 性能影响 | fork child process (copy-on-write) | Disk I/O (fsync frequency) |
| Human-readable / 人类可读 | ❌ Binary | ✅ Plain text |

### 4.2 生产推荐方案 / Production Recommendation

```conf
# Enable both (this is the default in Redis)
# RDB for backups, AOF for data recovery
save 3600 1          # RDB: at least 1 change per hour
appendonly yes       # Enable AOF
appendfsync everysec # Flush every second
```

> **EN:** Why both? Redis uses AOF for restart (more complete data), and RDB for daily backups.
>
> If your data isn't critical (pure cache), you can use only RDB or even neither.
>
> **CN:** 为什么两个都开？重启时 Redis 优先用 AOF 恢复（数据更完整），RDB 用来做日常备份。
>
> 如果你对数据安全性要求不高（比如纯缓存场景），可以只开 RDB 甚至什么都不开。

### 4.3 选择指南 / Decision Guide

| 场景 / Scenario | 推荐方案 / Recommendation |
|:----|:--------|
| Pure cache, data loss OK / 纯缓存可丢 | Neither (max performance) |
| Cache but no rebuild / 缓存不想重建 | RDB only |
| Important data / 数据重要 | RDB + AOF |
| Extreme data safety / 极端安全 | AOF `always` (rare, poor perf) |

---

## 🔄 五、主从复制 — 读写分离 / Master-Slave Replication

### 5.1 什么是主从复制？ / What is Replication?

**EN:** One **master** syncs data to N **replicas** (slaves).

**CN:** 一台 **master（主）** 把数据同步给 N 台 **replica（从）**。

```
┌─────────────┐
│   Master    │ ← Writes (SET/DEL/INCR...)
│  :6379      │
└─────┬───────┘
      │ Auto-sync
      ├──────────────┐
┌──────┴──────┐ ┌──────┴──────┐
│  Replica 1  │ │  Replica 2  │ ← Reads (GET/LRANGE...)
│  :6380      │ │  :6381      │
└─────────────┘ └─────────────┘
```

**Core rules / 核心规则：**
- **Master** can read and write
- **Replica** can only read (writes will error)
- Data syncs from master to replica automatically

### 5.2 为什么要主从复制？ / Why Replication?

| 目的 / Purpose | 说明 / Explanation |
|:----|:----|
| 读写分离 / Read-Write Separation | Master handles writes, replicas handle reads → higher throughput |
| 数据备份 / Data Backup | Disconnect a replica for backup without affecting master |
| 高可用基础 / HA Foundation | If master fails, a replica can take over (with Sentinel) |

### 5.3 Docker 动手实验 / Hands-on Demo

```bash
# 1. Start master (port 6379)
docker run -d --name redis-master \
  -p 6379:6379 \
  redis:7.4 redis-server --save "" --appendonly no

# 2. Start slave (port 6380), use --replicaof to specify master
docker run -d --name redis-slave \
  -p 6380:6379 \
  redis:7.4 redis-server --save "" --appendonly no --replicaof 127.0.0.1 6379

# 3. Check master status
docker exec -it redis-master redis-cli INFO replication
```

🔍 **Master output / 主节点输出：**
```
# Replication
role:master
connected_slaves:1
slave0:ip=127.0.0.1,port=6379,state=online,offset=14,lag=0
```

```bash
# 4. Check slave status
docker exec -it redis-slave redis-cli INFO replication
```

🔍 **Slave output / 从节点输出：**
```
# Replication
role:slave
master_host:127.0.0.1
master_port:6379
master_link_status:up
```

### 5.4 验证数据同步 / Verify Sync

```bash
# 1. Write to master
docker exec -it redis-master redis-cli SET mykey "hello from master"

# 2. Read from slave (data is synced!)
docker exec -it redis-slave redis-cli GET mykey
# → "hello from master"  ✅

# 3. Try writing to slave (will fail!)
docker exec -it redis-slave redis-cli SET anotherkey "nope"
# → (error) READONLY You can't write against a read only replica.
```

### 5.5 断开主从 / Detach Slave

```bash
# Make the slave independent (stop syncing)
docker exec -it redis-slave redis-cli REPLICAOF NO ONE
```

**EN:** After this, the slave becomes a master itself, but keeps existing data.

**CN:** 断开后从库变成主库，但已有的数据保留。

### 5.6 全量同步 vs 增量同步 / Full vs Incremental Sync

| 同步类型 / Type | 触发时机 / When | 行为 / Behavior |
|:--------|:--------|:----|
| **全量同步 / Full Sync** | First connection | Master generates RDB → sends to slave → buffers commands during transfer |
| **增量同步 / Incremental Sync** | Reconnect after disconnect | Only syncs missed commands via `PSYNC` |

> 🔍 **EN:** Full sync is expensive (RDB generation + network transfer). Keep slaves stable online.
>
> **CN:** 全量同步代价很大（生成 RDB + 网络传输），所以尽量让从库稳定在线。

### 5.7 常见配置 / Common Config

```conf
# Slave configuration
replicaof 127.0.0.1 6379  # Specify master address
replica-read-only yes      # Slave is read-only (default)
repl-backlog-size 1mb      # Replication buffer (for incremental sync)
```

---

## 🛡️ 六、Sentinel — 自动故障转移 / Automatic Failover

### 6.1 什么是 Sentinel？ / What is Sentinel?

**EN:** Sentinel is an independent process that **monitors** your Redis cluster and performs **automatic failover** when the master goes down.

**CN:** Sentinel（哨兵）是一个独立进程，负责**监控** Redis 主从集群，实现**自动故障转移**。

```
           ┌──────────┐
           │ Sentinel │ ← Monitors the cluster
           │ :26379   │
           └────┬─────┘
                │ Watch
    ┌───────────┼───────────┐
    │           │           │
┌───┴───┐  ┌───┴───┐  ┌───┴───┐
│Master │  │Slave 1│  │Slave 2│
│:6379  │  │:6380  │  │:6381  │
└───────┘  └───────┘  └───────┘
```

### 6.2 哨兵做了什么？ / What Does Sentinel Do?

| 功能 / Function | 说明 / Explanation |
|:----|:----|
| **监控 / Monitoring** | PINGs all nodes every 1 second |
| **通知 / Notification** | Alerts admin when a node goes down |
| **自动故障转移 / Auto Failover** | Master down → elect a new master from slaves |
| **配置提供 / Configuration** | Clients ask Sentinel for the current master address |

### 6.3 故障转移流程 / Failover Process

```
1. Sentinel detects master is unresponsive (subjective down)
2. Multiple Sentinels vote to confirm (objective down)
3. Elect a new master from slaves
4. Other slaves switch to replicate the new master
5. Old master auto-becomes slave when it recovers
```

```
Initial state / 初始状态：
  Master:6379 ← writes
  Slave:6380  ← reads
  Slave:6381  ← reads
        │
   Master:6379 CRASHES!
        ↓
  Sentinel auto-elects → Slave:6380 becomes NEW master
        ↓
After recovery / 恢复后：
  Master:6380 (was 6380) ← writes
  Slave:6381  ← reads
  Slave:6379 (old master, now a slave) ← reads
```

### 6.4 演示思路 / Quick Demo (Concept Only)

```bash
# Start 3 containers: 1 master + 2 slaves + 1 sentinel

# 1. Start master
docker run -d --name redis-master -p 6379:6379 redis:7.4

# 2. Start two slaves
docker run -d --name redis-slave1 -p 6380:6379 redis:7.4 redis-server --replicaof 172.17.0.2 6379
docker run -d --name redis-slave2 -p 6381:6379 redis:7.4 redis-server --replicaof 172.17.0.2 6379

# 3. Start sentinel (needs custom sentinel.conf)
# Skipping details — understand the concept, learn hands-on when needed
```

> **EN:** In production, deploy **3 Sentinels** (odd number, prevent split-brain). Sentinels monitor each other too.
>
> **CN:** 生产环境一般部署 **3 个 Sentinel**（奇数个，防止脑裂），Sentinel 之间也互相监控。

---

## ⚠️ 七、常见坑 & FAQ / Pitfalls & FAQ

### 7.1 BGSAVE 失败怎么办？ / BGSAVE Fails?

```bash
# Check if last BGSAVE succeeded
docker exec -it redis-rdb redis-cli INFO persistence
```

**EN:** If you see `rdb_last_bgsave_status:err`, check disk space and permissions.

**CN:** 如果看到 `rdb_last_bgsave_status:err`，检查磁盘空间和权限。

**Repair RDB file / 修复 RDB 文件：**
```bash
redis-check-rdb /data/dump.rdb
```

### 7.2 AOF 文件损坏 / AOF File Corruption

```bash
# Fix AOF file
redis-check-aof --fix /data/appendonly.aof
```

### 7.3 RDB 和 AOF 谁先加载？ / Which Loads First on Restart?

```
Redis startup order / Redis 启动顺序：
  1. Check if AOF exists → load AOF (more complete data)
  2. No AOF but RDB exists → load RDB
```

### 7.4 主从同步失败？ / Replication Not Working?

```bash
# Check sync status on slave
docker exec -it redis-slave redis-cli INFO replication
```

**Key fields / 关键字段：**
- `master_link_status:up` → OK
- `master_link_status:down` → check network/firewall

**Common causes / 常见原因：**
- Firewall blocking ports
- Master has `requirepass` but slave lacks `masterauth`
- `repl-id` mismatch (full sync needed)

### 7.5 为什么容器重启数据没了？ / Why Data Disappears After Restart?

**EN:** Your Docker container has no volume mount.

**CN:** 因为你没挂载持久化目录。

```bash
# ❌ Data lost when container is deleted
docker run -d --name redis-master redis:7.4

# ✅ Data survives container restart
docker run -d --name redis-master \
  -v redis-data:/data \
  redis:7.4
```

### 7.6 生产环境选什么？ / Production Decision Chart

```
Pure cache / 纯缓存场景 → No persistence / 什么都不开
Cache + OK to lose / 缓存可丢 → RDB only
Important data / 数据重要 → RDB + AOF everysec
Critical data / 敏感数据 → AOF always (rare / 极少用)
```

### 7.7 面试能用上吗？ / Interview Value?

> **Interviewer / 面试官："Redis 宕机了怎么办？"**
>
> **Your answer / 你的回答：**
>
> "Redis has two persistence methods: RDB (snapshot) and AOF (append-only). RDB is great for backups, AOF loses at most 1 second of data. In production I enable both. Plus master-slave replication for read-write separation, and Sentinel for automatic failover — if the master crashes, Sentinel elects a new master automatically, transparent to the application."
>
> "Redis 有 RDB 和 AOF 两种持久化方式。RDB 是定时快照，适合备份；AOF 是命令追加，最多丢 1 秒数据。生产环境我一般两个都开。另外用主从复制做读写分离，Sentinel 做自动故障转移——主库挂了哨兵会自动选一个新主库，业务无感。"

✅ **EN:** Shows production experience.

✅ **CN:** 面试官会觉得你有**生产环境经验**。

---

## 📖 总结 / Key Takeaways

```
DAY4 Core Topics / DAY4 核心知识点：
    ↓
  Persistence ──→ RDB: Snapshot ⚡ Fast recovery
  (Keep data)    │
                 └─→ AOF: Command log 🔒 Safer
    ↓
  Replication ──→ One master, multiple replicas
  (High avail.)  │
                 └─→ Read from replicas, write to master
    ↓
  Sentinel ────→ Auto-monitor + failover
  (Automation)  │
                └─→ Production essential
```

> **EN:** RDB + AOF — try it hands-on with Docker. Master-slave — start containers and see sync yourself. Sentinel — understand the concept, revisit when you need it.
>
> **CN:** 持久化（RDB + AOF）一定要亲手操作一遍，主从复制也建议自己起容器看效果。Sentinel 理解概念就行，用到时再回来查。

---

上一章 / Previous: [DAY3 — Expiry, Pub/Sub, Pipeline, Lua Scripting](../DAY3/README.md)

下一章 / Next: MySQL — Database Integration (wait until you learn MySQL/PostgreSQL)
