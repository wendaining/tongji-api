# tongji-api

`tongji-api` 是面向 AstrBot、Agent 和脚本的同济大学 1 系统只读工具服务。

项目由三层组成：

```text
XiaLing 风格 IAM 登录状态机
  -> api-enhanced 风格 raw API module registry
  -> 面向 Agent 的组合工具
```

运行时只请求 `https://1.tongji.edu.cn`，不使用同济开放平台。

## 能力

- 程序化 IAM 登录、RSA 密码加密和邮箱 MFA
- 持久化 `JSESSIONID` 与 `sessionid`
- 45 个 `/api/*` raw module，保留上游响应结构
- 14 个 `/tools/tongji/*` Agent 工具，使用稳定的 snake_case 字段
- Python SDK、HTTP 服务和通用 CLI 共用同一个 module registry
- FastAPI OpenAPI、Docker 和 GitHub Actions

## 安装

```powershell
uv sync --extra dev
Copy-Item .env.example .env
```

在 `.env` 中配置 IAM 账号。需要自动读取邮箱验证码时，再配置 IMAP：

```text
TJ_IAM_USERNAME=
TJ_IAM_PASSWORD=
TJ_IMAP_EMAIL=
TJ_IMAP_GRANTCODE=
```

密码和验证码不会写入 session 文件。

## 登录

```powershell
uv run tongji login
```

配置 IMAP 时会自动等待验证码；否则命令会在同一进程提示输入验证码。

## HTTP 服务

```powershell
uv run tongji serve
```

默认地址为 `http://127.0.0.1:8000`：

- Swagger：`/docs`
- OpenAPI：`/openapi.json`
- Raw modules：`/api/*`
- Agent tools：`/tools/tongji/*`
- Module 清单：`/meta/modules`
- Tool 清单：`/meta/tools`

服务不提供 Bearer token，默认只能监听回环地址。显式绑定内网地址时，HTTP 登录管理接口不会注册。

## CLI 和 Python

```powershell
uv run tongji tool grades
uv run tongji tool schedule-week
uv run tongji modules
uv run tongji call calendar_current_term
uv run tongji call notices_list --data '{"page":1,"page_size":5}'
uv run tongji ping
```

```python
from tongji.sdk import TongjiClient

result = await sdk.call("calendar_current_term")
```

## Docker

```powershell
docker compose up -d --build
docker compose exec tongji-api tongji login
```

Compose 只发布到宿主机 `127.0.0.1:8000`，session 保存在命名卷中。

## 开发

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy tongji
uv run pytest -q
uv run python scripts/generate_docs.py --check
uv run python -m build
```

Agent 开始任务前应阅读 [AGENTS.md](AGENTS.md)。接口清单见
[API 文档](docs/api.md)，逆向和开发经验见
[开发经验沉淀](docs/development.md)。部署到 AstrBot 时使用
[Skill](docs/SKILL.md)。

## 安全边界

- 仅用于本人账号或明确授权账号。
- 不记录 IAM 密码、验证码、Cookie、SSO token 或授权头。
- 只提供查询能力，不实现选课写入、管理或其他破坏性接口。
- 不要直接暴露到公网。
