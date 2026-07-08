# tongji-api

`tongji-api` 是一个 FastAPI 服务，封装了 `https://1.tongji.edu.cn` 的部分原始 API，用于 AstrBot 和 agent 工具调用。

第一阶段的范围有意保持精简：

- 仅对接原始 `1.tongji.edu.cn`，而非 `api.tongji.edu.cn`
- 通过粘贴最终的 `ssologin` URL 完成浏览器登录交接
- 将 `sessionid` 持久化到本地 JSON 文件
- 提供只读的会话、日历、通知和课程 API
- 使用 Bearer token 保护管理端和工具端路由
- 无缓存、无限流、无写入 API

## 快速开始

```powershell
uv sync --extra dev
Copy-Item .env.example .env
```

编辑 `.env` 文件并设置 `TJ_API_TOKEN`。

```powershell
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

然后：

1. `POST /admin/login/start`
2. 浏览器中打开返回的 `login_url`
3. 在浏览器中完成 IAM 登录
4. 将最终的 `https://1.tongji.edu.cn/ssologin?token=...&uid=...&ts=...`
   URL 粘贴到 `POST /admin/login/complete`
5. 调用 `GET /tools/tongji/session/ping`

所有 `/admin/*` 和 `/tools/tongji/*` 路由均需携带：

```text
Authorization: Bearer <TJ_API_TOKEN>
```

## 开发

```powershell
uv run pytest
uv run ruff check .
```
