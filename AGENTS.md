# Agent 操作手册

## 先做什么

这个项目是同济大学 `1.tongji.edu.cn` 的只读 API 工具服务。收到“查通知、课表、成绩、考试”等任务时：

1. 先读本文件，不要先翻源码。
2. 优先调用 `/tools/tongji/*`，它会自动补齐学号、当前学期和教学周。
3. 只有缺少对应工具或需要调试原始响应时，才使用 `/api/*` 或 `tongji call`。
4. 不要向用户索要 IAM 密码、验证码、Cookie、`sessionid` 或 `JSESSIONID`。

开发与提交规范不在本文件，见 `CONTRIBUTING.md`。

## 选择最快入口

### 首选：常驻 HTTP 服务

先探测：

```bash
curl -s http://127.0.0.1:8000/healthz
```

成功时直接调用 HTTP。常驻服务会复用 Python 进程、连接池和 session，适合一次任务中的连续查询。

如果服务未启动：

```bash
uv run tongji serve
```

### 次选：单进程聚合 CLI

不方便启动服务，但只需完成一个任务时，使用：

```bash
uv run tongji tool <tool-name> [--data '<json>']
```

`tongji tool` 会在一次进程内完成学号、学期、课表等依赖查询。不要把它拆成多次 `tongji call`。

### 最后：Raw CLI

```bash
uv run tongji call <module-name> --data '<json>'
```

每次 `tongji call` 都会重新启动 Python，通常需要约 1 至 2 秒。它是 raw API 调试入口，不是日常 Agent 任务入口。

可用 module 和参数：

```bash
uv run tongji modules
```

## 常见任务

### 学校通知

```text
GET /tools/tongji/notices?page_size=20
uv run tongji tool notices --data '{"page_size":20}'
```

用户追问具体通知时再调用：

```text
GET /tools/tongji/notices/{notice_id}
uv run tongji tool notice --data '{"notice_id":"..."}'
```

不要一开始就逐条请求所有通知详情。

### 今天或本周课程

```text
GET /tools/tongji/schedule/today
GET /tools/tongji/schedule/week

uv run tongji tool schedule-today
uv run tongji tool schedule-week
```

工具会自动查询当前学生、当前学期和教学周，不要先手工调用 `students_me`。

### 当前教学周和学期

```text
GET /tools/tongji/calendar/current-week
GET /tools/tongji/calendar/current-term

uv run tongji tool current-week
uv run tongji tool current-term
```

当上游 `currentWeek` 不可用时，工具会根据校历计算，并在 `meta.source` 中返回 `calculated`。

### 成绩与指定学期绩点

```text
GET /tools/tongji/grades
uv run tongji tool grades
```

这一步已经自动查询本人学号。不要再先调用 `students_me`。

成绩结果通常按学期存放在 `data.term[]`：

- 使用 `termName` 判断自然语言学期名称。
- 使用 `calName` 或上游学期代码精确匹配。
- 每学期课程一般位于 `creditInfo[]`。
- 用户说“大二下”但无法唯一映射时，应向用户确认学年，不要猜固定 calendar ID。

### 成绩排名

```text
GET /tools/tongji/scores/rank
uv run tongji tool score-rank
```

排名接口可能合法返回 `data: null`。此时 `meta.available=false`，应回答“当前账号或当前时间暂无可用排名”，不要当作程序异常，也不要反复重试。

### 考试安排

```text
GET /tools/tongji/exams
uv run tongji tool exams
```

### 当前用户

```text
GET /tools/tongji/me
uv run tongji tool me
```

## 错误处理

| 错误 | Agent 行为 |
|---|---|
| `NO_SESSION` | 提示管理员先执行 `uv run tongji login` |
| `SESSION_EXPIRED` | 提示登录态失效，需要管理员重新登录 |
| `UPSTREAM_ERROR` | 简短说明 1 系统暂时不可用，不要高频重试 |
| `VALIDATION_ERROR` | 检查工具参数，不要靠反复试错猜参数 |
| 排名 `data: null` | 正常边界情况，说明排名暂不可用 |
| 课表或排课为空 | 可能处于假期、学期未开始或没有安排 |

普通聊天用户不应触发 `/admin/*`，也不应看到内部 Cookie 或上游错误正文。

## 项目边界

- 本项目只提供 API、SDK 和调试 CLI，不包含 Agent Skill。
- Skill、AstrBot 插件和特定 Agent 提示词应作为独立衍生项目维护。
- 本项目只实现只读查询，不调用选课写入、管理和其他破坏性接口。
