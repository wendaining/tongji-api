# 如何新增 API

## 黄金法则

**不要猜。直接从浏览器 Network 面板拿真实请求。**

我们自己翻 `app.js`、用 Playwright 抓包、猜参数名，浪费了大量时间。事后发现，用户在浏览器里开 F12 看一眼真实请求，30 秒能搞定的事我们花了一小时。

## 三步流程

### 第一步：用户抓请求（30 秒）

1. 浏览器打开 1.tongji.edu.cn 目标页面（确保已登录）
2. `F12` → **Network** → 勾选 **Preserve log** → 清空
3. 正常使用页面功能（查询、翻页、筛选……）
4. 在 Network 面板点 **Fetch/XHR** 过滤器，只显示 API 请求
5. 找到目标请求 → 右键 → **Copy** → **Copy as cURL**
6. 把 curl 命令发给开发者

> **只发目标请求的 curl 即可。** 如果同一页面有多个相关请求（如 `queryCourseTag` + `getMyGrades`），可以都发过来。

### 第二步：开发者写代码（5 分钟）

以下以"成绩查询"为例：

**① 探测数据结构**

拿到 curl 后，先用 Python 跑一遍看返回格式：

```python
import json, httpx
# 从 curl 中提取：URL、method、params、data、headers

with open('data/session.json') as f:
    s = json.load(f)
cookie = f"JSESSIONID={s['jsessionid']}; sessionid={s['sessionid']}"
h = {'Cookie': cookie, 'X-Token': s['sessionid'], 'Accept': 'application/json'}

c = httpx.Client(timeout=15)
r = c.get('https://1.tongji.edu.cn/api/...', headers=h, params={...})
print(json.dumps(r.json(), ensure_ascii=False, indent=2)[:1000])
```

**② 写 service**

```
tongji/core/services/<name>.py
```

每个函数封装一个 API 调用，遵循 xialing 规范：form-encoded POST、GET 加 `_t` 时间戳。

```python
async def get_my_grades(client: RawOneClient, *, student_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/scoremanagementservice/scoreGrades/getMyGrades",
        params={"studentId": student_id},
    )
```

**③ 写翻译映射（dict.py）**

```python
GRADE_COURSE_FIELDS = [
    ("courseName", "课程名称"),
    ("gradePoint", "绩点"),
    ...
]

def translate_grade_course(raw: dict) -> dict:
    return {label: raw.get(code) for code, label in GRADE_COURSE_FIELDS}
```

如果有 I18n 字段（如 `sexI18n`），优先用 I18n。

**④ 写 CLI 命令**

在 `tongji/cli.py` 中：
- 写 `cmd_xxx()` 函数
- 加 `subs.add_parser(...)`
- 加 `elif args.command == "xxx": asyncio.run(cmd_xxx())`

**⑤ 写 HTTP 端点**

在 `tongji/server.py` 中加一个 `@app.get("/xxx")` 路由，支持 `?translated=1` 参数。

### 第三步：测试和提交

```bash
uv run pytest tests/ -q
uv run python -m tongji <新命令>
git add ... && git commit -m "feat(...): ..." && git push
```

## 教训：什么方法无效

### ❌ 翻 app.js 主文件

`app.3cadb0a2dbdf7d015f4d.js` 只包含主路由和公共 API。动态加载页面（如 `/oldStysteMyGrades`）的 API 调用在 webpack chunk 文件里，这些 chunk 文件名带 hash，无法直接定位。

### ❌ Playwright 自动抓包

Cookie 安全策略导致 Playwright 浏览器的 session 无法被 SPA 识别，页面始终跳到 IAM 登录。命令行 httpx 直接发请求反而没问题。

### ❌ 猜 API 参数名

培养方案 `findMadePlanCourseList` 需要 `schemeID` 参数，我们猜不到它的值，拖了很久。看 curl 命令一目了然。

## 已知有效的方法

| 方法 | 适用场景 |
|------|---------|
| **F12 curl** | 最佳通用方法，所有页面适用 |
| app.js 搜索 | 适合主路由中已暴露的 API（如 timetable/course、findPlanCourseTab） |
| api.tongji.edu.cn 文档 | 开放平台 API（需要 OAuth 鉴权，与 1 系统 session 不互通） |
| Playwright | 仅当需要模拟用户交互（填表单、点按钮）时考虑 |

## 新增 API 检查清单

- [ ] 在 `tongji/core/services/` 添加 service 文件
- [ ] 遵循 form-encoded POST / GET+`_t` 规范
- [ ] 在 `tongji/core/dict.py` 添加翻译函数
- [ ] 在 `tongji/cli.py` 注册命令
- [ ] 在 `tongji/server.py` 注册端点（支持 `?translated=1`）
- [ ] `uv run pytest tests/ -q` 通过
- [ ] `uv run python -m tongji <cmd>` 能跑
- [ ] 更新 `docs/agent-tools.md` 的意图映射表
- [ ] 更新 `docs/1-tongji-api-catalog.md` 标记已实现
- [ ] Git commit 采用双段式（英文标题 + 中文详细说明）
