# Security DAY5 — 企业级安全防护 🛡️

---

## 目录

- [Part 1：CSP 内容安全策略](#part-1csp-内容安全策略)
- [Part 2：输入验证与密码策略](#part-2输入验证与密码策略)
- [Part 3：Redis 限流](#part-3redis-限流)
- [Part 4：反爬虫与攻击成本](#part-4反爬虫与攻击成本)
- [Part 5：安全全景清单](#part-5安全全景清单)

---

## Part 1：CSP 内容安全策略

### X-XSS-Protection 已死

Chrome 已经移除了 `X-XSS-Protection` 的支持，现代浏览器统一使用 **CSP（Content-Security-Policy）** 替代。

### CSP 是什么

告诉浏览器**只能加载来自你自己域名的资源**，拦截一切外部注入。

```python
# 最严格的 CSP
response.headers["Content-Security-Policy"] = "default-src 'self'"
```

| 指令 | 意思 | 保护范围 |
|:----|:-----|:--------|
| `default-src 'self'` | 所有资源只从本站加载 | 脚本/样式/图片/字体等全部生效 |
| `script-src 'self'` | 只允许本站的 JS | 防 XSS 注入 `<script>` |
| `img-src *` | 图片可以从任何地方加载 | 常见放宽规则 |

### 你的改动

`MySQL/DAY3/app.py` 中替换安全头：

```python
# ❌ 旧的（已废弃）
response.headers["X-XSS-Protection"] = "1; mode=block"

# ✅ 新的（现代浏览器）
response.headers["Content-Security-Policy"] = "default-src 'self'"
```

> **注意：** 头字段名必须是 `Content-Security-Policy`，用下划线 `Content_Security-Policy` 不会生效。

---

## Part 2：输入验证与密码策略

### 只靠前端验证不够

```
浏览器提交的请求可以随意伪造：
  <script>fetch('/login', {body: JSON.stringify({password: "123"})})</script>

后端不验证 → 弱密码直接入库 ❌
```

### Pydantic Field 验证（后端硬校验）

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    userpassword: str = Field(
        min_length=8,
        pattern=r"^(?=.*[A-Za-z])(?=.*\d).+$"   # 必须含字母 + 数字
    )
    email: str = Field(
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"  # 合法邮箱格式
    )
```

| 规则 | 防什么 | 说明 |
|:----|:------|:-----|
| `min_length=8` | 弱密码 | 至少 8 位 |
| `pattern=字母+数字` | 无复杂度密码 | 必须混合 |
| `pattern=邮箱格式` | 非法输入 | 防止垃圾数据入库 |

> 正则不用背，**会搜 + 会用 Field 就够了**。

---

## Part 3：Redis 限流

### 核心原理

两个 Redis 命令搞定：

```
INCR rate:login:IP    → 每次请求 +1
EXPIRE rate:login:IP 60 → 60 秒后自动清零
```

```
第 1 次：INCR → 1（< 5，正常放行）
第 2 次：INCR → 2（< 5，正常放行）
第 3 次：INCR → 3（< 5，正常放行）
第 4 次：INCR → 4（< 5，正常放行）
第 5 次：INCR → 5（< 5，正常放行）
第 6 次：INCR → 6（> 5 → 返回 429 Too Many Requests）
```

### 三层限流体系

| 层 | 限流对象 | 基于 | 位置 | 参数 |
|:--|:--------|:----|:----|:----|
| 第一层 | 登录 | IP | `POST /login` | 5 次/分钟 |
| 第二层 | 注册 | IP | `POST /logup` | 3 次/小时 |
| 第三层 | 写操作 | user_id | `POST /articles` | 10 次/小时 |

### 通用函数

```python
# IP 限流（login / logup）
def rate_limit_login(request, key, window, max_count, detail):
    client_ip = request.client.host
    count = redis.incr(f"{key}:{client_ip}")
    if count == 1:
        redis.expire(f"{key}:{client_ip}", window)
    if count > max_count:
        raise HTTPException(status_code=429, detail=detail)

# 用户限流（发文章 / 点赞）
def rate_limit_user(user_id, key, window, max_count, detail):
    count = redis.incr(f"{key}:{user_id}")
    if count == 1:
        redis.expire(f"{key}:{user_id}", window)
    if count > max_count:
        raise HTTPException(status_code=429, detail=detail)
```

---

## Part 4：反爬虫与攻击成本

### 为什么简单的反爬手段没用

| 手段 | 问题 | 结论 |
|:----|:----|:----|
| User-Agent 检查 | `requests.get(url, headers=随便填)` | ❌ 形同虚设 |
| Referer 检查 | 伪造请求头轻松绕过 | ❌ 形同虚设 |

### 真正有用的是「提高攻击成本」

```
限流 3 次/小时   → 攻击者注册 1000 个号换 IP
CAPTCHA         → 攻击者花钱接打码平台
邮箱验证        → 攻击者买临时邮箱
信誉系统        → 攻击者养号花时间

每一层都在提高成本。
当成本 > 收益时，攻击者就去找下一个目标。
```

### 你现在已经做了的

```
三层限流：✅ 免费且有效
邮箱验证：⏳ 上线前必须加
CAPTCHA： ⏳ 有需要再加
```

> 参考 GitHub：API 限流 5000 次/小时（认证），照样有人爬。**目标是管理攻击，不是完全阻止。**

---

## Part 5：安全全景清单

### 你学过的全部防护

| 攻击类型 | 防护手段 | 对应 DAY | 关键代码 |
|:--------|:--------|:--------:|:---------|
| SQL 注入 | 参数化查询 `%s` | DAY1 | `cursor.execute(sql, params)` |
| 密码泄露 | bcrypt 哈希 | DAY1 | `bcrypt.hashpw()` / `bcrypt.checkpw()` |
| 暴力破解 | Redis INCR + EXPIRE 限流 | DAY5 | `rate_limit_login()` / `rate_limit_user()` |
| XSS | CSP `default-src 'self'` | DAY5 | `Content-Security-Policy` 头 |
| MIME 嗅探 | `X-Content-Type-Options: nosniff` | DAY2 | `response.headers["X-Content-Type-Options"]` |
| 点击劫持 | `X-Frame-Options: DENY` | DAY2 | `response.headers["X-Frame-Options"]` |
| CSRF | localStorage + Authorization header | DAY2 | 浏览器不自动带 Header |
| 中间人攻击 | HTTPS + TLS | DAY4 | OpenSSL 自签证书 |
| CORS 跨域 | CORSMiddleware | DAY4 | `allow_origins=["*"]` |
| JWT 伪造 | HMAC-SHA256 签名验证 | DAY2 | 密钥不一致→拒绝 |
| 批量注册 | Redis 注册限流 | DAY5 | 同 IP 3 次/小时 |
| 垃圾内容 | Redis 用户操作限流 | DAY5 | 同 user_id 10 次/小时 |

### 安全架构总览

```
浏览器 → HTTPS → 限流 → 应用层 → 服务层
                           │
      ┌────── JWT 认证 ────┤
      │  签名验证 + 过期检查 │
      ├────── CSP / 安全头 ─┤
      │  浏览器级别的防御   │
      ├────── 参数验证 ─────┤
      │  Pydantic Field    │
      ├────── 限流 ────────┤
      │  IP + user_id      │
      ├────── bcrypt 哈希 ─┤
      │  密码不存明文       │
      └─────────────────────┘
                           │
                    MySQL + Redis
```

---

## 基础安全总结

```
SECURITY 全 5 天：
  ├── DAY1：SQL 注入防御 + bcrypt 密码哈希 + 日志规范
  ├── DAY2：JWT 手写实现 + 集成项目 + 安全响应头 + CSRF 防护
  ├── DAY3：GitHub OAuth 第三方登录
  ├── DAY4：HTTPS/TLS 加密 + OpenSSL 自签证书 + CORS 跨域
  └── DAY5：CSP / 密码策略 / Redis 三层限流 / 安全全景清单

你已经从一个"能跑就行"的开发者，
变成了一个"上线前知道要防什么"的开发者。🛡️
```

> **基础安全完结 🎉 → 下一站：pytest 测试**
