# DAY1: SQL 基础速通 / SQL Basics Express

> **适合人群 / For You:**
> 有 SQLite 使用经验（Flask 项目），想快速切换到 MySQL。
>
> **学习方式 / Learning Approach:**
> Docker MySQL 命令行操作，对比 SQLite 理解差异。**中英双语 / Bilingual**
>
> **目标 / Goal:**
> 一天之内跑完 SQL 基础、JOIN、索引、事务，快速进入 Python+MySQL 整合。

---

## 📋 目录 / Contents

1. [环境搭建 / Setup](#-一环境搭建--setup)
2. [数据库与表 / Database & Table](#-二数据库与表--database--table)
3. [CRUD 操作 / Basic CRUD](#-三crud-操作--basic-crud)
4. [多表查询 JOIN / JOIN Queries](#-四多表查询-join--join-queries)
5. [索引 / Index](#-五索引--index)
6. [事务与 ACID / Transaction & ACID](#-六事务与-acid--transaction--acid)
7. [MySQL 特有函数 / MySQL Functions](#-七mysql-特有函数--mysql-functions)
8. [删表删库 / DROP & TRUNCATE](#-八删表删库--drop--truncate)

---

## 🔍 一、环境搭建 / Setup

### Docker MySQL

**EN:** Pull and start MySQL 8.0 with Docker.

**CN:** 用 Docker 拉取并启动 MySQL 8.0。

```bash
docker run -d --name mysql-local -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  mysql:8.0
```

**EN:** Connect to the MySQL server inside the container.

**CN:** 连接容器内的 MySQL。

```bash
docker exec -it mysql-local mysql -uroot -proot123
```

### 数据持久化 / Data Persistence

**EN:** By default, MySQL stores data inside the container at `/var/lib/mysql`. If you delete the container (`docker rm`), the data is gone. Mount a volume to persist data.

**CN:** 默认数据在容器内的 `/var/lib/mysql`，删容器数据就丢了。挂载数据卷才能持久化。

```bash
docker run -d --name mysql-local -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -v mysql-data:/var/lib/mysql \
  mysql:8.0
```

---

## 🏗️ 二、数据库与表 / Database & Table

### 创建数据库 / Create Database

```sql
CREATE DATABASE blog;
SHOW DATABASES;     -- 注意带 S，SHOW DATABASE 会报错
USE blog;
```

### MySQL vs SQLite 差异 / MySQL vs SQLite Differences

| 操作 / Operation | MySQL | SQLite |
|:---|:---|:---|
| 看表结构 / Describe table | `DESC articles;` | `.schema articles` |
| 看建表语句 / Show CREATE | `SHOW CREATE TABLE articles;` | 无 / None |
| 自增语法 / Auto increment | `AUTO_INCREMENT` | `AUTOINCREMENT` |

### 建表 / Create Table

**EN:** Create an `articles` table with id, title, content, and created_at.

**CN:** 创建 articles 表，包含 id、标题、内容、创建时间。

```sql
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### DESC 解读 / DESC Output Explained

```
+------------+--------------+------+-----+-------------------+-------------------+
| Field      | Type         | Null | Key | Default           | Extra             |
+------------+--------------+------+-----+-------------------+-------------------+
| id         | int          | NO   | PRI | NULL              | auto_increment    |
| title      | varchar(200) | NO   |     | NULL              |                   |
| content    | text         | YES  |     | NULL              |                   |
| created_at | datetime     | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+------------+--------------+------+-----+-------------------+-------------------+
```

| 列 / Column | 含义 / Meaning |
|:---|:---|
| **Field** | 字段名 / Column name |
| **Type** | 数据类型 / Data type（INT, VARCHAR, TEXT, DATETIME）|
| **Null** | 是否可为空 / Nullable（NO=必填, YES=可选）|
| **Key** | 索引类型 / Key type（PRI=主键）|
| **Default** | 默认值 / Default value |
| **Extra** | 额外信息 / Extra（auto_increment=自增）|

### SHOW CREATE TABLE 解读 / CREATE TABLE Output Explained

**EN:** Shows the full CREATE TABLE statement MySQL generated — useful for understanding ENGINE, CHARSET, etc.

**CN:** 显示 MySQL 生成的完整建表语句，可以看 ENGINE、CHARSET 等设置。

```
ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

| 字段 / Field | 含义 / Meaning |
|:---|:---|
| `ENGINE=InnoDB` | 存储引擎，支持事务/行级锁 / Supports transactions & row-level locks |
| `AUTO_INCREMENT=4` | 下一条数据 id=4 / Next row will have id=4 |
| `CHARSET=utf8mb4` | 字符集，支持 emoji / Supports emoji |
| `COLLATE=..._ai_ci` | 排序规则，不区分大小写 / Case-insensitive |

---

## ✍️ 三、CRUD 操作 / Basic CRUD

### INSERT

**EN:** Insert multiple rows at once.

**CN:** 一次插入多行。

```sql
INSERT INTO articles (title, content) VALUES
    ('First Article', 'Hello MySQL!'),
    ('Second Article', 'Learning SQL is fun'),
    ('Redis vs MySQL', 'They are different tools');
```

### SELECT

**EN:** Query with conditions, sorting, and pagination.

**CN:** 带条件、排序、分页的查询。

```sql
-- 全部查询 / All rows
SELECT * FROM articles;

-- 条件筛选 / WHERE condition
SELECT * FROM articles WHERE id > 1;

-- 排序 / Sorting（DESC=降序, ASC=升序）
SELECT * FROM articles ORDER BY created_at DESC;

-- 限制条数 / Limit rows
SELECT * FROM articles LIMIT 2;

-- 翻页 / Pagination
SELECT * FROM articles LIMIT 2 OFFSET 1;
SELECT * FROM articles LIMIT 1, 2;   -- 简写：偏移量, 条数 / shorthand
```

> **关于 LIMIT 简写 / About LIMIT shorthand:**
> `LIMIT 2, 3` = 跳过前 2 行，取 3 行 / Skip 2 rows, take 3 rows

### LIKE 模糊搜索 / Fuzzy Search

**EN:** `%` on the right can use index; `%` on the left causes full scan.

**CN:** `%` 在右边可能走索引，在左边一定全表扫。

```sql
SELECT * FROM articles WHERE title LIKE '%Redis%';   -- ❌ 不走索引
SELECT * FROM articles WHERE title LIKE 'First%';    -- ✅ 可能走索引
SELECT * FROM articles WHERE title LIKE '%First';    -- ❌ 不走索引
```

### UPDATE

**EN:** Always include WHERE, or every row gets updated!

**CN:** **一定带 WHERE！** 否则全表都会被改。

```sql
UPDATE articles SET content = 'Updated content!' WHERE id = 1;

-- 多列一起改 / Update multiple columns
UPDATE articles SET title = '新标题', content = '新内容' WHERE id = 1;
```

> **`SET` 的含义 / What SET does:** `SET 列名1 = 新值1, 列名2 = 新值2` — 指定要改的列和新值。

### DELETE

**EN:** Same warning — always use WHERE.

**CN:** 同样——**不带 WHERE 就是全删**。

```sql
DELETE FROM articles WHERE id = 3;
```

---

## 🔗 四、多表查询 JOIN / JOIN Queries

### 建作者表 / Create Authors Table

**EN:** Create an authors table and link it to articles.

**CN:** 创建作者表，关联到文章。

```sql
CREATE TABLE authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100)
);

INSERT INTO authors (name, email) VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com'),
    ('Charlie', 'charlie@example.com');

-- 添加作者关联列 / Add author FK column
ALTER TABLE articles ADD COLUMN author_id INT;

UPDATE articles SET author_id = 1 WHERE id = 1;
UPDATE articles SET author_id = 2 WHERE id = 2;
UPDATE articles SET author_id = 1 WHERE id = 3;
```

### INNER JOIN

**EN:** Only returns rows where both tables have a match.

**CN:** 只返回两表都能匹配上的行。

```sql
SELECT articles.title, authors.name, authors.email
FROM articles
INNER JOIN authors ON articles.author_id = authors.id;
```

```
+----------------+-------+-------------------+
| title          | name  | email             |
+----------------+-------+-------------------+
| First Article  | Alice | alice@example.com |
| Second Article | Bob   | bob@example.com   |
| Redis vs MySQL | Alice | alice@example.com |
+----------------+-------+-------------------+
```

**EN:** Charlie doesn't appear — he has no articles, so INNER JOIN excludes him.

**CN:** Charlie 没出现——他没写文章，INNER JOIN 不包含他。

### LEFT JOIN

**EN:** Keeps ALL rows from the left table (the one after FROM). If no match in the right table, fills with NULL.

**CN:** 左表（FROM 后面的表）**全部保留**，右表没有匹配就填 NULL。

```sql
SELECT articles.title, authors.name
FROM articles
LEFT JOIN authors ON articles.author_id = authors.id;
```

### JOIN 对比 / JOIN Comparison

| JOIN 类型 / Type | 左表 / Left Table | 右表 / Right Table |
|:---|:---:|:---:|
| `INNER JOIN` | 有匹配才出 / Matched only | 有匹配才出 / Matched only |
| `LEFT JOIN` | **全出** / **All kept** | 有匹配才出 / Matched only |
| `RIGHT JOIN` | 有匹配才出 / Matched only | **全出** / **All kept** |

> **常见错误 / Common mistake:**
> `ON articles.id = authors.id` ❌ — 这是用文章编号对作者编号，逻辑错误
> `ON articles.author_id = authors.id` ✅ — 这是用"谁写的"去对"作者是谁"

---

## 📊 五、索引 / Index

### 什么是索引 / What is an Index?

**EN:** An index is like a book's table of contents. Without it, MySQL scans every row (full table scan). With it, MySQL jumps directly to the right location.

**CN:** 索引就像书的目录。没索引就逐行扫描（全表扫描），有索引直接跳到目标位置。

**EN:** MySQL uses **B+ Tree** for indexes:
- **Non-leaf nodes**: store only routing info (index value + pointer)
- **Leaf nodes**: store actual row data
- 3-4 levels can handle millions of rows → only a few disk IOs per query

**CN:** MySQL 用 **B+ 树** 实现索引：
- **非叶子节点**：只存"路标"（索引值 + 指针），不存真实数据
- **叶子节点**：存完整行数据
- 3-4 层就能覆盖百万级数据，每次查询只需要几次磁盘 IO

### 基本操作 / Basic Operations

```sql
-- 创建索引 / Create index
CREATE INDEX idx_title ON articles(title);

-- 查看索引 / Show indexes
SHOW INDEX FROM articles;

-- 删除索引 / Drop index
DROP INDEX idx_title ON articles;

-- 查看查询计划 / Check query plan
EXPLAIN SELECT * FROM articles WHERE title = 'First Article';
```

### EXPLAIN type 含义 / EXPLAIN type Meanings

| type | 含义 / Meaning |
|:---:|:---|
| `const` | 主键/唯一索引，最多1行 / Primary key, at most 1 row |
| `ref` | 普通索引匹配 / Non-unique index match |
| `range` | 范围查询 / Range scan（`>`, `<`, `BETWEEN`, `LIKE 'xx%'`）|
| `ALL` | **全表扫描，没走索引** / **Full table scan** ❌ |

### 三种索引 / Three Types of Indexes

```sql
-- 普通索引 / Normal index（允许重复 / allows duplicates）
CREATE INDEX idx_name ON table(column);

-- 唯一索引 / Unique index（不允许重复 / no duplicates）
CREATE UNIQUE INDEX idx_email ON authors(email);

-- 复合索引 / Composite index（多列组合 / multiple columns）
CREATE INDEX idx_a_b_c ON table(a, b, c);
```

### ⭐ 最左前缀原则 / Leftmost Prefix Rule

**EN:** A composite index `(a, b, c)` is sorted by `a → b → c`. You must start from the leftmost column for the index to work.

**CN:** 复合索引 `(a, b, c)` 按 `a → b → c` 排序。查询必须从最左列开始，索引才生效。

**EN:** Think of a phonebook sorted by **last name → first name**. You can't skip the last name and look up by first name only.

**CN:** 就像电话本按**姓→名**排序，你跳过姓只查名，翻不了目录。

| 查询 / Query | 走索引? / Uses index? |
|:---|:---:|
| `WHERE a = 1` | ✅ 全走 / Full |
| `WHERE a = 1 AND b = 2` | ✅ 全走 / Full |
| `WHERE a = 1 AND b = 2 AND c = 3` | ✅ 全走 / Full |
| `WHERE a = 1 AND c = 3` | ✅ a 走，c 不走（跳过了 b）/ a uses index, c doesn't |
| `WHERE b = 2` | ❌ 不走索引 / Full scan |

### 索引优缺点 / Pros & Cons

| ✅ 优点 / Pros | ❌ 缺点 / Cons |
|:---|:---|
| 查询加速（百万行 3-4 次 IO）/ Fast queries | 占磁盘空间 / Disk space |
| 避免排序（ORDER BY 走索引）/ Avoid sorting | 写入变慢（要同步更新索引）/ Slower writes |

---

## 🔒 六、事务与 ACID / Transaction & ACID

### 什么是事务 / What is a Transaction?

**EN:** Bundles multiple SQL operations into one unit — **either all succeed, or all roll back**.

**CN:** 把多个 SQL 操作捆绑成一个整体——**要么全部成功，要么全部回滚**。

```sql
START TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

COMMIT;    -- ✅ 全部生效 / All changes committed
-- ROLLBACK;  -- ❌ 全部撤销 / All changes undone
```

**EN:** Like Git — `COMMIT` is like `git commit`, `ROLLBACK` is like `git reset --hard`. Before COMMIT, other sessions can't see your changes.

**CN:** 和 Git 一样——`COMMIT` 相当于 `git commit`，`ROLLBACK` 相当于 `git reset --hard`。提交之前其他连接看不到你的改动。

### ACID（面试必考 / Must-know for Interviews）

| 特性 / Property | 含义 / Meaning | 一句话 / In One Word |
|:---|:---|:---|
| **A**tomicity | 要么全做，要么全不做 / All or nothing | 做绝 or 不做 |
| **C**onsistency | 数据始终符合规则 / Data always follows rules | 不违反约束 |
| **I**solation | 并发的沙箱互不干扰 / Concurrent transactions don't interfere | 提交前别人看不见 |
| **D**urability | COMMIT 后数据不丢 / Data survives crashes | 写入磁盘了 |

### ACID 实验 / ACID Demo

**EN:** Delete a row, see it disappear, then ROLLBACK and watch it come back.

**CN:** 删一行数据，看它消失，ROLLBACK 后再看它回来。

```sql
START TRANSACTION;
DELETE FROM articles WHERE id = 4;
SELECT * FROM articles;   -- id=4 消失了 / id=4 is gone
ROLLBACK;
SELECT * FROM articles;   -- id=4 回来了！/ id=4 is back!
```

### 事务解决什么问题 / What Problems Does Transaction Solve?

**EN:** When multiple operations depend on each other — they must all succeed or all fail together.

**CN:** 多个操作之间有**牵连关系**时——必须一起成功或一起失败。

| 场景 / Scenario | 涉及操作 / Operations |
|:---|:---|
| 转账 / Transfer | 扣钱 + 加钱 / Debit + Credit |
| 发文章 / Publish article | INSERT 文章 + UPDATE 作者计数 / INSERT article + UPDATE author count |
| 下单 / Place order | INSERT 订单 + UPDATE 库存 / INSERT order + UPDATE stock |
| 注册 / Sign up | INSERT 用户 + INSERT 配置 / INSERT user + INSERT settings |

---

## 🛠️ 七、MySQL 特有函数 / MySQL Functions

**EN:** Functions that work differently from SQLite, or are MySQL-only.

**CN:** 和 SQLite 不同，或者 MySQL 独有的函数。

```sql
-- 日期时间 / Date & Time
SELECT NOW();                          -- 当前时间 2026-06-07 08:30:00
SELECT CURDATE();                      -- 当前日期 2026-06-07
SELECT DATEDIFF(NOW(), created_at)     -- 相差天数 / Days difference
FROM articles;

-- 字符串拼接 / String concatenation
-- SQLite: 'Hello' || ' ' || 'World'
-- MySQL:
SELECT CONCAT('Hello', ' ', 'World');

-- 多行拼成一行 / Aggregate into one string
SELECT GROUP_CONCAT(title) FROM articles;
-- 结果: "First Article, Second Article, Redis vs MySQL"

-- 空值处理 / Null handling
-- IFNULL 只处理"行存在但列为 NULL"，不处理"行不存在"
-- IFNULL handles NULL in a column, NOT a missing row
SELECT IFNULL(content, '暂无内容') FROM articles WHERE id = 1;

-- 行不存在需要子查询 / For missing rows, use a subquery:
SELECT IFNULL(
    (SELECT content FROM articles WHERE id = 999),
    'NOT FOUND'
);
```

---

## ❌ 八、删表删库 / DROP & TRUNCATE

**EN:** These operations are irreversible — MySQL won't ask "are you sure?".

**CN:** 这些操作**不可逆**——MySQL 不会问你"确定吗？"。

```sql
DROP TABLE authors;             -- 删表 / Delete table
DROP TABLE authors, articles;   -- 一次删多张 / Drop multiple
TRUNCATE TABLE articles;        -- 清空数据，保留结构 / Clear data, keep table
DROP DATABASE blog;             -- 删库 / Delete database
```

### 防误删措施 / Safety Measures

**EN:** In production, you won't have DROP permissions. Here's how to stay safe:

**CN:** 生产环境你拿不到 DROP 权限。以下是日常防误删手段：

| 措施 / Practice | 做法 / How |
|:---|:---|
| 权限控制 / Access control | 生产环境不给 DROP 权限 / No DROP in production |
| 先备份 / Backup first | `CREATE TABLE bak AS SELECT * FROM target;` |
| 事务包裹 / Wrap in transaction | 先 `START TRANSACTION`，确认后再 `COMMIT` |
| 安全模式 / Safe mode | `SET sql_safe_updates = 1;`（DELETE/UPDATE 不带 WHERE 报错）|

---

## 📝 总结 / Summary

| 内容 / Topic | 掌握程度 / Level |
|:---|:---:|
| Docker MySQL 搭建 / Docker MySQL Setup | ✅ 熟练 / Proficient |
| 建库建表 DESC / SHOW CREATE TABLE | ✅ 对比 SQLite / Compared with SQLite |
| CRUD（SELECT/INSERT/UPDATE/DELETE） | ✅ 语法一致 / Same as SQLite |
| JOIN（INNER / LEFT） | ✅ 多表查询 / Multi-table queries |
| 索引 + 最左前缀 / Index + Leftmost Prefix | ✅ 理解原理 / Understand the concept |
| 事务 + ACID / Transaction + ACID | ✅ 理解 / Understand |
| MySQL 特有函数 / MySQL Functions | ✅ 有印象 / Have an impression |

> **下一步 / Next Up:** DAY2 — Python + MySQL（PyMySQL / mysql-connector-python）
