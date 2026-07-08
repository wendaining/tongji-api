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
| 6 | `culture` | `plan`, `plan-detail` | `/plan/credits`, `/plan/courses`, `/plan/detail` | ✅ | ✅ |
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
| `GET /plan/detail` | 来自培养方案详情页 `myBclCultureScheme`，返回方案元信息、模板明细、学期、课程标签 |
| `GET /plan/detail/queryStudentCultureScheme` | 学生培养方案关联查询，获取关联的 scheme ID |
| `GET /plan/detail/cultureSchemeById/{id}` | 按 ID 查培养方案详情 |
| `GET /plan/detail/cultureSchemeDetailList/{id}` | 培养方案模板明细列表 |
| `GET /plan/detail/cultureSchemeTerms/{id}` | 培养方案对应学期 |
| `GET /plan/detail/cultureLabelList/{id}` | 方案课程标签列表 |
| `GET /plan/detail/cultureLabelRelation/{id}` | 方案课程标签关联 |

## 未实现

按 `docs/1-tongji-api-catalog.md` 中的优先级排列。

### Phase 2 优先（学生高频只读）

| 优先级 | 模块 | 关键 API | 说明 |
|--------|------|---------|------|
| 1 | ✅ 课表 | `timetable/course/{sid}` | 已实现，暑假无数据 |
| 2 | ✅ 成绩 | `scoreGrades/getMyGrades` | 已实现 |
| 3 | ✅ 学生信息 | `studentInfo/findStuInfoList` | 已实现 |
| 4 | ✅ 培养方案 | `bclCulturePlan/*`, `bclCultureScheme/*`, `bclStudentCultureRel/*` | 已实现（含详情页） |
| 5 | 🔲 考试安排 | `undergraduateExamQuery/*` | 未实现 |
| 6 | 🔲 数据字典 | `dictionary/query` | 未实现 |
| 7 | 🔲 选课查询 | `elcCourseTake/page` | 未实现（只读查询） |
| 8 | 🔲 教师信息 | `teacherInfo/findTeacherInfoList` | ✅ **已确认可用**，POST 请求，学生可查 |

### 主动探测发现的其他可用 API

> 以下端点通过对 1.tongji.edu.cn 发起真实 HTTP 请求验证，学生 Session 能返回真实数据。

| 服务 | 端点 | 方法 | 说明 | 数据 |
|------|------|------|------|------|
| `commonservice` | `administrativeClass/query` | POST | 行政班查询 | 20+ 条 |
| `commonservice` | `workbenchMsg/queryAllWorkbenchMsg` | POST | 工作台消息 | 20 条/页 |
| `commonservice` | `commonMsgPublish/myNotReadCommonMsgCount` | GET | 未读通知数 | 返回计数 |
| `commonservice` | `campusProfession/findCampusProfessionList` | POST | 校区专业列表 | 100+ 条 |
| `baseresservice` | `holiday/list` | GET | 假期列表 | 37 条 |
| `baseresservice` | `schoolCalendar/nextTermCalendar` | GET | 下学期校历 | 1 条 |
| `baseresservice` | `schoolCalendar/currentTermCalendar` | GET | 当前学期（直接查） | 1 条 |
| `baseresservice` | `classroomController/getClassroomInfoList` | POST | 教室/建筑信息 | 20 条/页 |
| `baseresservice` | `classroomOccupation/getClassroomUsageRateByWeek` | POST | 教室占用率（按周） | 1068 条 |
| `cultureservice` | `bclCourses/page` | POST | 课程库分页查询 | 20 条/页 |
| `arrangementservice` | `teachingTask/page` | POST | 教学任务查询 | 2890 条 |
| `scoremanagementservice` | `studentScoreBk/queryCourseTag` | GET | 课程标签（精品/通识/美育分类） | 12 条 |
| `sessionservice` | `session/queryQuickAccessMenu` | GET | 快捷菜单/权限树 | 20 项 |
| `sessionservice` | `session/getSessionUser` | GET | 当前登录用户完整信息 | 1 条 |
| `studentservice` | `teacherInfo/findTeacherInfoList` | POST | 教师信息查询 | 10+ 条/页 |

**注**：以上均以本科生示例用户的账号验证。其中 `teacherInfo` 之前标记为未实现，实际可用。

### 教师/管理端 API（学生 Session 不可用）

以下端点虽然在前端代码中引用，但用学生 Session 调用返回 403/404/405 或"无权限"，因此在本项目中不需要实现：  

| API | 原因 |
|-----|------|
| `studentDetailInfo/getStatusInfoByStudentId` | 405 Method Not Allowed |
| `studentEduBackg/findEduBackgroudList` | 405 |
| `studentAward/findAwardList` | 404 |
| `studentRegister/findRegisterInfo` | 404 |
| `studentParty/findPartyInfo` | 404 |
| `studentDic/findAllStuDicts` | 405 |
| `studentInfo/findAllStuInfoList` | 无权限 |
| `evaluationservice/questionnaireStudent/force` | 需评教上下文 |

### 管理端/写入 API（后续阶段）

34 个微服务中大部分为管理端 API（排课管理、选课管理、学籍管理、用户管理等），约 1100+ 端点，暂不实现。

## CLI 命令速查

```bash
python -m tongji me              # 学生信息
python -m tongji scores          # 完整成绩单
python -m tongji plan            # 培养方案 + 学分统计
python -m tongji plan-detail     # 培养方案详情（方案/模板/学期/标签）
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
GET /plan/detail
GET /plan/detail/queryStudentCultureScheme?stuid={sid}
GET /plan/detail/cultureSchemeById/{schemeId}
GET /plan/detail/cultureSchemeDetailList/{cultureId}
GET /plan/detail/cultureSchemeTerms/{schemeId}
GET /plan/detail/cultureLabelList/{schemeId}
GET /plan/detail/cultureLabelRelation/{schemeId}
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
