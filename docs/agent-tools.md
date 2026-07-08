# Agent / AstrBot 工具调用规则

本文档给 AstrBot、Agent 或其他自动化调用方使用。服务地址以下用
`ONE_DOT_TONGJI_API_BASE` 表示。

## 通用规则

- 所有 `/tools/tongji/*` 接口都只读。
- 所有 `/tools/tongji/*` 接口都需要请求头：

```text
Authorization: Bearer <TJ_API_TOKEN>
```

- 不要调用 `/admin/*`，除非用户明确要求更新登录态。
- 不要调用写接口、选课接口、管理接口、审批接口。
- 不要直接把 raw JSON 倾倒给用户，应先整理成人话。
- 如果返回 `SESSION_EXPIRED` 或 `NO_SESSION`，提示用户重新完成 1 系统登录。

## 意图映射

### 用户问“我是谁 / 当前登录账号”

调用：

```text
GET /tools/tongji/me
```

### 用户问“登录态还在吗 / 1 系统通不通”

调用：

```text
GET /tools/tongji/session/ping
```

### 用户问“现在第几周 / 当前教学周”

调用：

```text
GET /tools/tongji/calendar/current-week
```

### 用户问“当前学期 / 现在是什么学期”

调用：

```text
GET /tools/tongji/calendar/current-term
```

### 用户问“校历 / 学期列表”

调用：

```text
GET /tools/tongji/calendar/list
```

### 用户问“通知 / 公告 / 教务通知 / 学校有什么消息”

优先调用：

```text
GET /tools/tongji/notices?page=1&page_size=20
```

如果用户给了关键词：

```text
GET /tools/tongji/notices?page=1&page_size=20&keyword=关键词
```

### 用户追问某条通知详情

调用：

```text
GET /tools/tongji/notices/{id}
```

### 用户问“有多少未读通知”

调用：

```text
GET /tools/tongji/notices/unread-count
```

### 用户问“课程 / 排课 / 这周有什么课”

调用：

```text
GET /tools/tongji/courses
```

可选查询参数：

```text
calendar=
campus=
college=
course=
training_level=
page=1
page_size=200
```

如果用户没有提供 `calendar`，第一阶段可以不传；后续可先调用当前学期接口再推断。

## 登录态失效处理

当接口返回：

```json
{
  "ok": false,
  "error": {
    "code": "SESSION_EXPIRED"
  }
}
```

Agent 应回复类似：

```text
1 系统登录态失效了，需要重新登录。请让管理员调用 /admin/login/start
发起服务端 IAM 登录；如果需要邮箱验证码，再调用 /admin/login/mfa 完成验证。
```

不要向普通聊天用户索要 IAM 密码。邮箱验证码只应在管理员明确执行登录流程时，
通过受保护的 `/admin/login/mfa` 接口提交。
