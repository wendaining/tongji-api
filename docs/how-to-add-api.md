# 如何新增 Raw API Module

## 原则

不要猜接口。先从浏览器 Network 面板复制真实请求，并确认 method、URL、query、form body 和响应结构。

所有运行时请求必须通过 `RawOneClient`，不得使用同济开放平台。

## 实现步骤

1. 在 `tongji/core/services/` 编写或确认上游调用，只使用 `params=` 和 form-encoded `data=`。
2. 在 `tongji/modules/catalog.py` 注册一个唯一的 `ModuleDefinition`：
   - module 名称
   - `/api/*` route 和公开 HTTP method
   - 请求字段、alias 和校验
   - summary、description、tag
   - service 或自定义 executor
3. 若能力需要面向 Agent，修改 `tongji/tools/service.py` 组合 raw module，并在工具路由中暴露稳定的 snake_case 响应。
4. 运行文档生成器，更新 raw module 和 Agent 工具清单。

```powershell
uv run python scripts/generate_docs.py
```

## 测试要求

- 使用 `httpx.MockTransport` 验证真实上游 method、path、query/form 和 session header。
- 使用匿名合成数据验证 raw 响应和 Agent 规范化结果。
- 不提交浏览器 Cookie、session、IAM 信息或真实学生数据。

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy tongji
uv run pytest -q
uv run python scripts/generate_docs.py --check
```

Registry 会自动提供 Python SDK、CLI、HTTP 路由和 OpenAPI，不要再在 `server.py` 或 CLI 中重复注册接口。
