# one-dot-tongji-api 第一阶段规划

## 1. 项目定位

`one-dot-tongji-api` 是一个部署在个人服务器上的同济 1 系统 raw API 工具层，不是前端网页应用。它面向 AstrBot、Agent、脚本或其他自动化服务提供 HTTP 工具接口，由调用方把自然语言意图转换成结构化调用。

目标链路：

```text
QQ / 微信
  -> AstrBot / Agent
  -> one-dot-tongji-api FastAPI 服务
  -> https://1.tongji.edu.cn/api/{service}/...
```

第一阶段只做“本人账号或明确授权账号”的只读查询能力。服务端持久化保存 1 系统登录态，并在请求 1 系统业务 API 时自动附带 `sessionid`。

## 2. 非目标和边界

明确不做：

- 不做普通网页应用、管理后台或可视化页面。
- 不接入同济开放平台 `https://api.tongji.edu.cn/v1/...`。
- 不申请或依赖 `client_id`、`client_secret`、OAuth scope、开放平台 token。
- 不把明文密码、验证码、SSO token 写入日志或 session 持久化文件。
- 不实现写接口、选课接口、管理接口、审批接口。
- 不默认暴露公网无鉴权访问。
- 不在日志中打印 `sessionid`、Cookie、SSO token、完整请求头。

`api.tongji.edu.cn` 只能作为接口命名或业务字段参考，不能成为运行时调用路径。运行时只走：

```text
https://1.tongji.edu.cn
https://1.tongji.edu.cn/api/{service}/...
```

## 3. 核心参考资料

- XiaLing233：同济大学 1 系统通知公告备份与提醒  
  https://blog.xialing.icu/2025/01/tongji-bulletin-mirror/
- XiaLing233：同济统一身份认证登录 1 系统  
  https://blog.xialing.icu/2025/01/tongji-login/
- XiaLing233：fetch-1-dot-tongji  
  https://github.com/XiaLing233/fetch-1-dot-tongji

从这些资料中确认的核心先验：

- 1 系统 raw API 可以通过同济 IAM 登录后的 1 系统登录态访问。
- 登录链路最终需要拿到 1 系统侧的 `JSESSIONID` 和 `sessionid`。
- 业务 API 重点依赖 `sessionid`，请求时需要带 `Cookie: sessionid=...` 和 `X-Token: <sessionid>`。
- 如果登录态失效，接口可能返回 `{"message":"sessionid is not exist."}`。
- 第一阶段改为参考 XiaLing233 的程序化 IAM 登录流程：服务端通过同一个 HTTP 客户端维护完整重定向链和 Cookie，拿到 `ssologin` 三元组后立即调用 `session/login`，最终持久化 `JSESSIONID` 和 `sessionid`。

## 4. 第一阶段 MVP

第一阶段交付一个可在服务器运行的 FastAPI 服务：

1. 支持程序化 IAM 登录流程：
   - 服务读取 `TJ_IAM_USERNAME` 和 `TJ_IAM_PASSWORD`。
   - 服务端请求 1 系统入口并维护同一个 HTTP cookie jar。
   - 从 IAM 登录页解析 `authnLcKey`、`spAuthChainCode`、RSA 公钥脚本地址。
   - 使用 RSA 公钥加密密码并提交 `ActionAuthChain`。
   - 如触发邮箱 MFA，服务发送验证码并返回 `login_id`，等待用户调用 `/admin/login/mfa` 提交验证码。
   - 继续请求 `AuthnEngine` 和 SSO 链路，获得 `ssologin?token=...&uid=...&ts=...`。
   - 服务端立即调用 `POST /api/sessionservice/session/login` 换取 `sessionid`。
2. 将 `JSESSIONID` 和 `sessionid` 持久化到服务器本地文件。
3. 保留 `TJ_SESSIONID`、`TJ_JSESSIONID` 和手动写入 session 作为调试 / 兜底方式，不作为主流程。
4. 封装统一 raw-one HTTP client：
   - `base_url = https://1.tongji.edu.cn`
   - 自动附带 `Cookie: sessionid=<sessionid>`
   - 自动附带 `X-Token: <sessionid>`
   - 统一超时、重试边界、错误转换和 session 失效检测
