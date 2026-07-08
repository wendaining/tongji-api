# API 实现状态

最后更新：2026-07-09

## 已实现（9 个服务，11 个命令）

| # | 服务 | 命令 | HTTP 端点 | 翻译 | 状态 |
|---|------|------|-----------|------|------|
| 1 | `session` | `ping` | `/session/ping`, `/session/me` | - | ✅ |
| 2 | `students` | `me` | `/students/me`, `/students` | ✅ I18n | ✅ |
| 3 | `notices` | `notices`, `notice <id>` | `/notices`, `/notices/{id}` | ✅ | ✅ |
| 4 | `calendar` | `calendar list/current-term` | `/calendar/*` | ✅ | ✅ |
| 5 | `grades` | `scores` | `/grades` | ✅ | ✅ |
| 6 | `culture` | `plan` | `/plan/credits`, `/plan/courses` | ✅ | ✅ |
| 7 | `courses` | `courses` | `/courses` | ✅ | ⚠️ 暑假无数据 |
| 8 | `timetable` | `timetable` | `/timetable` | ✅ | ⚠️ 暑假无数据 |
| 9 | `elections` | `cross-courses` | `/cross-courses/apply` | ✅ | 跨学科选课申请 |

## 已知问题

| 问题 | 影响 | 原因 |
|------|------|------|
| `currentWeek` 报 400 | `/calendar/current-week` 不可用 | 上游参数绑定方式未知，xialing 也未使用 |
| 课表数据为空 | `timetable` 命令无输出 | 暑假期间 1 系统无课表数据 |
| 排课数据为空 | `courses` 命令无输出 | 暑假期间无排课 |
| `score` 字段显示 -1 | 部分课程成绩仅显示等级 | 同济的课程只有等级制，无数字分，绩点：优对应5，良对应4，中对应3，及格对应2，不及格对应0 |

## 已实现但需注意

| API | 说明 |
|-----|------|
| `GET /grades` | 来自 `oldStysteMyGrades` 页面，返回完整成绩单（GPA、学期均绩、每门课成绩/绩点/考试类型） |
| `GET /plan/credits` | 来自培养方案，显示已修/应修学分进度 |
| `GET /plan/courses` | 来自培养方案，86 个课程模块（含未修课程） |
| `GET /calendar/current-week` | **不可用**，上游报 `getCurrentWeek.arg0: 不能为null` |

## 未实现

按 `docs/1-tongji-api-catalog.md` 中的优先级排列。

### Phase 2 优先（学生高频只读）

| 优先级 | 模块 | 关键 API | 说明 |
|--------|------|---------|------|
| 1 | ✅ 课表 | `timetable/course/{sid}` | 已实现，暑假无数据 |
| 2 | ✅ 成绩 | `scoreGrades/getMyGrades` | 已实现 |
| 3 | ✅ 学生信息 | `studentInfo/findStuInfoList` | 已实现 |
| 4 | ✅ 培养方案 | `bclCulturePlan/*` | 已实现 |
| 5 | 🔲 考试安排 | `undergraduateExamQuery/*` | 未实现 |
| 6 | 🔲 数据字典 | `dictionary/query` | 未实现 |
| 7 | 🔲 选课查询 | `elcCourseTake/page` | 未实现（只读查询） |
| 8 | 🔲 教师信息 | `teacherInfo/*` | 未实现 |

### 从浏览器 Network 发现的其他 API

| API | 页面 | 说明 |
|-----|------|------|
| `scoremanagementservice/studentScoreBk/queryCourseTag` | oldStysteMyGrades | 课程成绩标签（辅助） |
| `studentservice/studentDetailInfo/getStatusInfoByStudentId` | oldStysteMyGrades | 学籍状态信息 |
| `evaluationservice/questionnaireStudent/force` | oldStysteMyGrades | 评教强制问卷 |
| `commonservice/dictionary/query` | oldStysteMyGrades | 字典查询（JSON body） |
| `sessionservice/session/currentAuthId` | oldStysteMyGrades | 当前权限 ID |
| `electionservice/elcMutualApply/page` | 跨学科选课申请 | 跨学科选课申请列表 |
| `electionservice/elcMutualCourses/findDept` | 跨学科选课申请 | 跨学科选课院系列表 |

### 管理端/写入 API（后续阶段）

29 个微服务中大部分为管理端 API（排课管理、选课管理、学籍管理、用户管理等），约 900+ 端点，暂不实现。

## CLI 命令速查

```bash
python -m tongji me              # 学生信息
python -m tongji scores          # 完整成绩单
python -m tongji plan            # 培养方案 + 学分统计
python -m tongji notices         # 通知列表
python -m tongji notice <id>     # 通知详情
python -m tongji calendar list   # 校历列表
python -m tongji calendar current-term  # 当前学期
python -m tongji courses         # 课程查询（暑假空）
python -m tongji timetable       # 课表（暑假空）
python -m tongji login           # 登录（自动 IMAP 收码）
python -m tongji serve           # 启动 HTTP 服务
python -m tongji ping            # 测试连接
python -m tongji cross-courses --student-id student-demo --calendar 121  # 跨学科选课申请
```

## HTTP 端点速查

```
GET /healthz
GET /students/me
GET /students
GET /notices
GET /notices/{id}
GET /grades
GET /plan/credits
GET /plan/courses
GET /courses
GET /timetable
GET /calendar/list
GET /calendar/current-term
GET /calendar/current-week    ← 不可用
GET /calendar/{id}
GET /session/ping
GET /session/me
GET /cross-courses/apply
```
