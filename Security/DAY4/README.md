# Security DAY4 — HTTPS/TLS + CORS 跨域 🔐

---

## 目录

- [实操一：HTTPS / TLS 加密](#实操一https--tls-加密)
- [实操二：CORS 跨域](#实操二cors-跨域)
- [总结：DAY4 思维导图](#总结)

---

## 实操一：HTTPS / TLS 加密

### HTTP 为什么不安全？

```
HTTP 明文传输（端口 8000）：

你发 POST /login?username=admin&password=123456
                            │
                            ▼
                  中间人抓包直接看到密码 ❌
```

**Wireshark / 路由器 / WiFi 热点都能抓到。**

### HTTPS = HTTP + TLS

```
HTTPS 加密传输（端口 443）：

你发 POST /login?username=admin&password=123456
                            │
                            ▼
                  客户端 TLS 加密 → 乱码
                            │
                            ▼
                  服务端 TLS 解密 → 正常处理
                            │
                            ▼
                  服务端 TLS 加密返回 → 乱码
                            │
                            ▼
                  客户端 TLS 解密 → 看到响应 ✅
```

**中间人抓到也是一堆乱码。**

### 三种密钥

| 密钥 | 谁有 | 作用 |
|:----|:----|:----|
| **公钥** | 所有人（浏览器拿到） | 加密会话密钥 |
| **私钥** | 只有服务器有 | 解密会话密钥 |
| **会话密钥** | 浏览器 + 服务器（协商出来的） | 加密所有后续通信 |

### TLS 握手（四次通信）

```
Browser                              Server
  │                                     │
  │  1. "我要 HTTPS，支持哪些加密？"      │
  │────────────────────────────────────>│
  │                                     │
  │  2. 返回证书（含公钥）+ 选加密算法    │
  │<────────────────────────────────────│
  │                                     │
  │  3. 验证证书 → 生成会话密钥          │
  │     用公钥加密会话密钥 → 发过去       │
  │────────────────────────────────────>│
  │                                     │
  │  4. 私钥解密会话密钥 ✅              │
  │     "好的，之后用这个密钥加密"        │
  │<────────────────────────────────────│
  │                                     │
  │  之后全部用会话密钥（对称加密）       │
  │════════════════════════════════════>│
```

**三步精髓：**

```
非对称加密（公钥+私钥）→ 安全传递会话密钥
                  ↓
对称加密（会话密钥）   → 加密所有数据（快）
```

### 自签证书 vs CA 证书

| | 自签证书 | CA 证书 |
|:--|:--------|:--------|
| 价格 | 免费 | 收费 / 免费（Let's Encrypt） |
| 浏览器 | ❌ 红色警告 | ✅ 绿色安全锁 |
| 用途 | 开发/测试 | 生产部署 |

### 实操指令

```bash
# 1. 生成私钥
openssl genrsa -out key.pem 2048

# 2. 生成自签证书（Git Bash 要加 MSYS_NO_PATHCONV=1）
MSYS_NO_PATHCONV=1 openssl req -new -x509 \
    -key key.pem -out cert.pem \
    -days 365 -subj "/CN=localhost"

# 3. 启动 HTTPS 服务器
uvicorn app:app --host 0.0.0.0 --port 8843 \
    --ssl-keyfile key.pem --ssl-certfile cert.pem

# 4. 测试（-k 跳过自签证书验证）
curl -k -X POST "https://localhost:8843/login?username=admin&password=123456"
```

### 验证 HTTPS 加密

```bash
# HTTP（明文 —— 危险）
curl -X POST "http://localhost:8000/login?username=admin&password=123456"
# 响应：{"username":"admin","password":"123456"}

# HTTPS（加密 —— 安全，但自签证书要 -k）
curl -k -X POST "https://localhost:8843/login?username=admin&password=123456"
# 响应一样，但网络传输中是乱码

# 没有 -k → SEC_E_UNTRUSTED_ROOT（自签证书不被信任）
curl -X POST "https://localhost:8843/login?username=admin&password=123456"
```

---

## 实操二：CORS 跨域

### 同源策略（Same-Origin Policy）

```
同源 = 协议 + 域名 + 端口 完全一致

同源 ✅：http://localhost:5500 → http://localhost:5500
跨源 ❌：http://localhost:5500 → http://localhost:8000（端口不同）
```

**同源策略是浏览器的安全机制：**
- 页面里的 JS 只能读取**同源**的资源
- 读取**跨源**资源会被浏览器拦截

### CORS 的流程

```
前端（localhost:5500）→ 后端（localhost:8000）

fetch 发请求 → 服务器收到并处理 ✅
             ↓
          服务器返回数据 ✅
             ↓
          浏览器拿到数据 ✅
             ↓
          浏览器检查 CORS 头：
            Access-Control-Allow-Origin: *
             ↓
          有 → 放行 ✅
          没有 → 拦截 ❌
```

**CORS 是服务器声明、浏览器执行的策略。**

### CORS 不是后端安全

```
CORS 拦截的是浏览器的 JS 读取响应，不是请求本身。

❌ curl 不受 CORS 影响
❌ Postman 不受 CORS 影响
✅ 浏览器里的 fetch / XMLHttpRequest 受影响
```

### FastAPI CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许哪些来源
    allow_methods=["*"],      # 允许哪些 HTTP 方法
    allow_headers=["*"],      # 允许哪些请求头
)
```

| 参数 | 意思 | 生产环境建议 |
|:----|:-----|:------------|
| `allow_origins` | 允许的域名 | 写具体域名，不写 `*` |
| `allow_methods` | 允许的 HTTP 方法 | 只写需要的，如 `["GET", "POST"]` |
| `allow_headers` | 允许的自定义请求头 | 按需开放 |

### CORS 与 JWT、CSRF 的区别

| 机制 | 保护什么 | 谁执行 | 类比 |
|:----|:--------|:------|:----|
| **JWT** | 认证身份（你是谁） | 后端 | 身份证 |
| **CORS** | 阻止跨源读取（防止数据被偷读） | 浏览器 | 门卫 |
| **CSRF** | 阻止跨源写入（防止伪造操作） | 浏览器/后端 | 防伪章 |

---

## 总结

```
DAY4 — HTTPS/TLS + CORS
  ├── 实操一：HTTPS/TLS 加密
  │   ├── HTTP 明文传输，HTTPS 加密传输（TLS 层）
  │   ├── 三种密钥：公钥（锁） / 私钥（钥匙） / 会话密钥（对称）
  │   ├── TLS 握手：非对称交换会话密钥 → 对称加密通信
  │   ├── CA 证书 = 可信第三方签名，自签证书只用于开发（浏览器警告）
  │   ├── OpenSSL 实操：genrsa → req -new -x509 → uvicorn --ssl
  │   └── curl -k 跳过自签证书验证
  └── 实操二：CORS 跨域
      ├── 同源策略 = 协议 + 域名 + 端口一致
      ├── CORS = 服务器声明（响应头），浏览器执行（拦截）
      ├── FastAPI：CORSMiddleware（allow_origins / methods / headers）
      ├── CORS 只影响浏览器 JS（curl / Postman 不受影响）
      ├── JWT = 身份认证 / CORS = 跨源读保护 / CSRF = 跨源写保护
      └── 前端 fetch 默认 GET，手动 method: "POST"
```
