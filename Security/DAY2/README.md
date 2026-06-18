# Security DAY2 — 认证安全：JWT 实战 🛡️

> **日期：** 2026-06-16
> **核心主题：** JWT 原理与实现 / CSRF 防护 / 安全响应头

---

## 目录

- [实操一：手写 JWT（01_jwt_demo.py）](#实操一手写-jwt)
- [实操二：JWT 集成博客项目](#实操二jwt-集成博客项目)
- [实操三：CSRF 防护 + 安全响应头](#实操三csrf-防护--安全响应头)
- [总结：DAY2 思维导图](#总结)

---

## 实操一：手写 JWT

### JWT 是什么？

**JSON Web Token** — 三段用 `.` 拼接的 ASCII 字符串：

```
header.payload.signature
```

| 段 | 内容 | 作用 |
|:--|:-----|:-----|
| **header** | `{"alg":"HS256","typ":"JWT"}` | 声明签名算法 |
| **payload** | `{"username":"admin","exp":...}` | 用户数据（谁 + 过期时间） |
| **signature** | HMAC-SHA256 指纹 | 防篡改（只有服务器能算出来） |

### JWT 不是加密

任何人都能 base64 解码看到 header 和 payload 的内容。**JWT 是防篡改，不是加密。**

### 为什么需要 base64？

```python
流程：dict → JSON(str) → .encode() → bytes → base64 → ASCII(str)
                                                     ↑
                                            HTTP Header 只允许可见 ASCII 字符
```

- HMAC-SHA256 签名输出的是**原始二进制**，必须编码成文本才能放进 JWT
- 为了统一，header 和 payload 也一起 base64 编码
- URL-safe base64：`+` → `-`，`/` → `_`，去掉 `=` 填充

### 核心函数

```python
# 1. base64 编解码
def base64_bencode(data: bytes) -> str:   # bytes → URL-safe ASCII
def base64_bdecode(data: str) -> bytes:    # URL-safe ASCII → bytes

# 2. 签名（防篡改的核心）
def sign(header_b64: str, payload_b64: str, secret: str) -> str:
    message = f"{header_b64}.{payload_b64}"
    raw = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return base64_bencode(raw.encode())

# 3. 签发 JWT
def encode(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64_bencode(json.dumps(header).encode())
    payload_b64 = base64_bencode(json.dumps(payload).encode())
    signature = sign(header_b64, payload_b64, secret)
    return f"{header_b64}.{payload_b64}.{signature}"

# 4. 验证 JWT
def decode(jwt: str, secret: str) -> dict:
    header_b64, payload_b64, signature = jwt.split(".")
    if sign(header_b64, payload_b64, secret) != signature:
        return None  # 签名不一致 → 被篡改
    payload = json.loads(base64_bdecode(payload_b64))
    if payload.get("exp") and payload["exp"] < time.time():
        return None  # 过期了
    return payload
```

### JWT 防篡改原理

```
签名 = HMAC-SHA256("header.payload", secret)

相同内容 + 相同密钥 → 相同签名
改了内容             → 签名不一样 → 服务器拒绝
不知道密钥           → 算不出新签名 → 无法伪造
```

---

## 实操二：JWT 集成博客项目

### 改动文件

| 文件 | 改动 |
|:----|:-----|
| `utils/jwt.py` | 从实操一复制 JWT 工具函数 |
| `api/users.py` | `/login` 返回 token + 新增 `/me` |
| `api/articles.py` | `POST /articles` 需要 JWT 认证 |

### 认证流程

```python
# login → 返回 JWT
@router.post("/login")
def login(user: User):
    # 验证用户名密码...
    token = jwt_encode({
        "username": user.username,
        "user_id": row["id"],
        "exp": time.time() + 3600   # 1 小时过期
    }, SECRET)
    return {"token": token, "username": user.username}

# /me → 从 token 读出当前用户
@router.get("/me")
def get_me(authorization: str = Header(None)):
    token = authorization.split(" ")[1]       # 去掉 "Bearer "
    payload = jwt_decode(token, SECRET)
    if not payload:
        raise HTTPException(status_code=401)
    return {"username": payload["username"]}

# 发文章 → 需要有效 token
@router.post("/articles")
def post_articles(article: Article, authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    payload = jwt_decode(token, SECRET)
    if not payload:
        raise HTTPException(status_code=401)
    author_id = payload["user_id"]  # 从 token 取，不硬编码
    # ... 创建文章 ...
```

### Session vs JWT

| | Session | JWT |
|:--|:--------|:---|
| 存在哪 | 服务器（Redis/内存） | **客户端**（浏览器 localStorage） |
| 验证方式 | 查数据库/缓存 | **验签名**，不用查库 |
| 扩展性 | 需要共享 session 存储 | 天然支持分布式 |

---

## 实操三：CSRF 防护 + 安全响应头

### CSRF（跨站请求伪造）

**攻击原理：**

```html
你登录了银行 → 浏览器有 cookie（含 JWT）
你访问黑客网站 → 黑客网站藏了：
  <img src="https://bank.com/transfer?to=hacker&amount=10000">
浏览器自动带上 cookie → 银行以为是你在操作！
```

**你的项目天然防 CSRF**（因为用的是 localStorage + Authorization header，不是 cookie）：

| 方案 | 说明 | 你的项目 |
|:----|:-----|:--------:|
| CSRF Token | 表单里藏随机 token | ❌ 未用 |
| SameSite Cookie | cookie 限制跨站 | ❌ 未用 |
| Referer 检查 | 验证来源域名 | ❌ 未用 |
| **localStorage + Header** | 手动传 token，不自动带 | **✅ 在用** |

### 安全响应头（app.py）

4 行代码防 4 种攻击：

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"       # 防 MIME 嗅探
    response.headers["X-Frame-Options"] = "DENY"                 # 防点击劫持
    response.headers["X-XSS-Protection"] = "1; mode=block"       # 防 XSS
    response.headers["Strict-Transport-Security"] = "max-age=31536000"  # 强制 HTTPS
    return response
```

### 四个头各防什么

| 头 | 防什么 | 攻击例子 |
|:---|:------|:--------|
| **`X-Content-Type-Options: nosniff`** | 防 **MIME 嗅探** — 浏览器不会自作主张猜文件类型 | 你上传一张图但里面藏了 JS，浏览器不会当 JS 执行 |
| **`X-Frame-Options: DENY`** | 防 **点击劫持** — 别人不能把你的页面嵌在 iframe 里 | 黑客做个假网站，透明叠一层你的银行页面，你点的"领奖"其实是"转账" |
| **`X-XSS-Protection: 1; mode=block`** | 防 **反射型 XSS** — URL 里有可疑脚本时浏览器直接阻止 | 别人发你链接 `?q=<script>偷cookie</script>`，浏览器拦住不执行 |
| **`Strict-Transport-Security`** | **强制 HTTPS** — 告诉浏览器以后只走 HTTPS，不走 HTTP | 你手动输入 `http://你的网站`，浏览器自动换成 `https://` |

---

## 总结

```
DAY2 — 认证安全：JWT
  ├── 实操一：手写 JWT
  │   ├── JWT = header.payload.signature（三段 ASCII）
  │   ├── base64：bytes ↔ ASCII（为了网络传输）
  │   ├── HMAC-SHA256：用密钥算签名，防篡改
  │   ├── encode()：组装 JWT（dict → JSON → bytes → base64 → 签名）
  │   └── decode()：验证 JWT（拆三段 → 重新算签名 → 对比 → 检查过期）
  ├── 实操二：JWT 集成博客
  │   ├── login → 返回 JWT token（含 username + user_id + exp）
  │   ├── /me → 从 token 读出当前用户
  │   ├── 发文章 → 验证 token 后取出 author_id
  │   └── 拆代码的必要性：一个文件只做一件事
  └── 实操三：CSRF + 安全头
      ├── CSRF：黑客借你的手发请求（浏览器自动带 cookie）
      ├── localStorage + Header → 天然防 CSRF（不自动带）
      └── 4 个响应头 → 防 4 种其他攻击
```

> **明日预告：** DAY3 — GitHub OAuth
