"""
DAY4 实操二：索引对比 / Index Performance Comparison

对比：
  - 无索引：全表扫描（10 万行逐行翻）
  - 有索引：直接定位（B+ 树查找）

用法：
  python 02_index_explain.py

"""

import pymysql
import os
import time
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root123"),
    "database": "practice_db",
}


def get_conn():
    return pymysql.connect(**DB_CONFIG, autocommit=True, cursorclass=pymysql.cursors.DictCursor)


def setup(conn):
    """建表 + 插入 10 万行数据"""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS perf_test")
        cur.execute("""
            CREATE TABLE perf_test (
                id INT AUTO_INCREMENT PRIMARY KEY,
                value1 VARCHAR(100),
                value2 INT
            )
        """)

    print("⏳ 正在插入 10 万条数据...")

    # 批量插入（5000 条一次提交，比逐条快得多）
    batch_size = 5000
    with conn.cursor() as cur:
        for batch_start in range(1, 100001, batch_size):
            batch_end = min(batch_start + batch_size, 100001)
            values = []
            for i in range(batch_start, batch_end):
                values.append(f"('data_{i}', {i})")
            sql = f"INSERT INTO perf_test (value1, value2) VALUES {','.join(values)}"
            cur.execute(sql)

    print(f"✅  插入完成，共查询行数确认：")
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM perf_test")
        print(f"    perf_test 表共 {cur.fetchone()['cnt']} 行")
    print()


def query_without_index(conn):
    """无索引查询"""
    target = 88888
    print("🔍 无索引查询：")

    # EXPLAIN 看执行计划
    with conn.cursor() as cur:
        cur.execute("EXPLAIN SELECT * FROM perf_test WHERE value2 = %s", (target,))
        plan = cur.fetchone()
        print(f"    type:  {plan['type']}")
        print(f"    rows:  {plan['rows']}")
        print(f"    Extra: {plan['Extra']}")
        print("   👆 type=ALL 表示全表扫描！")

    # 实际计时
    start = time.time()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM perf_test WHERE value2 = %s", (target,))
        row = cur.fetchone()
    elapsed = time.time() - start
    print(f"    耗时: {elapsed:.4f} 秒")
    print(f"    结果: id={row['id']}, value1={row['value1']}, value2={row['value2']}")
    print()

    return elapsed


def add_index(conn):
    """加索引"""
    print("⏳ 正在创建索引...")
    start = time.time()
    with conn.cursor() as cur:
        cur.execute("CREATE INDEX idx_value2 ON perf_test(value2)")
    elapsed = time.time() - start
    print(f"✅  索引创建完成（耗时 {elapsed:.2f} 秒）")
    print()


def query_with_index(conn):
    """有索引查询"""
    target = 88888
    print("🔍 有索引查询：")

    with conn.cursor() as cur:
        cur.execute("EXPLAIN SELECT * FROM perf_test WHERE value2 = %s", (target,))
        plan = cur.fetchone()
        print(f"    type:  {plan['type']}")
        print(f"    rows:  {plan['rows']}")
        print(f"    Extra: {plan['Extra']}")
        print("   👆 type=ref 表示走了索引！")

    start = time.time()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM perf_test WHERE value2 = %s", (target,))
        row = cur.fetchone()
    elapsed = time.time() - start
    print(f"    耗时: {elapsed:.4f} 秒")
    print(f"    结果: id={row['id']}, value1={row['value1']}, value2={row['value2']}")
    print()

    return elapsed


def demo_index_failure(conn):
    """演示索引失效场景"""
    print("=" * 50)
    print("附：索引失效场景")
    print("=" * 50)

    # 1. 没索引的列
    with conn.cursor() as cur:
        cur.execute("EXPLAIN SELECT * FROM perf_test WHERE value1 = 'data_88888'")
        plan = cur.fetchone()
        print(f"1. 查未索引列 (value1)：type={plan['type']}, rows={plan['rows']}")
        print("   👆 type=ALL，没索引当然全表扫")

    # 2. LIKE 以 % 开头
    with conn.cursor() as cur:
        cur.execute("EXPLAIN SELECT * FROM perf_test WHERE value2 LIKE '%8888'")
        plan = cur.fetchone()
        print(f"2. LIKE '%8888'：type={plan['type']}, rows={plan['rows']}")
        print("   👆 以 % 开头，索引失效")

    # 3. 索引列上用了函数
    with conn.cursor() as cur:
        cur.execute("EXPLAIN SELECT * FROM perf_test WHERE value2 + 1 = 88889")
        plan = cur.fetchone()
        print(f"3. 函数运算 (value2+1)：type={plan['type']}, rows={plan['rows']}")
        print("   👆 索引列上做运算，索引失效")

    print()


if __name__ == "__main__":
    conn = get_conn()

    setup(conn)

    t1 = query_without_index(conn)

    add_index(conn)

    t2 = query_with_index(conn)

    print("=" * 50)
    print("📊 对比总结")
    print("=" * 50)
    print(f"   无索引: {t1:.4f} 秒  (全表扫描 10 万行)")
    print(f"   有索引: {t2:.4f} 秒  (B+ 树直接定位)")
    if t1 > 0:
        print(f"   差距:   约 {t1/t2:.0f} 倍")
    print()

    demo_index_failure(conn)

    conn.close()
