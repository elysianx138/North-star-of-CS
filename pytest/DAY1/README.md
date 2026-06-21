# DAY1 — pytest 基础：assert、测试发现、fixture

> **核心目标：** 理解 pytest 三件套——assert 自动判对错、test_ 规则找测试、fixture 抽离准备工作。
> **前置知识：** 基本的 Python 函数定义。

---

## 一、pytest 是什么？

> **自动化测试框架。** 你写测试代码，pytest 一键帮你跑，自动汇报哪些过了、哪些挂了。

---

## 二、assert — 自动判定，告别肉眼检查

### 本质

```python
# 没有 assert：每次改完代码手动 print，眼睛盯
result = some_function()
print(result)

# 有 assert：写一次检查规则，以后 pytest 自动判定
def test_some_function():
    result = some_function()
    assert result == "预期结果"  # ✅ 绿 = 符合预期，❌ 红 = 出岔了
```

### 效果

assert 后面跟一个表达式，**True 就过，False 就挂**：

```python
def test_math():
    assert 1 + 1 == 2          # True → PASSED

def test_string():
    assert "hello" in "hello world"  # True → PASSED

def test_will_fail():
    assert 2 * 2 == 5          # False → FAILED
```

### 什么时候该写 assert？

```
核心业务逻辑 + 容易踩坑的边界条件 = ✅ 值得测
通用工具函数 + 简单的一行代码   = ❌ 没必要测
你在项目里手动测试超过 3 次的操作 = ✅ 应该写成自动化测试
```

---

## 三、测试发现规则 — pytest 怎么找到你的测试

### 一条规则

> **递归扫描，抓到 `test_` 开头的函数/方法就跑，其余无视。**

```python
def test_normal():          # ✅ 抓到
    assert 1 == 1

def not_a_test():           # ❌ 无视
    assert 1 == 2

class TestGroup:            # 类名 Test 开头也会收集
    def test_in_class(self):    # ✅ 抓到
        assert "a" in "abc"

    def not_test_either(self):  # ❌ 无视
        assert False
```

### 为什么要有这个规则？

项目大了，测试文件里混着辅助函数：

```python
def setup_database():     # 辅助函数 — pytest 无视
def cleanup():            # 辅助函数 — pytest 无视
def helper_create_user(): # 辅助函数 — pytest 无视
def test_login():         # ✅ 真正的测试
def test_register():      # ✅ 真正的测试
```

**约定大于配置。** 你不用告诉 pytest 哪些是测试，它看名字就知道。

---

## 四、fixture — 抽离准备工作

### 问题场景

每个测试函数之前都要做同样的事：连数据库、创建测试数据、清理。

```python
def test_login():
    db = connect_db()        # 重复
    create_test_user(db)     # 重复
    result = login_api()
    assert result["ok"]

def test_register():
    db = connect_db()        # 重复
    create_test_user(db)     # 重复
    result = register_api()
    assert result["ok"]
```

### fixture 解决

```python
import pytest

@pytest.fixture
def db():
    conn = connect_mysql()
    create_test_user(conn)
    yield conn               # 把控制权交给测试函数
    conn.close()             # 测试跑完后自动清理

def test_login(db):          # pytest 自动注入 db
    result = login_api(db, password="correct")
    assert result["token"]

def test_register(db):       # 不用再写一遍连库
    result = register_api(db, username="new_user")
    assert result["user_id"]
```

### fixture 三个好处

| 问题 | 解决 |
|:----|:-----|
| 重复代码 | 准备工作写一次，所有测试共用 |
| 清理遗漏 | `yield` 后面的代码自动跑，不会忘记关连接 |
| 改配置 | 只需要改 fixture 一处，不用改 100 个测试 |

---

## 五、DAY1 核心收获

1. ✅ **assert** — 自动检查预期结果，取代 print 肉眼盯
2. ✅ **test_ 发现规则** — pytest 只跑 `test_` 开头的函数
3. ✅ **fixture** — `@pytest.fixture` 抽离准备工作，`yield` 前后分别是准备和清理

### 相关实验文件

- [test_assert.py](test_assert.py) — assert 基础用法
- [test_discovery.py](test_discovery.py) — pytest 发现规则验证
- [test_fixture.py](test_fixture.py) — fixture 注入和生命周期

---

## 下一步

**DAY2 → Mock + TestClient：** 在不启动项目的情况下测试 API 接口，用 mock 隔离数据库和 Redis。
