# tongji-api

`tongji-api` 是一个同济大学 `1.tongji.edu.cn` 系统的 CLI + HTTP 工具包，用于 AstrBot、agent 和其他自动化工具。

架构参考 [NeteaseCloudMusicApiEnhanced](https://github.com/neteasecloudmusicapienhanced/api-enhanced)：核心逻辑 (`core/`) 由 CLI 和 HTTP server 共享。

目前项目仍处于第一阶段：

- 服务端按 XiaLing233 的流程程序化完成同济 IAM 登录
- 通过环境变量提供 IAM 学号和密码；密码只从配置读取，不写入 session 文件
- 如果触发邮箱 MFA，自动通过 IMAP（QQ 邮箱）读取验证码
- 将 `JSESSIONID` 和 `sessionid` 持久化到本地 JSON 文件
- 提供只读的会话、学生信息、通知、日历和课程 API
- 无缓存、无限流、无写入 API

## 快速开始

```powershell
uv sync --extra dev
Copy-Item .env.example .env
```

编辑 `.env` 文件并设置：

```text
TJ_IAM_USERNAME=学号
TJ_IAM_PASSWORD=密码
TJ_IMAP_EMAIL=邮箱
TJ_IMAP_GRANTCODE=邮箱授权码
```

## 使用方式

### CLI 模式（推荐日常使用）

```powershell
# 登录
uv run python -m tongji login

# 查询
uv run python -m tongji me              # 学生信息
uv run python -m tongji notices         # 通知列表
uv run python -m tongji notice <id>     # 通知详情
uv run python -m tongji courses         # 课程查询
uv run python -m tongji calendar list   # 校历

# 查看所有命令
uv run python -m tongji --help
```

### HTTP 服务模式（给 AstrBot 等调用）

```powershell
uv run python -m tongji serve --port 8000
```

端点：

```
GET /healthz
GET /students/me
GET /students
GET /notices
GET /notices/{id}
GET /courses
GET /calendar/list
GET /calendar/current-term
GET /session/ping
```

无需 Bearer token——1 系统 session 即鉴权。

### Docker（可选）

```powershell
docker build -t tongji-api .
docker run -p 8000:8000 --env-file .env tongji-api
```

## 开发

```powershell
uv run pytest
uv run ruff check .
```
