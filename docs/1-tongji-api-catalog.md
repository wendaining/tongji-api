# 1.tongji.edu.cn API 全景

从 workbench 的 `app.js` 中提取的完整 API 端点清单。共 **29 个微服务**、**949 个端点**。

## 已实现（Phase 1）

| 服务 | 端点 | 说明 |
|------|------|------|
| `sessionservice` | `ping`, `getSessionUser` | 登录态查询 |
| `ssoservice` | `loginIn` | SSO 登录入口 |
| `baseresservice` | `schoolCalendar/list`, `currentTermCalendar`, `currentWeek`, `detail` | 校历 |
| `commonservice` | `commonMsgPublish/findHomePageCommonMsgPublish`, `findCommonMsgPublishList`, `findCommonMsgPublishById`, `myNotReadCommonMsgCount` | 通知公告 |
| `arrangementservice` | `manualArrange/page`, `teachingProgress/progressQuery`, `teachingProgress/getPageContentById`, `teachingProgress/getAssistTeacher` | 课程查询 / 教学进度 |
| `workflow` | `approval/selectApproFlow` | 审批流查询 |

## Phase 2 优先实现（学生端只读高频）

### 1. 课表查询 `arrangementservice`
```
GET  /api/arrangementservice/timetable/course/{studentId}     # 学生课表
GET  /api/arrangementservice/timetable/teacher/{teacherCode}   # 教师课表
GET  /api/arrangementservice/timetable/teachers                 # 教师列表
GET  /api/arrangementservice/professionDir/getProDir            # 专业方向
GET  /api/arrangementservice/professioncampusnum/findCampus     # 校区列表
GET  /api/arrangementservice/teachingTask/page2                 # 教学任务
```

### 2. 学生信息 `studentservice`
```
POST /api/studentservice/studentInfo/findStuInfoList            # 学生信息查询
POST /api/studentservice/studentInfo/findAllStuInfoList         # 全部学生
GET  /api/studentservice/studentDetailInfo/stuDetailByClass     # 按班级查详情
POST /api/studentservice/studentEduBackg/findEduBackgroudList   # 教育背景
POST /api/studentservice/studentDic/findAllStuDicts             # 数据字典
POST /api/studentservice/teacherInfo/findTeacherInfoList        # 教师信息
POST /api/studentservice/advancedQuery/findResultList           # 高级查询
```

### 3. 选课查询 `electionservice`（只读）
```
POST /api/electionservice/elcCourseTake/page                    # 选课名单
POST /api/electionservice/electionRound/page                    # 选课轮次
POST /api/electionservice/elcLog/page                           # 选课日志
POST /api/electionservice/schoolExamArrange/schoolExamArrangeQuery  # 排考查询
POST /api/electionservice/undergraduateExamQuery/exportPrintingList # 考试安排
POST /api/electionservice/elcMutualApply/page                   # 跨学科选课申请列表（已实现）
GET  /api/electionservice/elcMutualCourses/findDept             # 跨学科选课院系列表（已实现）
```

### 4. 培养方案 `cultureservice`（只读）

**已实现（培养方案概览）：**
```
GET  /api/cultureservice/bclCulturePlan/findPlanCourseTab?studentID=... # 培养方案课程（按标签分组）
GET  /api/cultureservice/bclCulturePlan/statsCredit?studentID=...       # 学分统计
GET  /api/cultureservice/bclCulturePlan/queryCourseLabelTree?studentID=... # 课程标签树
POST /api/cultureservice/bclCourses/page                               # 课程库分页
```

**新增（培养方案详情页 `myBclCultureScheme`）：**
```
GET  /api/cultureservice/bclStudentCultureRel/queryStudentCultureScheme?stuid=...     # 学生方案关联
GET  /api/cultureservice/bclCultureScheme/findCultureSchemeById?id=...                # 方案元信息
GET  /api/cultureservice/bclCultureSchemeDetail/findCultScheDetailOrTemplateList?cultureId=... # 模板明细
GET  /api/cultureservice/bclCultureScheme/getSchemeSchoolTerm?id=...                  # 方案学期
GET  /api/cultureservice/bclCultureTemplate/coursesLabelList/{schemeId}?type=...      # 课程标签列表
GET  /api/cultureservice/bclCourseLabelRelation/list/{schemeId}?type=...              # 课程标签关联
```

