# Docker 部署与入门 / Docker Setup & Getting Started

> 适合零基础的同学，从安装到写出第一个 Dockerfile。  
> For absolute beginners — from installation to writing your first Dockerfile.
>
> **中英双语 / Bilingual**

---

## 📥 一、安装 Docker / Installation

### 下载链接 / Download Links

| 系统 Platform | 下载链接 Download Link |
|---|---|
| **Windows** | [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) |
| **macOS** | [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) |
| **Linux** | 见下方 / See below |

> **💡 小贴士 / Tip**：Docker Desktop 对个人开发者免费。Linux 下推荐用包管理器安装 Docker Engine，而非 Desktop。
>
> Docker Desktop is free for personal use. On Linux, prefer installing Docker Engine via your package manager over Docker Desktop.

---

### Windows 安装注意 / Windows Installation Notes

Windows 上 Docker 依赖 **WSL 2（Windows Subsystem for Linux 2）**，安装前请确保：

Docker on Windows requires **WSL 2**. Before installing, make sure:

```bash
# 以管理员身份打开 PowerShell / Run as Administrator in PowerShell
wsl --install                    # 安装 WSL 2 和默认 Linux 发行版
wsl --set-default-version 2      # 确保默认版本为 WSL 2
```

**常见坑 / Common Pitfalls** 🕳️

- ❌ **虚拟化未开启** → 进 BIOS 开启 Intel VT-x / AMD-V
- ❌ **WSL 2 未正确安装** → 运行 `wsl --status` 检查状态
- ❌ **Hyper-V 冲突** → 某些旧版 VMware/VirtualBox 可能与 Hyper-V 冲突

> Virtualization not enabled → Enable Intel VT-x / AMD-V in BIOS.  
> WSL 2 not properly installed → Run `wsl --status` to check.  
> Hyper-V conflicts → Some older VMware/VirtualBox versions conflict with Hyper-V.

---

### macOS 安装注意 / macOS Installation Notes

- **Intel Mac**：Docker Desktop 直接安装即可
- **Apple Silicon (M1/M2/M3)**：Docker Desktop 已原生支持 ARM，但部分老旧镜像可能需要加 `--platform linux/amd64` 参数运行
- 也可用 **Colima** 替代 Docker Desktop（更轻量）：