5. 暴露面向 Agent / AstrBot 的只读 HTTP 工具接口。
6. 编写 Agent 工具调用规则文档，后续放在 `docs/agent-tools.md`。
7. 第一阶段不做缓存和限流，先把登录、session 持久化和只读 API 跑通。

## 5. 推荐技术栈

- Python 3.11+
- FastAPI
- Uvicorn
- HTTPX
- Pydantic Settings
- Pydantic response models
- Pytest + respx 或 pytest-httpx
- Ruff 或 Black，用于基础格式检查

不引入数据库作为硬依赖。第一阶段 session 持久化优先使用本地 JSON 文件，例如：

```text
data/session.json
```

该文件必须被 `.gitignore` 忽略。

## 6. 建议仓库结构

```text
one-dot-tongji-api/
  app/
    main.py
    core/
      config.py
      errors.py
      logging.py
      security.py
    raw_one/
      client.py
      session_store.py
      session_state.py
      services/
        session.py
        calendar.py
        notices.py
        courses.py
    tools/
      dependencies.py
      routes_session.py
      routes_calendar.py
      routes_notices.py
      routes_courses.py
      routes_admin.py
  docs/
    phase-1-raw-one-api-tool-service-plan.md
    agent-tools.md
    raw-one-api-notes.md
  tests/
    test_session_store.py
    test_raw_one_client.py
    test_tools_calendar.py
    test_tools_notices.py
  data/
    .gitkeep
  .env.example
  .gitignore
  pyproject.toml
  README.md
```

## 7. 配置项

建议使用环境变量：

```text
TJ_SESSIONID=
TJ_JSESSIONID=
TJ_IAM_USERNAME=
TJ_IAM_PASSWORD=
TJ_API_TOKEN=
TJ_SESSION_STORE_PATH=./data/session.json
TJ_ONE_BASE_URL=https://1.tongji.edu.cn
TJ_REQUEST_TIMEOUT_SECONDS=15
TJ_LOGIN_EXPIRES_SECONDS=600
TJ_PUBLIC_BASE_URL=
TJ_LOG_LEVEL=INFO
```

含义：

- `TJ_SESSIONID`：启动时导入的 1 系统 `sessionid`，可为空。
- `TJ_JSESSIONID`：启动时导入的 1 系统 `JSESSIONID`，可为空。
- `TJ_IAM_USERNAME`：同济 IAM 学号。
- `TJ_IAM_PASSWORD`：同济 IAM 密码，只从配置读取，不写入 session store。
- `TJ_API_TOKEN`：调用本服务的本地鉴权 token，必须配置。
- `TJ_SESSION_STORE_PATH`：session 持久化位置。
- `TJ_ONE_BASE_URL`：raw-one base URL，默认固定为 1 系统。
- `TJ_REQUEST_TIMEOUT_SECONDS`：请求 1 系统超时时间。
- `TJ_LOGIN_EXPIRES_SECONDS`：MFA 登录挑战的有效期。
- `TJ_PUBLIC_BASE_URL`：保留配置，第一阶段程序化登录暂不依赖浏览器回调。

## 8. 登录态管理设计

第一阶段主流程采用程序化登录，而不是让用户复制浏览器 Cookie 或 `ssologin` URL：

```text
AstrBot / 用户 / 管理脚本
  -> POST /admin/login/start
  -> one-dot-tongji-api 使用 TJ_IAM_USERNAME / TJ_IAM_PASSWORD 请求 IAM
  -> 如果需要 MFA，发送邮箱验证码并返回 login_id
  -> 用户调用 POST /admin/login/mfa 提交验证码
  -> one-dot-tongji-api 继续同一个 HTTP cookie jar 的 SSO 链路
  -> 得到 ssologin URL 中的一次性 token / uid / ts
  -> POST https://1.tongji.edu.cn/api/sessionservice/session/login
  -> 得到 JSESSIONID + sessionid 并持久化保存
  -> 后续工具接口自动带 sessionid 请求 raw-one API
```

