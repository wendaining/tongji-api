# API Status

最后更新：2026-07-09

- Raw module：45 个，统一注册在 module registry。
- Agent tool：由 `scripts/generate_docs.py` 从 FastAPI 路由生成。
- 登录：IAM RSA、无 MFA、IMAP MFA 和手动 MFA。
- 会话：持久化 `JSESSIONID` 与 `sessionid`，失效后要求显式重新登录。
- 边界：只读、单账号、默认回环地址、无缓存、无限流。

详细接口见：

- [Raw API Reference](api-reference.md)
- [Agent Tools](agent-tools.md)
- 运行服务后的 `/openapi.json`

`currentWeek` 优先调用上游；上游参数绑定失败时，Agent 工具根据当前学期开始日期计算并标记来源。
