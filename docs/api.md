# API 文档

本文件由 `scripts/generate_docs.py` 从 module registry 和 FastAPI 路由生成，请勿手工编辑。

## 入口选择

1. Agent 日常任务优先调用 `/tools/tongji/*`。
2. 不启动服务时使用一次性的 `tongji tool` 聚合命令。
3. `/api/*` 与 `tongji call` 仅用于 raw 数据和接口调试。

常驻 HTTP 服务会复用进程、连接池和 session。连续执行多个 `tongji call` 会重复冷启动，不适合 Agent 工作流。

## Agent 工具

| Method | HTTP Route | CLI Tool | Purpose |
|---|---|---|---|

工具会自动补齐当前学生、当前学期和教学周。完整参数及响应模型以 `/openapi.json` 为准。

### CLI 示例

```bash
uv run tongji tool notices --data '{"page_size":5}'
uv run tongji tool notice --data '{"notice_id":"..."}'
uv run tongji tool schedule-week
uv run tongji tool grades
uv run tongji tool score-rank
```

CLI tool 参数使用 snake_case。每条 `tongji tool` 命令只启动一次 Python。

## Raw API Modules

| Module | Method | Route | Description |
|---|---|---|---|
| `students_me` | `GET` | `/api/students/me` | 查询当前学生 |
| `students_list` | `GET` | `/api/students` | 查询学生列表 |
| `notices_list` | `GET` | `/api/notices` | 查询通知列表 |
| `notices_my` | `GET` | `/api/notices/my` | 查询与当前用户相关的通知 |
| `notices_detail` | `GET` | `/api/notices/{notice_id}` | 查询通知详情 |
| `notices_unread_count` | `GET` | `/api/notices/unread-count` | 查询未读通知数量 |
| `courses_list` | `GET` | `/api/courses` | 查询排课课程 |
| `calendar_list` | `GET` | `/api/calendar/list` | 查询校历列表 |
| `calendar_current_term` | `GET` | `/api/calendar/current-term` | 查询当前学期 |
| `calendar_current_week` | `GET` | `/api/calendar/current-week` | 查询当前教学周 |
| `calendar_professional_work` | `GET` | `/api/calendar/professional-work` | 查询校历教学安排 |
| `calendar_holidays` | `GET` | `/api/calendar/holidays` | 查询年度节假日 |
| `calendar_detail` | `GET` | `/api/calendar/{calendar_id}` | 查询校历详情 |
| `plan_credits` | `GET` | `/api/plan/credits` | 查询培养方案学分统计 |
| `plan_courses` | `GET` | `/api/plan/courses` | 查询培养方案课程 |
| `timetable_student` | `GET` | `/api/timetable` | 查询学生课表 |
| `grades_list` | `GET` | `/api/grades` | 查询学生成绩 |
| `grades_tags` | `GET` | `/api/grades/tags` | 查询成绩课程标签 |
| `exams_schedule` | `GET` | `/api/exams` | 查询考试安排 |
| `exams_info` | `GET` | `/api/exams/info` | 查询考试元数据 |
| `exams_dictionary` | `GET` | `/api/exams/dictionary` | 查询考试数据字典 |
| `tutor_meetings` | `GET` | `/api/tutor-meetings` | 查询导师见面会 |
| `timetable_major` | `GET` | `/api/timetable/major` | 查询专业课表 |
| `teaching_progress_list` | `GET` | `/api/teaching-progress` | 查询教学进度 |
| `teaching_progress_detail` | `GET` | `/api/teaching-progress/{progress_id}` | 查询教学进度详情 |
| `cross_courses_apply` | `GET` | `/api/cross-courses/apply` | 查询跨学科课程申请 |
| `session_ping` | `GET` | `/api/session/ping` | 检查 1 系统会话 |
| `session_user` | `GET` | `/api/session/me` | 查询 1 系统会话用户 |
| `students_tabs` | `GET` | `/api/students/tabs` | 查询学生可见标签 |
| `students_stations` | `GET` | `/api/students/stations` | 查询生源地字典 |
| `classroom_towers` | `GET` | `/api/classroom/towers` | 查询教学楼 |
| `help_articles` | `GET` | `/api/help/articles` | 查询帮助文章 |
| `help_groups` | `GET` | `/api/help/groups` | 查询帮助分组 |
| `scores_rank` | `GET` | `/api/scores/rank` | 查询成绩排名 |
| `culture_strength_class` | `GET` | `/api/culture/strength-class` | 查询强化班状态 |
| `attendance_class_dates` | `GET` | `/api/attendance/class-dates` | 查询有课日期 |
| `attendance_class_content` | `GET` | `/api/attendance/class-content` | 查询指定日期课程 |
| `students_status` | `GET` | `/api/students/status` | 查询学生申请状态 |
| `students_activation` | `GET` | `/api/students/activation` | 查询学生激活状态 |
| `help_my` | `GET` | `/api/help/my` | 查询我的帮助文章 |
| `students_picture` | `POST` | `/api/students/picture` | 查询学生照片 |
| `elections_rounds` | `GET` | `/api/elections/rounds` | 查询选课轮次 |
| `elections_apply_list` | `GET` | `/api/elections/apply-list` | 查询选课申请列表 |
| `classroom_usage_report` | `GET` | `/api/classroom/usage-report` | 查询教室使用情况 |
| `culture_strength_class_info` | `GET` | `/api/culture/strength-class-info` | 查询强化班信息 |

raw 路由保留 1 系统原始字段和响应层级。CLI 调试示例：

```bash
uv run tongji modules
uv run tongji call calendar_current_term
uv run tongji call grades_list --data '{"student_id":"student-demo"}'
```

## 错误

| Code | Meaning |
|---|---|
| `NO_SESSION` | 尚未保存 1 系统登录态 |
| `SESSION_EXPIRED` | 登录态失效，`action_required=login` |
| `UPSTREAM_ERROR` | 1 系统超时、不可达或返回 HTTP 错误 |
| `VALIDATION_ERROR` | module 或 tool 参数不符合模型 |

排名 `data: null`、课表空列表等属于合法业务结果，不属于上述错误。
