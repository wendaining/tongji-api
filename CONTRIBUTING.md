# Contributing

## 项目定位

`tongji-api` 是 `1.tongji.edu.cn` 的只读 API 工具层，不是网页或通知镜像。仓库只维护一份供 AstrBot/Agent 调用服务的 `docs/SKILL.md`，不包含框架插件代码。

架构分为：

```text
XiaLing 风格 IAM 登录层
  -> api-enhanced 风格 raw module registry
  -> tongji-api Agent 工具层
```

- 登录流程参考 [XiaLing233/fetch-1-dot-tongji](https://github.com/XiaLing233/fetch-1-dot-tongji)。
- module、SDK/HTTP 同源思路参考 [api-enhanced](https://github.com/neteasecloudmusicapienhanced/api-enhanced)。
- 不使用 `api.tongji.edu.cn`、OAuth、`client_id` 或 `client_secret`。

## 代码边界

- `tongji/core/`：配置、登录、session、统一 HTTP client 和已验证的上游调用。
- `tongji/modules/`：每个 raw API 的名称、参数、路由、模型和 executor。
- `tongji/tools/`：面向 Agent 的聚合能力和稳定 snake_case 输出。
- `tongji/server.py`：生命周期和路由装配，不放业务逻辑。
- `tongji/cli.py`：服务管理、登录、通用 module/tool 调用，不复制业务实现。

新增普通查询时先注册 raw module；只有存在明确自然语言场景时才增加 Agent tool。

## Raw 请求规范

所有上游请求必须经过 `RawOneClient`：

```text
base URL: https://1.tongji.edu.cn
X-Token: <sessionid>
Cookie: JSESSIONID=<jsessionid>; sessionid=<sessionid>
```

- POST 查询使用 `application/x-www-form-urlencoded`。
- Spring MVC 嵌套参数使用 `condition.field` 点号展开。
- GET 查询使用 `params=`，需要时附加毫秒时间戳。
- 除 IAM/login/logout 协议外，不直接创建第二套 HTTP client。
- raw `/api/*` 保持上游字段和层级；Agent `/tools/tongji/*` 才做规范化。
- 当前不实现 AES 学号或附件路径加密，也不从登录响应持久化 AES key/IV。

## 登录和安全

登录状态机必须对照 XiaLing 的 `loginout.py` 和 `encrypt.py`：

```text
FETCH_ENTRY -> SUBMIT_PASSWORD -> MFA -> AUTHN_ENGINE -> SESSION_LOGIN
```

不得记录或提交：

- IAM 密码和验证码
- `sessionid`、`JSESSIONID`、Cookie、`X-Token`
- SSO token、授权头、IMAP 授权码
- 真实姓名、学号、邮箱或原始响应

测试和文档统一使用 `student-demo`、`示例用户` 等虚构数据。

## 新增 API

1. 从浏览器 Network 获取真实请求，不猜 method 和参数。
2. 在 core service 中实现经过验证的上游调用。
3. 在 module registry 中声明请求模型、alias、响应模型和文档。
4. 使用 `MockTransport` 验证 method、path、query/form 和 session header。
5. 如需自然语言任务，再在 AgentTools 中组合 module。
6. 更新生成文档：

```bash
uv run python scripts/generate_docs.py
```

详细经验和已知上游限制见 `docs/development.md`。

## 质量检查

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy tongji
uv run pytest -q
uv run python scripts/generate_docs.py --check
uv run python -m build
```

真实上游 smoke test必须单独标记，且不得保存响应。

## 文档规则

`docs/` 只保留：

- `api.md`：从 registry 和 FastAPI 自动生成的公开 API 文档。
- `development.md`：人工维护的逆向经验、架构决策和已知问题。
- `SKILL.md`：供 AstrBot/Agent 使用的中文 API 调用指令。

仓库开发 Agent 的操作入口是根目录 `AGENTS.md`；部署后的聊天 Agent 使用 `docs/SKILL.md`。

## Git 提交

提交信息使用两段式格式：

```text
<type>(optional scope): <short English summary>

* 做了什么：……
* 为什么：……
* 影响范围：……
* 注意事项：……
```

第一行使用英文 Conventional Commits，中文正文保持 2 至 5 条明确说明。
