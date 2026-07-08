# tongji-api

`tongji-api` 是一个 FastAPI 服务，封装了 `https://1.tongji.edu.cn` 的部分原始 API，用于 AstrBot 和 agent 工具调用。

目前项目仍处于第一阶段：

- 仅对接原始 `1.tongji.edu.cn`，而非 `api.tongji.edu.cn`
- 服务端按 XiaLing233 的流程程序化完成同济 IAM 登录
- 通过环境变量提供 IAM 学号和密码；密码只从配置读取，不写入 session 文件
- 如果触发邮箱 MFA，服务会发送验证码并等待用户手动提交
- 将 `JSESSIONID` 和 `sessionid` 持久化到本地 JSON 文件
- 提供只读的会话、日历、通知和课程 API
- 使用 Bearer token 保护管理端和工具端路由
- 无缓存、无限流、无写入 API

## 快速开始

```powershell
uv sync --extra dev
Copy-Item .env.example .env
```

编辑 `.env` 文件并设置：

```text
TJ_API_TOKEN=...
TJ_IAM_USERNAME=...
TJ_IAM_PASSWORD=...
```

```powershell
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

然后：

1. `POST /admin/login/start`
2. 如果返回 `SUCCESS`，直接调用 `GET /tools/tongji/session/ping`
3. 如果返回 `MFA_REQUIRED`，查看邮箱验证码
4. 调用 `POST /admin/login/mfa`，请求体包含 `login_id` 和 `code`
5. 登录成功后调用 `GET /tools/tongji/session/ping`

所有 `/admin/*` 和 `/tools/tongji/*` 路由均需携带：

```text
Authorization: Bearer <TJ_API_TOKEN>
```

## 开发

```powershell
uv run pytest
uv run ruff check .
```
