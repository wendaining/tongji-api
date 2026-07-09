# Agent / AstrBot Tools

本文件由 `scripts/generate_docs.py` 生成。Agent 应优先调用本页工具，不要直接拼接 1 系统上游参数。

| Method | Route | Purpose |
|---|---|---|

## 调用规则

- 通知、公告、教务消息：调用 `/tools/tongji/notices`，追问详情时再调用详情。
- 当前周、学期、校历：调用 `/tools/tongji/calendar/*`。
- 今天或本周课程：调用 `/tools/tongji/schedule/today` 或 `schedule/week`。
- 成绩与考试：分别调用 `/tools/tongji/grades` 和 `/tools/tongji/exams`。
- `SESSION_EXPIRED` 且 `action_required=login` 时，提示管理员重新登录。
- 默认只调用只读工具，不向聊天用户索要 IAM 密码、验证码或 Cookie。