不能再让用户粘贴最终 `ssologin` URL：该 URL 里的 token 会被浏览器正常跳转过程消费掉，后端再次使用会拿不到 `sessionid`。

建议内部结构：

```json
{
  "sessionid": "redacted",
  "jsessionid": "redacted",
  "source": "programmatic_login",
  "created_at": "2026-07-08T20:00:00+08:00",
  "updated_at": "2026-07-08T20:00:00+08:00",
  "last_validated_at": null
}
```

MFA 登录挑战状态建议单独保存为内存态，过期后自动丢弃：

```json
{
  "login_id": "opaque-random-id",
  "status": "mfa_required",
  "mfa_channel": "email",
  "created_at": "2026-07-08T20:00:00+08:00",
  "expires_at": "2026-07-08T20:10:00+08:00"
}
```

## 9. Raw-one HTTP Client 规则

所有 1 系统请求必须经过统一 client，不允许业务 route 直接拼 HTTPX 请求。

默认请求头：

```text
Accept: application/json, text/plain, */*
User-Agent: one-dot-tongji-api/0.1
X-Token: <sessionid>
Cookie: JSESSIONID=<jsessionid>; sessionid=<sessionid>
```

统一处理：

- 网络超时转换为 `502 Bad Gateway`。
- 1 系统返回非 JSON 时保留摘要，不透传完整 HTML。
- 检测 `sessionid is not exist`、401、403，并转换为本服务的 `SESSION_EXPIRED`。
- 日志中所有 token、cookie、session 字段必须脱敏。
- POST JSON 使用 `json=payload`，不手动拼接 JSON 字符串。
- 查询参数使用 HTTPX `params`，不手动拼 URL。

统一错误响应：

```json
{
  "ok": false,
  "error": {
    "code": "SESSION_EXPIRED",
    "message": "1 系统登录态已失效，请重新登录 1 系统后更新 sessionid。"
  }
}
```

## 10. 对外工具接口

所有工具接口建议放在 `/tools/tongji/*` 下，默认只读。

### 健康和登录态

```text
GET /healthz
GET /tools/tongji/me
GET /tools/tongji/session/ping
```

对应 raw-one：

```text
GET /api/sessionservice/session/getSessionUser
GET /api/sessionservice/session/ping
```

### 校历

```text
GET /tools/tongji/calendar/list
GET /tools/tongji/calendar/current-term
GET /tools/tongji/calendar/current-week
GET /tools/tongji/calendar/{id}
```

对应 raw-one：

```text
GET /api/baseresservice/schoolCalendar/list
GET /api/baseresservice/schoolCalendar/currentTermCalendar
GET /api/baseresservice/schoolCalendar/currentWeek
GET /api/baseresservice/schoolCalendar/detail?id=...
```

### 通知公告

```text
GET /tools/tongji/notices
GET /tools/tongji/notices/{id}
GET /tools/tongji/notices/unread-count
```

建议查询参数：

```text
page=1
page_size=20
keyword=
```

对应 raw-one：

```text
POST /api/commonservice/commonMsgPublish/findHomePageCommonMsgPublish
POST /api/commonservice/commonMsgPublish/findCommonMsgPublishList
GET  /api/commonservice/commonMsgPublish/findCommonMsgPublishById?id=...
GET  /api/commonservice/commonMsgPublish/myNotReadCommonMsgCount
```

### 课程 / 排课

```text
GET /tools/tongji/courses
```

建议查询参数：

```text
calendar=
campus=
college=
course=
training_level=
page=1
page_size=200
```

对应 raw-one：

```text
POST /api/arrangementservice/manualArrange/page?profile
```

