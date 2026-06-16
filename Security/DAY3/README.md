# Security DAY3 — OAuth2.0 第三方登录 🔐

---

## 目录

- [实操一：OAuth2.0 原理](#实操一oauth20-原理)
- [实操二：GitHub OAuth 实战](#实操二github-oauth-实战)
- [总结：DAY3 思维导图](#总结)

---

## 实操一：OAuth2.0 原理

### 为什么需要 OAuth？

用户不想在每个网站都注册账号，他想**直接用 GitHub 账号登录**。

**问题：**
- 用户不想把 GitHub 密码给你
- 但你确实需要知道用户是谁

**OAuth2.0 的方案：**
```
用户点 "Login with GitHub"
  → 跳转到 GitHub 官方授权页
  → 用户点"同意"
  → GitHub 通知你的后端："用户同意了，他的信息给你"
  → 你用这个信息注册/登录用户
```

**全程用户没把 GitHub 密码给你。**

### 4 种角色

| 角色 | 白话 | 你的项目里 |
|:----|:-----|:----------:|
| **资源拥有者** | 用户本人 | 你的用户 |
| **客户端** | 想登录的网站 | 你的博客项目 |
| **授权服务器** | GitHub 的登录页面 | GitHub |
| **资源服务器** | GitHub 的 API | GitHub |

### 授权码模式（核心流程）

```
用户浏览器                   你的后端                      GitHub
    │                          │                          │
    │  1. 点 "GitHub 登录"     │                          │
    │─────────────────────────>│                          │
    │                          │                          │
    │  2. 返回授权 URL         │                          │
    │<─────────────────────────│                          │
    │                          │                          │
    │  3. 跳转 GitHub 点同意   │                          │
    │─────────────────────────────────────────────────>│
    │                          │                          │
    │  4. 回调 → 带 code       │                          │
    │<──────────────────────────────────────────────────│
    │                          │                          │
    │  5. code + secret 换 token                         │
    │─────────────────────────────────────────────────>│
    │                          │                          │
    │  6. 返回 access_token                              │
    │<──────────────────────────────────────────────────│
    │                          │                          │
    │  7. 用 token 调 API 拿用户信息                     │
    │─────────────────────────────────────────────────>│
    │                          │                          │
    │  8. 返回用户信息                                    │
    │<──────────────────────────────────────────────────│
    │                          │                          │
    │  9. 注册/登录 → 签发 JWT                            │
    │                          │                          │
    │  10. 返回 JWT token     │                          │
    │<─────────────────────────│                          │
```

### 为什么需要 code？

```
直接返回 token：
  黑客拦截回调 URL → token 泄露 → 你的数据被偷 ❌

code + client_secret：
  code 一次性，几分钟过期
  client_secret 只有你的后端知道，不走浏览器
  黑客拿到 code 也没用，没有 secret 换不到 token ✅
```

### 关键术语

| 术语 | 是什么 | 类比 |
|:----|:------|:-----|
| **client_id** | 你的应用的"工牌"，公开的 | 工牌 |
| **client_secret** | 你的应用的"密码"，绝密 | 银行卡密码 |
| **code** | GitHub 给你的一次性通行证 | 号码牌 |
| **access_token** | 调 GitHub API 用的令牌 | VIP 手环 |
| **scope** | 你请求的权限范围 | 权限清单 |

### scope 权限

```
scope=read:user   → 读用户公开信息（最基本的）
scope=user:email  → 读邮箱地址
scope=repo        → 读私有仓库（危险！）
```

---

## 实操二：GitHub OAuth 实战

### 代码结构

```python
# GET /auth/github/login — 返回 GitHub 授权 URL
@router.get("/auth/github/login")
def github_login():
    params={
        "client_id":os.getenv("GITHUB_CLIENT_ID",""),
        "redirect_uri":os.getenv("GITHUB_REDIRECT_URI",""),
        "scope":"read:user"
    }
    url = f"https://github.com/login/oauth/authorize?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&scope={params['scope']}"
    return {"url":url}

# GET /auth/github/callback?code=xxx — GitHub 回调
@router.get("/auth/github/callback")
def github_callback(code:str):
    # 1. code + secret → access_token
    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id":os.getenv("GITHUB_CLIENT_ID",""),
            "client_secret":os.getenv("GITHUB_CLIENT_SECRET",""),
            "code":code,
            "redirect_uri":os.getenv("GITHUB_REDIRECT_URI","")
        },
        headers={"Accept":"application/json"},
        timeout=30,
        verify=False
    )
    data =  response.json()
    access_token = data.get("access_token")

    # 2. access_token → 用户信息
    user_response = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization":f"Bearer {access_token}"},
        timeout=30,
        verify=False
    )
    user_data = user_response.json()
    return {"user":user_data}
```

### 两个接口的分工

| 接口 | 做什么 | 技术点 |
|:----|:-------|:-------|
| `GET /auth/github/login` | 返回 GitHub 授权 URL | 拼接 URL + 环境变量 |
| `GET /auth/github/callback` | 收 code → 换 token → 拿用户信息 | httpx POST/GET |

### httpx 的两个用法

```python
# POST — 发数据给 GitHub（带 secret，后台对后台）
response = httpx.post(url, data={...}, headers={...})

# GET — 调 API 拿数据（带 token 在 Header 里）
response = httpx.get(url, headers={"Authorization": f"Bearer {token}"})
```

### Bearer Token

```python
headers={"Authorization": f"Bearer {access_token}"}
```

`Bearer` = "持有者令牌"，跟你在 JWT 课写的 `authorization.split(" ")[1]` 是同一个东西。

### FastAPI 自动解析 URL 参数

```python
# GitHub 回调 URL: /auth/github/callback?code=abc123
def github_callback(code: str):       # FastAPI 自动从 URL 参数里取 code
```

跟之前学的一样：
- `Header(None)` → 从请求头取
- `code: str` → 从 URL 查询参数取
- `article_id: int` → 从 URL 路径取

### 环境变量配置

```env
GITHUB_CLIENT_ID=你的client_id
GITHUB_CLIENT_SECRET=你的client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

### OAuth + JWT 串联

```
OAuth2.0 → 拿到 GitHub 用户身份
     ↓
在你的数据库注册/查找用户
     ↓
签发你的 JWT token（你项目内部认证）
     ↓
后续请求带 JWT（跟之前一样）
```

### 踩坑记录

| 坑 | 原因 | 解决 |
|:---|:-----|:-----|
| Docker 环境变量没传 | `env_file` 没加 | 用 `env_file: .env` |
| `MYSQL_PORT` 类型错误 | `os.getenv` 返回字符串 | 用 `int()` 转换 |
| SSL 证书验证失败 | 代理拦截 HTTPS | `verify=False` |
| httpx 超时 | 网络慢 | 加 `timeout=30.0` |

---

## 总结

```
DAY3 — OAuth2.0 第三方登录
  ├── 实操一：OAuth2.0 原理
  │   ├── OAuth = 用户不用给你密码，也能登录
  │   ├── 4 种角色：用户 / 应用 / GitHub 授权 / GitHub API
  │   ├── 授权码模式：code + secret → token → 用户信息
  │   ├── client_id（公开工牌）vs client_secret（机密密码）
  │   └── scope = 权限范围 read:user
  └── 实操二：GitHub OAuth 实战
      ├── /auth/github/login → 返回授权 URL
      ├── /auth/github/callback → code → token → 用户信息
      ├── httpx.post 换 token（后台对后台）
      ├── httpx.get 拿用户信息（Bearer token 在 Header）
      ├── FastAPI 自动解析 URL 参数（code: str）
      └── OAuth 拿身份 → JWT 做内部认证
```

> **下一个任务：** DAY4 — HTTPS/TLS + CORS 跨域