> For Apple Silicon: Docker Desktop natively supports ARM. Some old images may need `--platform linux/amd64`.  
> Alternative: [Colima](https://github.com/abiosoft/colima) — a lighter Docker Desktop alternative.

```bash
brew install colima
colima start
```

---

### Linux 安装 / Linux Installation

以 Ubuntu/Debian 为例 / For Ubuntu/Debian:

```bash
# 卸载旧版本 / Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# 安装依赖 / Install dependencies
sudo apt update
sudo apt install ca-certificates curl gnupg

# 添加 Docker 官方 GPG 密钥 / Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加仓库 / Add repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker / Install Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 验证 / Verify
sudo docker run hello-world
```

**🚀 免 sudo 运行 Docker / Run Docker without sudo**

```bash
sudo usermod -aG docker $USER
# 重新登录或执行 newgrp docker 生效
# Log out and back in, or run: newgrp docker
```

---

### 🌐 二、配置国内镜像源 / Configure Chinese Mirror Registry

> 🚨 **非常重要！** 不配置镜像源，在中国大陆 `docker pull` 会超时或极慢。  
> **Critical!** Without a mirror registry, `docker pull` will time out or be extremely slow in mainland China.

**配置方法 / Configuration Method**：

1. 打开 Docker Desktop → Settings → Docker Engine
2. 编辑 `daemon.json`，添加 registry mirrors：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

3. 点击 **Apply & Restart**

**验证配置是否生效 / Verify**：

```bash
docker info
# 输出中应包含 Registry Mirrors 列表
# Should see "Registry Mirrors:" in the output
```

> ⚠️ **注意**：这些镜像站可能随时间失效，建议定期检查或搜索"最新 Docker 国内镜像源"。  
> These mirrors may become unavailable over time. Search for "latest Docker China mirror" periodically.

---

### 🚀 安装后验证 / Verify Installation

```bash
# 查看版本 / Check version
docker --version

# 查看 Docker 系统信息 / System-wide info
docker info

# 跑通 hello-world / Run hello-world
docker run hello-world
```

如果看到欢迎信息，恭喜你，Docker 安装成功！🎉

If you see the welcome message, congratulations — Docker is installed successfully!

---

## 🐳 三、Docker 初体验 / First Experience

### 1. `docker pull` — 拉取镜像 / Pull an Image

```bash
docker pull hello-world
```

> `docker pull` 从镜像仓库（默认 Docker Hub）下载镜像到本地。  
> `docker pull` downloads an image from a registry (default: Docker Hub) to your local machine.

**常用变体 / Common variants**：

```bash
docker pull ubuntu:22.04              # 指定标签（版本）/ Specify tag (version)
docker pull nginx:latest              # latest 标签 / The "latest" tag
docker pull python:3.10-slim          # 轻量版 Python / Slim Python image
```

**已拉取的镜像列表 / List pulled images**：

```bash
docker images
# 或 / Or
docker image ls
```

---

### 2. `docker run` — 运行容器 / Run a Container

```bash
docker run hello-world
```

这条命令的执行流程 / What happens behind the scenes:

1. Docker 检查本地是否有 `hello-world` 镜像 / Checks if local image exists
2. 如果没有，自动执行 `docker pull hello-world` / If not, auto-pulls it
3. 基于该镜像创建一个新容器 / Creates a new container from the image
4. 运行容器，输出欢迎信息后退出 / Runs the container, prints welcome message, then exits

**🚩 常用参数 / Common Flags**：

| 参数 Flag | 作用 Purpose | 示例 Example |
|---|---|---|
| `-d` | 后台运行（detach）/ Run in background | `docker run -d nginx` |
| `-it` | 交互式终端 / Interactive terminal | `docker run -it ubuntu bash` |
| `--rm` | 退出后自动删除容器 / Auto-remove on exit | `docker run --rm hello-world` |
| `-p` | 端口映射 / Port mapping | `docker run -p 8080:80 nginx` |
| `--name` | 指定容器名 / Assign a name | `docker run --name my-nginx nginx` |

**查看运行中的容器 / List containers**：

```bash
docker ps            # 运行中的 / Running containers
docker ps -a         # 所有（含已停止）/ All containers (including stopped)
```

**🕳️ 常见坑 / Common Pitfall**：

> ❌ 在 Windows 上，如果 WSL 2 未正确配置，`docker run` 可能报错：
> `docker: error during connect...`
>
> ✅ 检查 WSL 2 是否启用、Docker Desktop 是否已启动。
>
> On Windows, if WSL 2 isn't properly configured, `docker run` may fail.  
> Check that WSL 2 is enabled and Docker Desktop is running.

---

## 📄 四、Dockerfile — 构建自己的镜像 / Build Your Own Image

Dockerfile 是一个文本文件，包含一系列**指令（instructions）**，告诉 Docker 如何构建镜像。

A Dockerfile is a text file containing instructions that tell Docker how to build an image.

---

### `.dockerignore` — 忽略不必要的文件 / Ignore Unnecessary Files

**作用 / Purpose**：

告诉 Docker 构建上下文中有哪些文件**不该**被发送到 Docker 守护进程。类似于 `.gitignore`。

Tells Docker which files in the build context should **NOT** be sent to the Docker daemon. Similar to `.gitignore`.

**为什么重要 / Why It Matters** 🎯

| 原因 Reason | 说明 Explanation |
|---|---|
| 🏎️ **加快构建速度** | 减少发送到守护进程的文件体积 / Reduces the data sent to the daemon |
| 🔒 **提升安全性** | 避免 `.env`、密钥等敏感文件被打包进镜像 / Prevents secrets like `.env` from being baked in |
| 🎯 **减少镜像体积** | 不需要的文件不会被加入镜像层 / Unnecessary files won't add to image layers |

**示例 / Example** (`.dockerignore`)：

```dockerignore
.git
__pycache__
*.pyc
.env
.vscode
node_modules
Dockerfile
.gitignore
README.md
```

> **💡 最佳实践**：在项目根目录创建 `.dockerignore`，养成习惯。  
> Best practice: always create `.dockerignore` at your project root.

---

### 以 Flask 为例的 Dockerfile / Example: Flask Dockerfile

```dockerfile
# ============================================
# 阶段 1：选择基础镜像 / Stage 1: Base Image
# ============================================
FROM python:3.10-slim

# 🔍 FROM 指定基础镜像 / Specifies the base image
#    - python:3.10-slim 是官方 Python 镜像的轻量版（基于 Debian）
#    - slim 比 full 小很多（~120MB vs ~900MB），包含运行 Python 所需的最小依赖
#
#    python:3.10-slim is the official Python slim image (Debian-based).
#    "slim" is much smaller than "full" — enough for most Python apps.

# ============================================
# 阶段 2：设置工作目录 / Stage 2: Set Working Directory
# ============================================
WORKDIR /app

# 🔍 WORKDIR 设置容器内的工作目录 / Sets the working directory inside the container
#    - 类似 cd，后续 COPY / RUN / CMD 都在此目录下执行
#    - 如果目录不存在，Docker 会自动创建
#    - Always use an absolute path for clarity
#
#    Like `cd` — subsequent COPY, RUN, CMD execute relative to this path.
#    Docker creates the directory if it doesn't exist.

# ============================================
# 阶段 3：复制依赖文件 / Stage 3: Copy Dependencies
# ============================================
COPY requirements.txt .

# 🔍 为什么先复制 requirements.txt 而不是全部代码？
# Why copy requirements.txt before the rest of the code?
#
#    Docker 构建是分层缓存的（layer caching）。
#    如果先 COPY . .，任何代码改动都会 invalidate 整个缓存层，
#    导致每次构建都要重新 pip install。
#
#    先复制 requirements.txt 并运行 pip install，
#    只要 requirements.txt 不变，这层缓存就有效，
#    构建速度大幅提升！
#
#    Docker builds use layer caching. Every instruction creates a layer.
#    If we COPY all code first, any code change invalidates the pip install cache.
#    By copying requirements.txt first, Docker caches the pip layer
#    and only reruns it when requirements.txt changes.
#    This speeds up builds significantly!

# ============================================
# 阶段 4：安装 Python 依赖 / Stage 4: Install Dependencies
# ============================================
RUN pip install --no-cache-dir --user -r requirements.txt

# 🔍 RUN 在构建过程中执行命令 / Executes commands during build
#    - --no-cache-dir：不缓存 pip 包，减小镜像体积
#    - --user：安装到用户目录，不需要 root 权限（更安全）
#    - 最终镜像会更小、更安全
#
#    --no-cache-dir: don't cache pip packages (smaller image)
#    --user: install to user directory (no root needed, more secure)

# ============================================
# 阶段 5：复制全部代码 / Stage 5: Copy All Source Code
# ============================================
COPY . .

# 🔍 复制所有项目文件到工作目录
# 注意 .dockerignore 排除了不必要的文件
#
# Copies all project files to the working directory.
# .dockerignore excludes unnecessary files.

# ============================================
# 阶段 6：声明端口 / Stage 6: Declare Port
# ============================================
EXPOSE 5000

# 🔍 EXPOSE 声明容器监听哪个端口（仅做文档说明）
#    并不会自动发布端口！运行容器时仍需 -p 参数：
#    docker run -p 5000:5000 your-image
#
#    EXPOSE documents which port the container listens on.
#    It does NOT publish the port — you still need -p at runtime.
#    Think of it as a comment/self-documentation for your image.

# ============================================
# 阶段 7：启动命令 / Stage 7: Startup Command
# ============================================
CMD ["sh", "-c", "python init_db.py && python app.py"]

# 🔍 CMD 指定容器启动时执行的命令 / Defines the startup command
#    - 每个 Dockerfile 只有一个 CMD 生效
#    - 使用 exec 格式（JSON array）：CMD ["executable", "arg1", "arg2"]
#    - 这里用 sh -c 是因为需要 && 链接两个命令
#    - 先用 init_db.py 初始化数据库，再启动应用
#
#    Only one CMD per Dockerfile is effective.
#    Prefer exec form (JSON array) over shell form.
#    Here, `sh -c` chains two commands: init DB first, then start the app.
#    This ensures the database schema is ready before the app serves requests.
```

---

### 构建与运行 / Build & Run

```bash
# 构建镜像 / Build the image (注意末尾的 . 是构建上下文)
# Note: the trailing dot is the build context
docker build -t my-flask-app .

# 运行容器 / Run the container
docker run -d -p 5000:5000 --name flask-app my-flask-app

# 查看日志 / View logs
docker logs flask-app

# 进入容器内部 / Enter the container shell
docker exec -it flask-app bash

# 停止并删除容器 / Stop and remove the container
docker stop flask-app
docker rm flask-app

# 一键停止并删除 / One-liner: stop & remove
docker rm -f flask-app
```

---

## 🏗️ 五、多阶段构建 / Multi-stage Builds

> 多阶段构建是一种优化技术：**用一个 Dockerfile 定义多个 `FROM` 阶段**，每个阶段可以用不同的基础镜像，最终只把需要的产物复制到最后一个阶段。  
> Multi-stage builds let you use multiple `FROM` statements in one Dockerfile. Only the final stage becomes the image — build tools and intermediate artifacts are discarded.

### 为什么需要多阶段构建？/ Why Multi-stage?

| 问题 Problem | 多阶段的解法 Solution |
|---|---|
| ❌ 编译型语言（C++/Go/Java）需要完整的编译工具链，但运行时只需要编译好的二进制 | ✅ 第一阶段装编译器编译，第二阶段只复制编译产物 |
| ❌ Python 项目 `pip install` 会下载很多临时文件 | ✅ 第一阶段装依赖，第二阶段只复制 `site-packages` |
| ❌ 镜像体积大，传输和部署慢 | ✅ 最终镜像只包含运行时所需的最小文件 |

### 以 Flask 为例 / Flask Example

```dockerfile
# ============================================
# 第一阶段：构建阶段 / Stage 1: Builder
# 目标：安装 Python 依赖
# Purpose: Install all Python dependencies
# ============================================
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 🔍 AS builder 给这个阶段命名，后续可以引用它
#    安装的依赖保存在 /root/.local/ 下
#
#    AS builder names this stage so we can reference it later.
#    Pip packages installed with --user go to /root/.local/.

# ============================================
# 第二阶段：运行阶段 / Stage 2: Runtime
# 目标：最小化最终镜像
# Purpose: Minimal final image
# ============================================
FROM python:3.10-slim

WORKDIR /app

# 从 builder 阶段复制已安装的 Python 包
# Copy installed Python packages from the builder stage
COPY --from=builder /root/.local /usr/local

# 把 /usr/local/bin 加入 PATH，确保 pip 安装的命令可用
# Ensure pip-installed commands are in PATH
ENV PATH=/usr/local/bin:$PATH

# 复制项目代码
# Copy project source code
COPY . .

EXPOSE 5000
CMD ["sh", "-c", "python init_db.py && python app.py"]
```

**对比效果 / Size Comparison** 🎯

| 方式 Method | 镜像体积 Image Size |
|---|---|
| ❌ 单一阶段（不带 `--no-cache-dir`） | ~500MB+ |
| ❌ 单一阶段（带 `--no-cache-dir`） | ~350MB |
| ✅ **多阶段构建** | **~120MB** |

> 多阶段构建把构建工具和中间产物隔离在 builder 阶段，最终镜像只留运行时所需的东西，体积大幅减小。  
> Multi-stage builds isolate build tools in the builder stage — the final image only contains what's needed at runtime.

### 📦 实际输出对比 / Real-world Output

```bash
# 构建多阶段镜像
docker build -t myblog:multi-stage .

# 单一阶段构建（不带多阶段，单一FROM）
docker build -t myblog:single-stage -f Dockerfile.single .

# 对比大小 / Compare sizes
docker images | grep myblog

# 输出示例 / Example output:
# myblog          multi-stage     a1b2c3d4   120MB
# myblog          single-stage    e5f6g7h8   380MB
```

---

## 🔒 六、非 root 用户 / Non-root User

### 为什么重要？/ Why Does It Matter? 🚨

默认情况下，容器以 **root 用户** 运行。但这**不推荐**：

By default, containers run as **root**. This is **not recommended**:

| 风险 Risk | 说明 Explanation |
|---|---|
| 🐞 **权限过大** | 如果应用被攻击（如 RCE），攻击者获得容器内的 root 权限 / If your app is compromised, the attacker gets root inside the container |
| 📁 **意外修改系统文件** | 应用 bug 可能误删或篡改系统文件 / A bug could accidentally delete or modify system files |
| 🔗 **主机文件权限问题** | 如果挂载了宿主机目录，root 写出的文件在宿主机上可能无法删除 / Files written as root on mounted volumes may be undeletable on the host |

**一句话 / In one sentence**：让你的应用只用它需要的权限，不要给多余的权利。  
Principle of least privilege — your app should only have the permissions it needs.

---

### 实战：带安全加固的完整 Dockerfile / Production-Ready Dockerfile

下面的示例包含了你踩过的两个坑以及对应的修复：

The following example includes both pitfalls you encountered and their fixes:

```dockerfile
# ============================================
# 第一阶段：构建阶段 / Builder Stage
# ============================================
FROM python:3.10-slim AS builder
WORKDIR /myblog
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# 第二阶段：运行阶段 / Runtime Stage (with audit)
# ============================================
FROM python:3.10-slim
WORKDIR /myblog

# --- 复制依赖 ---
COPY --from=builder /root/.local /usr/local
ENV PATH=/usr/local/bin:$PATH

# --- 创建非 root 用户 ---
RUN useradd --create-home appuser

# 🕳️ 坑 1 / Pitfall 1：为什么要 --create-home？
#
# 如果你只写 RUN useradd appuser，系统不会自动创建 home 目录。
# 但 pip 安装的缓存和一些运行时文件默认会写入 /home/appuser，
# 如果这个目录不存在，就会报错！
# 加上 --create-home（或 -m）让系统自动创建 home 目录。
#
# If you only write RUN useradd appuser, no home directory is created.
# But pip cache and some runtime files expect /home/appuser to exist.
# Without it, you'll get a "No such file or directory" error!
# --create-home (or -m) creates the home directory automatically.

# --- 复制代码 ---
COPY . .

# 🕳️ 坑 2 / Pitfall 2：为什么需要 chown？
#
# 前面的 COPY . . 是用 root 复制的，文件所有者是 root。
# 切换到 appuser 后，应用就无法写入这些文件了！
# 比如你的应用要在 /myblog/uploads 下保存文件，会报 Permission denied。
# RUN chown 把文件所有者改为 appuser，应用才能正常读写。
#
# Files copied with COPY . . are owned by root.
# After switching to appuser, the app can't write to them!
# e.g., saving a file to /myblog/uploads would fail with Permission denied.
# RUN chown changes the owner so appuser can read and write.

RUN chown -R appuser:appuser /myblog

# --- 切换到非 root 用户 ---
USER appuser

# 🔍 USER 之后的所有指令（CMD 等）都以 appuser 身份运行
# 安全风险大幅降低！
# All subsequent instructions (including CMD) run as appuser.
# This significantly reduces security risks!

EXPOSE 5000
CMD ["sh", "-c", "python init_db.py && python app.py"]
```

### 验证当前用户 / Verify the User

```bash
# 进入容器后 / Inside the container
whoami
# 输出：appuser（不再是 root！）

id
# uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
```

### 常见问题 / FAQ

**Q: 使用非 root 用户后，apt install 还能用吗？**  
A: 不能了。如果你需要在容器里额外安装系统包，在 `USER appuser` **之前** 用 root 安装完。

**Q: 如果我的应用需要写某个特定目录怎么办？**  
A: 确保这个目录在 `chown` 范围内，或单独 `RUN chown appuser:appuser /path/to/dir`。

**Q: 端口号小于 1024（如 80、443）能绑定吗？**  
A: 非 root 用户不能绑定特权端口（<1024）。解决方案：
   - 使用 >=1024 的端口（如 8080、8443），运行时用 `-p 80:8080` 映射
   - 或者给容器加 `CAP_NET_BIND_SERVICE` 能力

> Non-root users can't bind to privileged ports (<1024). Use ports >=1024 and map them at runtime with `-p 80:8080`.

---

## 📚 附：常用 Docker 命令速查 / Quick Command Reference

| 操作 Action | 命令 Command |
|---|---|
| 列出镜像 | `docker images` / `docker image ls` |
| 列出所有容器 | `docker ps -a` |
| 查看日志 | `docker logs <container>` |
| 实时跟踪日志 | `docker logs -f <container>` |
| 进入容器 shell | `docker exec -it <container> bash` |
| 查看资源占用 | `docker stats` |
| 清理未使用的镜像/容器 | `docker system prune` |
| 清理所有（含卷） | `docker system prune -a --volumes` 🚨 |
| 从 Docker Hub 搜索镜像 | `docker search <name>` |
| 标记并推送至仓库 | `docker tag <img> <user>/<repo>:<tag>`<br>`docker push <user>/<repo>:<tag>` |

---

## 🧩 拓展阅读 / Further Reading

- [Docker 官方文档 / Official Docs](https://docs.docker.com/)
- [Docker 最佳实践 / Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Dockerfile 参考 / Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Hub](https://hub.docker.com/) — 查找公共镜像 / Find public images

---

> **📝 笔记来源 / About This Note**
>
> 由 CS 大一新生整理，记录 Docker 学习过程中的知识点和踩过的坑。  
> 希望能帮到后来的同学！欢迎补充和指正 🙌
>
> Written by a CS freshman, documenting Docker knowledge and pitfalls encountered along the way.  
> Hope this helps fellow students! Contributions and corrections are welcome 🙌