默认 payload：

```json
{
  "condition": {
    "trainingLevel": "",
    "campus": "",
    "calendar": 119,
    "college": "",
    "course": "",
    "ids": [],
    "isChineseTeaching": null
  },
  "pageNum_": 1,
  "pageSize_": 200
}
```

注意：`calendar` 不应长期硬编码为 `119`。实现时应允许调用方传入，或根据当前学期接口动态推断。

## 11. 管理接口

第一阶段只保留最小管理能力，并要求鉴权：

```text
POST /admin/login/start
POST /admin/login/mfa
GET /admin/login/{login_id}/status
GET /admin/session/status
PUT /admin/session
DELETE /admin/session
```

鉴权方式：

```text
Authorization: Bearer <TJ_API_TOKEN>
```

`POST /admin/login/start` 成功响应示例：

```json
{
  "ok": true,
  "data": {
    "status": "SUCCESS",
    "session": {
      "has_session": true,
      "has_jsession": true,
      "source": "programmatic_login"
    }
  }
}
```

`POST /admin/login/start` 触发 MFA 响应示例：

```json
{
  "ok": true,
  "data": {
    "status": "MFA_REQUIRED",
    "login_id": "opaque-random-id",
    "expires_at": "2026-07-08T20:10:00+08:00",
    "mfa": {
      "channel": "email",
      "masked_email": "s***@example.com",
      "next_step": "POST /admin/login/mfa with login_id and code"
    }
  }
}
```

`POST /admin/login/mfa` 请求体：

```json
{
  "login_id": "opaque-random-id",
  "code": "邮箱验证码"
}
```

`PUT /admin/session` 仍保留为调试 / 兜底接口，请求体：

```json
{
  "sessionid": "兜底调试用 sessionid",
  "jsessionid": "兜底调试用 JSESSIONID"
}
```

响应不回显 session 原文：

```json
{
  "ok": true,
  "data": {
    "has_session": true,
    "updated_at": "2026-07-08T20:00:00+08:00"
  }
}
```

## 12. Agent / AstrBot 调用规则

后续 `docs/agent-tools.md` 应包含这些规则：

- 用户问“通知、公告、教务消息、学校通知”时，优先调用 `GET /tools/tongji/notices`。
- 用户追问某条通知详情时，调用 `GET /tools/tongji/notices/{id}`。
- 用户问“现在第几周、教学周、校历、当前学期”时，调用 calendar 接口。
- 用户问“这周有什么课、课表、课程安排、排课”时，调用 courses 接口。
- 默认只调用只读接口。
- 不调用写接口、选课接口、管理接口。
- session 失效时，回复用户“需要重新登录 1 系统并更新 sessionid”。
- Agent 最终回复应做人话总结，不直接倾倒 raw JSON。

## 13. 安全策略

最低安全要求：

- `TJ_API_TOKEN` 必填，未设置时服务启动失败。
- 所有 `/tools/tongji/*` 和 `/admin/*` 接口都要求 Bearer token，除非部署在明确的本机回环地址并显式关闭鉴权。
- 默认监听 `127.0.0.1`，由 Nginx、Caddy、内网或反向代理控制访问。
- 日志脱敏字段：`sessionid`、`JSESSIONID`、`Cookie`、`X-Token`、`Authorization`、`token`。
- 错误响应不泄露 1 系统完整响应头、Cookie、HTML 页面。
- session store 文件权限尽量收紧，仅服务进程可读写。

## 14. 缓存和限流

第一阶段不做缓存和限流，先验证 raw-one API 能跑通。所有工具接口每次请求都直接访问 1 系统。

后续准备上线给多用户或高频 Agent 使用时，再补：

- 进程内短缓存或外部缓存。
- 单 token 简单限流。
- 针对通知列表、通知详情、课程查询的差异化 TTL。

## 15. 测试策略

不在测试中访问真实 `1.tongji.edu.cn`。

第一阶段测试覆盖：

