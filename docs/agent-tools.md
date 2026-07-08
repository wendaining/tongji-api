# Agent / AstrBot 工具调用规则

`tongji-api` 支持两种调用方式：**CLI**（推荐本地 Agent）和 **HTTP**（AstrBot 或远程调用）。

## CLI 模式（推荐）

Agent 通过 subprocess 直接调用，无需启动服务：

```bash
python -m tongji <command> [options]
```

### 可用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `me` | 当前学生信息 | `python -m tongji me` |
| `notices` | 通知列表 | `python -m tongji notices --page-size 5` |
| `notice <id>` | 通知详情 | `python -m tongji notice 2717` |
| `courses` | 课程查询 | `python -m tongji courses --calendar 121` |
| `calendar list` | 校历列表 | `python -m tongji calendar list` |
| `calendar current-term` | 当前学期 | `python -m tongji calendar current-term` |
| `exams` | 考试安排查询 | `python -m tongji exams` |
| `tutor-meetings` | 新生导师见面会 | `python -m tongji tutor-meetings` |
| `scores` | 课程成绩/绩点 | `python -m tongji scores` |
| `ping` | 测试连接 | `python -m tongji ping` |
| `login` | 登录 | `python -m tongji login` |

输出为标准 JSON，字段名为中文。

## HTTP 模式

先启动服务：

```bash
python -m tongji serve --port 8000
```

所有端点均为 `GET`，无需鉴权 header：

| 端点 | 说明 |
|------|------|
| `/students/me` | 当前学生信息 |
| `/students` | 学生搜索（?studentId=&name=&faculty=） |
| `/notices` | 通知列表（?page=&page_size=&keyword=） |
| `/notices/{id}` | 通知详情 |
| `/notices/{id}?translated=1` | 通知详情（中文字段名） |
| `/courses` | 课程查询（?calendar=&page=&page_size=） |
| `/calendar/list` | 校历列表 |
| `/calendar/current-term` | 当前学期 |
| `/calendar/{id}` | 校历详情 |
| `/exams/info` | 考试安排基本信息（默认考试类型、学期列表）|
| `/exams/dictionary` | 字典查询（?keys=X_XQ&authId=9102） |
| `/tutor-meetings` | 新生导师见面会（?searchText=&page=&page_size=）|
| `/session/ping` | 测试 1 系统连接 |
| `/healthz` | 健康检查 |

## 意图映射

### 用户问"我是谁 / 当前登录账号"

```bash
python -m tongji me
# or GET /students/me
```

### 用户问"通知 / 公告 / 学校有什么消息"

```bash
python -m tongji notices --page-size 20
# or GET /notices?page_size=20
```

如果用户给了关键词：

```bash
python -m tongji notices --keyword 关键词
# or GET /notices?keyword=xxx
```

### 用户追问某条通知详情

```bash
python -m tongji notice <id>
# or GET /notices/{id}
```

### 用户问"现在第几周 / 当前学期 / 校历"

```bash
python -m tongji calendar current-term
python -m tongji calendar list
# or GET /calendar/list
```

### 用户问"课程 / 排课 / 这周有什么课"

```bash
python -m tongji courses --calendar <id>
# or GET /courses?calendar=<id>
```

### 用户问"考试 / 考试安排 / 什么时候考试"

```bash
python -m tongji exams
# or GET /exams/info
```

### 用户问"导师见面会 / 新生导师 / 见面会安排"

```bash
python -m tongji tutor-meetings
# or GET /tutor-meetings
```

## 登录态失效处理

CLI 模式会直接报错退出。Agent 应执行：

```bash
python -m tongji login
```

HTTP 模式返回 409 错误。Agent 应提示用户重新登录。

## 数据格式

所有输出字段名为中文，值已翻译（利用上游 I18n 字段）：

```json
// GET /students/me
{
  "学号": "student-demo",
  "姓名": "示例用户",
  "性别": "男",
  "校区": "嘉定校区",
  "学院": "计算机科学与技术学院"
}

// GET /notices?translated=1&page_size=2
{
  "total": 2076,
  "items": [
    {"标题": "...", "发布人": "...", "发布时间": "..."},
    ...
  ]
}
```

## 安全注意事项

- IAM 密码、验证码、sessionid、Cookie 为机密信息。
- 不要向普通聊天用户索要 IAM 密码。
- 本服务只提供只读查询，不包含写 API、选课 API、管理 API。
- 默认部署为本地或私有网络。