**调用前置条件（从浏览器 Network 复现）：**
1. `POST /api/sessionservice/session/currentAuthId` — JSON body `{"authId": 9091}`（切换培养方案权限）
2. `PUT /api/sessionservice/session/setLanguage` — JSON body `{"language": "cn"}`
3. `POST /api/commonservice/dictionary/query` — JSON body `{"lang":"cn","type":"allChild","keys":["G_ZY","X_KSLX","X_PYCC","K_KCLB"],"authId":"9091"}`

### 5. 基础资源 `baseresservice`
```
POST /api/baseresservice/teacher/findTeacherList                # 教师列表
POST /api/baseresservice/classroomController/getClassroomInfoList # 教室列表
POST /api/baseresservice/studentCollege/list                    # 学院列表
POST /api/baseresservice/schoolCalendar/page                    # 校历分页
POST /api/baseresservice/classroomOccupation/getClassroomUsageRateByWeek  # 教室占用率
GET  /api/baseresservice/teacher/checkTeacherAuth               # 教师权限检查
GET  /api/baseresservice/schoolCalendar/nextTermCalendar        # 下学期校历
```

### 6. 公共数据 `commonservice`
```
POST /api/commonservice/dictionary/query                        # 字典查询
POST /api/commonservice/dictionary/getDictionaryForList          # 字典列表
POST /api/commonservice/campusProfession/findCampusProfessionList # 校区专业
POST /api/commonservice/workbenchMsg/queryAllWorkbenchMsg       # 工作台消息
GET  /api/commonservice/workbenchMsg/noReadCount                # 未读消息数
```

### 7. 工作台 `sessionservice`
```
GET  /api/sessionservice/session/queryQuickAccessMenu           # 快捷入口菜单
GET  /api/sessionservice/session/currentAuthId                  # 当前权限
POST /api/sessionservice/session/setLanguage                    # 语言设置
```

### 8. 教学进度 `arrangementservice` / `workflow`
```
POST /api/arrangementservice/teachingProgress/progressQuery        # 教学进度列表
POST /api/arrangementservice/teachingProgress/getPageContentById   # 教学进度详情
GET  /api/arrangementservice/teachingProgress/getAssistTeacher     # 助教信息
GET  /api/workflow/approval/selectApproFlow                        # 审批流查询
```
```
GET  /api/sessionservice/session/queryQuickAccessMenu           # 快捷入口菜单
GET  /api/sessionservice/session/currentAuthId                  # 当前权限
POST /api/sessionservice/session/setLanguage                    # 语言设置
```

## 管理端 API（后续阶段，含写入）

| 服务 | 端点数 | 说明 |
|------|--------|------|
| `userservice` | 61 | 用户/角色/部门/权限管理 |
| `cultureservice` | 216 | 培养方案完整 CRUD |
| `studentservice` | 135 | 学籍/注册/毕设全流程 |
| `electionservice` | 124 | 选课/排考完整管理 |
| `arrangementservice` | 54 | 排课完整流程 |
| `pgstudentservice` | 52 | 研究生管理 |
| `designservice` | 44 | 毕设管理 |
| `welcomeservice` | 30 | 迎新流程 |
| `workflow` | 14 | 审批流 |
| `lectureservice` | 10 | 讲座管理 |
| `externalexchangeservice` | 8 | 国际交流 |
| `innovativeservice` | 7 | 创新创业 |
| `practiceservice` | 6 | 实践教学 |
| `competitionservice` | 4 | 竞赛 |
| 其他 | ~30 | 学籍/成绩/大纲/推免等 |

## 系统级 API

| 服务 | 端点 | 说明 |
|------|------|------|
| `ssoservice` | `system/revoking` | 注销 |
| `transformer` | `picture/queryPicture` | 图片代理 |
| `logMessageService` | `generalBusinessLog/generalQueryListPage` | 业务日志 |

## 优先级建议

1. **课表** (`timetable/course`) — 学生最高频，"我下节什么课/在哪上"
2. **学生信息** (`studentInfo`) — "我的学籍信息/教育背景"
3. **选课信息** (`elcCourseTake`) — "我选了哪些课"
4. **培养方案** (`culturePlan`) — "我还差什么课没修"
5. **考试安排** (`undergraduateExamQuery`) — "什么时候考试/在哪考"
6. **数据字典** (`dictionary`) — 校区/学院/专业等基础数据查询