- `POST /admin/login/start` 能执行程序化登录；成功时持久化 `JSESSIONID` 和 `sessionid`。
- `POST /admin/login/start` 触发 MFA 时能发送邮箱验证码并返回 `login_id`。
- `POST /admin/login/mfa` 能继续同一个 HTTP cookie jar 并完成登录。
- session store 能读写、更新、清空，且不会把 session 原文写入日志。
- raw-one client 能正确注入 `Cookie` 和 `X-Token`。
- raw-one client 能识别 `sessionid is not exist`。
- 工具接口能把 raw-one 响应转换为稳定 JSON。
- 管理接口需要 Bearer token。
- 无 `TJ_API_TOKEN` 时启动失败。

验收：

1. 设置 `TJ_API_TOKEN`。
2. 启动服务。
3. 设置 `TJ_IAM_USERNAME` 和 `TJ_IAM_PASSWORD`。
4. 调用 `POST /admin/login/start`。
5. 如果返回 `MFA_REQUIRED`，查看邮箱验证码并调用 `POST /admin/login/mfa`。
6. 调用 `GET /tools/tongji/session/ping`。
7. 调用 `GET /tools/tongji/calendar/current-week`。
8. 调用 `GET /tools/tongji/notices?page_size=5`。
9. 故意写入错误 session，确认返回 `SESSION_EXPIRED`。

## 16. 分阶段路线图

### Phase 1A：项目骨架

- 初始化 Python 包结构。
- 配置 FastAPI、HTTPX、Pydantic Settings。
- 增加 `.env.example`、`.gitignore`、README。
- 实现 `/healthz`。

### Phase 1B：登录态持久化

- 实现 `SessionStore`。
- 支持启动时导入 `TJ_SESSIONID` / `TJ_JSESSIONID` 作为兜底。
- 实现程序化登录任务：start、mfa、status。
- 实现 `/admin/session` 写入、删除、状态查询作为调试 / 兜底。
- 增加脱敏日志工具。

### Phase 1C：Raw-one Client

- 实现统一 HTTP client。
- 注入 `sessionid` Cookie 和 `X-Token`。
- 实现超时和错误映射。
- 增加 session 失效识别。

### Phase 1D：只读工具接口

- session：me、ping。
- calendar：list、current-term、current-week、detail。
- notices：list、detail、unread-count。
- courses：manual arrange page 查询。

### Phase 1E：Agent 文档和示例

- 编写 `docs/agent-tools.md`。
- 编写 AstrBot HTTP 调用示例。
- 给出自然语言意图到工具接口的映射表。

## 17. 后续增强

第二阶段可以做自动登录，但必须作为可选能力：

- 自动走 IAM 登录链路。
- 从登录页面解析 `authnLcKey`、`spAuthChainCode`、RSA 公钥。
- 使用 RSA 加密密码。
- 处理 `ActionAuthChain`、`AuthnEngine`、SSO redirect、`session/login`。
- 支持邮箱验证码或人工输入验证码。
- 如部署者明确接受风险，可通过环境变量或 secret manager 提供账号密码；默认不启用，不写日志，不进入文档示例的推荐路径。

第三阶段可以整理 raw-one API 知识库：

- 记录每个 raw-one endpoint 的方法、参数、响应字段、是否需要登录态。
- 将稳定接口生成 OpenAPI schema。
- 输出给 Agent 使用的工具卡片。
- 整理 AstrBot 插件示例。

## 18. 当前决策

第一阶段先实现“浏览器 IAM 登录交接 + FastAPI 只读工具接口 + Agent 调用文档”。这条路线能最快验证：

- raw-one 请求规则是否稳定；
- `sessionid` 持久化是否足够；
- AstrBot / Agent 调用形态是否顺手；
- 通知、校历、课程这三类高频问题是否能被自然语言可靠触发。

缓存、限流、IMAP 自动读取验证码、通知镜像归档、附件下载、写接口和开放平台兼容都放到后续阶段。
