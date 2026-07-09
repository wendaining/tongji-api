# tongji-api

`tongji-api` 是一个同济大学 `1.tongji.edu.cn` 系统的 CLI + HTTP 工具包，用于 AstrBot、agent 和其他自动化工具。

架构参考 [NeteaseCloudMusicApiEnhanced](https://github.com/neteasecloudmusicapienhanced/api-enhanced)：核心逻辑 (`core/`) 由 CLI 和 HTTP server 共享。

目前项目仍处于第一阶段：

- 服务端按 [XiaLing233 的流程程序化](https://blog.xialing.icu/2025/01/tongji-bulletin-mirror/)完成同济 IAM 登录
- 通过环境变量提供 IAM 学号和密码；密码只从配置读取，不写入 session 文件
- 如果触发邮箱 MFA，自动通过 IMAP（QQ 邮箱）读取验证码
- 将 `JSESSIONID` 和 `sessionid` 持久化到本地 JSON 文件
- 提供只读的会话、学生信息、通知、日历和课程 API
- 无缓存、无限流、无写入 API
- 所有 POST/PUT 请求使用 `application/x-www-form-urlencoded`（对齐 XiaLing233）
- 约 45 个 API 端点已实现（基于 2026-07-09 CDP 浏览器全站扫描）

## 快速开始

```powershell
uv sync --extra dev
Copy-Item .env.example .env
```

编辑 `.env` 文件并设置：

```text
TJ_IAM_USERNAME=学号
TJ_IAM_PASSWORD=密码
TJ_IMAP_EMAIL=邮箱
TJ_IMAP_GRANTCODE=邮箱授权码
```

## 使用方式

### CLI 模式（推荐日常使用）

```powershell
# 登录
uv run python -m tongji login

# 学生信息
uv run python -m tongji me              # 当前学生
uv run python -m tongji stations        # 生源地列表

# 通知
uv run python -m tongji notices         # 通知列表
uv run python -m tongji notice <id>     # 通知详情

# 课程 & 课表
uv run python -m tongji courses         # 课程查询
uv run python -m tongji timetable       # 我的课表
uv run python -m tongji major-timetable # 专业课表

# 校历
uv run python -m tongji calendar list          # 校历列表
uv run python -m tongji calendar current-term  # 当前学期
uv run python -m tongji calendar current-week  # 当前周次

# 成绩
uv run python -m tongji scores           # 成绩单
uv run python -m tongji scores --tags    # 课程分类标签
uv run python -m tongji scores --rank    # 绩点排名

# 考试
uv run python -m tongji exams            # 考试安排（含分级考试）

# 培养方案
uv run python -m tongji plan             # 学分概况
uv run python -m tongji plan-detail      # 培养方案详情

# 选课 & 跨学科
uv run python -m tongji cross-courses    # 跨学科选课申请

# 教学进度
uv run python -m tongji teaching-progress
uv run python -m tongji progress-detail <id>

# 导师见面会
uv run python -m tongji tutor-meetings

# 教室资源
uv run python -m tongji classroom        # 教学楼列表

# 查看所有命令
uv run python -m tongji --help
```

### HTTP 服务模式（给 AstrBot 等调用）

```powershell
uv run python -m tongji serve --port 8000
```

端点：

```
GET  /healthz
GET  /session/ping
GET  /session/me

# 学生信息
GET  /students/me
GET  /students
GET  /students/tabs                  # 可见标签
GET  /students/stations?translated   # 生源地列表
GET  /students/status?studentId=&translated
GET  /students/activation?studentId=
POST /students/picture?studentIds=

# 通知
GET  /notices
GET  /notices/{id}

# 课程 & 课表
GET  /courses
GET  /timetable?studentId=&calendarId=
GET  /timetable/major?code=&grade=&calendarId=

# 校历
GET  /calendar/list
GET  /calendar/current-term
GET  /calendar/current-week
GET  /calendar/{calendar_id}
GET  /calendar/professional-work?translated
GET  /calendar/holidays?year=&translated

# 成绩
GET  /grades?studentId=&translated
GET  /grades/tags?studentId=&translated       # 课程分类标签
GET  /scores/rank?studentId=&translated       # 绩点排名

# 考试
GET  /exams?translated            # 考试安排
GET  /exams/info                  # 考试元数据
GET  /exams/dictionary?keys=

# 培养方案
GET  /plan/credits?studentId=
GET  /plan/courses?studentId=
GET  /culture/strength-class      # 强化班状态
GET  /culture/strength-class-info?type=

# 选课
GET  /cross-courses/apply?studentId=&calendarId=
GET  /elections/rounds?projectId=
GET  /elections/apply-list?calendarId=

# 教学进度
GET  /teaching-progress?calendarId=
GET  /teaching-progress/{id}

# 导师见面会
GET  /tutor-meetings?searchText=

# 考勤
GET  /attendance/class-dates?yearMonth=
GET  /attendance/class-content?chooseDate=

# 教室资源
GET  /classroom/towers?translated
GET  /classroom/usage-report?calendarId=

# 帮助中心
GET  /help/articles
GET  /help/groups
GET  /help/my
```

无需 Bearer token——1 系统 session 即鉴权。

### Docker（可选）

```powershell
docker build -t tongji-api .
docker run -p 8000:8000 --env-file .env tongji-api
```

## 开发

```powershell
uv run pytest
uv run ruff check .
```
