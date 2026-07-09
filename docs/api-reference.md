# Raw API Reference

本文件由 `scripts/generate_docs.py` 从 module registry 生成，请勿手工编辑。

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

所有 raw 路由保留 1 系统原始字段和响应层级。参数定义及响应 schema 以 `/openapi.json` 为准。
