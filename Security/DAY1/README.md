# Security DAY1 — Web Security Basics 🛡️

> **日期：** 2026-06-15
> **核心主题：** SQL 注入防御 / 密码安全 / 日志规范

---

## 目录

- [实操一：SQL 注入攻防（01_sql_injection.py）](#实操一sql-注入攻防)
- [实操二：密码加密演进（02_password_hash.py）](#实操二密码加密演进)
- [实操三：日志规范 —— 在博客项目中落地](#实操三日志规范)
- [总结：DAY1 思维导图](#总结)

---

## 实操一：SQL 注入攻防

### 攻击原理

通过**拼接 SQL 字符串**，利用用户输入中的特殊字符改变 SQL 语义。

**经典注入语句：**

```sql
-- 正常登录
SELECT * FROM users WHERE username='admin' AND password='supersecret'

-- 注入后："admin' -- " 注释掉了密码检查
SELECT * FROM users WHERE username='admin' -- ' AND password='12344'
                           ^^^^^^^^^^^^^^^^
                           条件为真，绕过登录
```

**MySQL `--` 注释要点：**
- `-- ` 后面**必须跟空格**（或制表符/换行），否则不生效
- `admin' --`（无空格）→ 语法错误
- `admin' -- `（有空格）→ 成功绕过

### UNION SELECT 数据窃取

```sql
' UNION SELECT username, password FROM users -- '
```

`UNION` 将额外查询结果合并到正常结果中，攻击者可以**窃取任意表的数据**。

### DROP TABLE 删表

```sql
' ; DROP TABLE users; -- '
```

**PyMySQL 默认阻止多语句执行**（`multi=True` 才会执行），这是重要的安全防线。

### 防御方案

```python
# ❌ 不安全：字符串拼接
sql = f"SELECT * FROM users WHERE username='{username}'"

# ✅ 安全：参数化查询（占位符 %s）
sql = "SELECT * FROM users WHERE username = %s AND password = %s"
cursor.execute(sql, (username, password))
```

**占位符 `%s`** 告诉 MySQL：「这是数据，不是 SQL 指令」，用户输入中的 `'`、`--` 等字符自动被转义。

---

## 实操二：密码加密演进

### 技术演进路线

```
明文 ─→ SHA-256 ─→ SHA-256 + Salt ─→ bcrypt
                        ↑                ↑
                    防彩虹表        故意慢 + 自含盐
```

### 各方案对比

| 方案 | 速度 | 抗暴力破解 | 抗彩虹表 | 存储 |
|:----|:----:|:----------:|:--------:|:----|
| 明文 | 0ns | ❌ | ❌ | 直接存密码 |
| SHA-256 | ~1B hash/sec | ⚠️ 弱 | ❌ 相同密码输出相同 | 64 位 hex |
| bcrypt | ~10 hash/sec | ✅ 极强 | ✅ 自动加盐 | 60 位字符 |

### bcrypt 核心概念

**1. 自带盐（Salt）**
```python
salt = bcrypt.gensalt()       # 自动生成随机盐
hashed = bcrypt.hashpw(pwd.encode(), salt)
# 输出示例：$2b$12$LJ3m...（包含了版本 + 轮数 + salt + hash）
```

- 同一个密码每次加密结果不同
- 盐存储在 hash 字符串中，无需额外字段

**2. 故意慢**
- bcrypt 设计参数：~10 hash/sec
- SHA-256：~1,000,000,000 hash/sec
- 攻击者暴力破解成本增加 **1 亿倍**

**3. 验证方式**
```python
# hashpw 返回 bytes；checkpw 内部提取盐重新计算对比
bcrypt.checkpw(password.encode(), hashed)
```

### 字节 vs 字符串

| 操作 | 作用 |
|:----|:----|
| `str.encode()` | `"hello"` → `b"hello"` |
| `bytes.decode()` | `b"hello"` → `"hello"` |

- bcrypt API 要求 `bytes` 输入
- MySQL VARCHAR 存 `str`，所以 `.decode()` 后存储

### 博客项目中的改动

- **logup：** `bcrypt.hashpw(password.encode(), bcrypt.gensalt())` 存入 DB
- **login：** `bcrypt.checkpw(input.encode(), stored_hash)` 验证
- Redis 缓存中存的是 hash 而不是明文

---

## 实操三：日志规范

### 英语日志句式

| 动作 | 句式 | 示例 |
|:----|:----|:----|
| 尝试 | `{Action} attempt:{detail}` | `Login attempt:admin` |
| 成功 | `{Action} success:{detail}` | `Login success:admin (cache)` |
| 失败/拒绝 | `{Action} blocked:{detail}{reason}` | `Login blocked:user not found in DB` |
| 警告 | `{Action} failed:{detail}{reason}` | `Validation failed:invalid email format` |
| 缓存 | `Cache {action}:{detail}` | `Cache miss for admin,querying DB` |

### 四个关键打日志位置

1. **入口** — 函数开头记录尝试（`Login attempt:admin`）
2. **成功** — 正常结束（`Login success:admin from cache`）
3. **异常** — 捕获错误或拒绝（`Login blocked:wrong password for admin`）
4. **缓存操作** — 缓存命中/未命中（`Cache miss for admin,querying DB`）

### 日志级别选择

| 级别 | 何时用 |
|:----|:--------|
| `info` | 正常流程：尝试、成功、缓存 miss |
| `warning` | 可预期的异常：密码错误、用户名已存在 |
| `error` | 不可预期的异常：数据库连接失败 |

---

## 总结

```
DAY1 — Web Security Basics
  ├── SQL Injection
  │   ├── 原理：拼接字符串改变 SQL 语义
  │   ├── 危险：绕过登录 / 窃取数据 / 删表
  │   └── 防御：参数化查询（%s 占位符）
  ├── Password Security
  │   ├── bcrypt vs SHA-256：故意慢 + 自动加盐
  │   ├── hashpw(pwd, salt) 和 checkpw(input, hash)
  │   └── .encode() / .decode() 的 bytes ↔ str 转换
  └── Logging Standards
      ├── 英语句式：attempt / success / blocked 三段式
      ├── 四个位置：入口 / 成功 / 异常 / 缓存
      └── 日志级别：info / warning / error
```

> **明日预告：** DAY2 — 认证安全（JWT？Session？CSRF？）
