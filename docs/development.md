# 开发经验沉淀

## 架构决策

本项目不是 XiaLing 通知镜像的复制品，也不是完整照搬网易云 API：

- 复用 XiaLing 对 IAM、RSA、MFA、SSO 和附件加密的协议分析。
- 采用 api-enhanced 的“一项能力一个 module、SDK 与 HTTP 同源”思想。
- 保留服务器单账号持久化 session，既不每次任务重新登录，也不支持调用方 Cookie。
- raw API 与 Agent 工具分层，避免为了易读而破坏上游保真数据。

## 获取接口的可靠方法

不要猜接口参数。优先流程：

1. 浏览器登录 `1.tongji.edu.cn`。
2. 打开 Network，启用 Preserve log。
3. 正常执行一次目标查询。
4. 过滤 Fetch/XHR，复制目标请求为 cURL。
5. 记录 method、URL、query、form body、前置权限调用和响应层级。
6. 使用当前 session 在 `httpx` 中复现，确认后再写 module。

Webpack 主文件经常只包含路由；具体页面请求可能位于动态 chunk。直接猜参数、盲目翻主 bundle 或重新模拟整个浏览器通常成本更高。

## 1 系统请求规律

- 业务 POST 多数是 form-encoded，而不是 JSON。
- 嵌套条件常以 `condition.trainingLevel` 形式展开。
- 详情 GET 经常携带毫秒时间戳避免缓存。
- 某些页面需要先调用 `currentAuthId` 和 `setLanguage`。
- `JSESSIONID` 和 `sessionid` 必须来自同一登录链。
- 401、403 或 `sessionid is not exist.` 都表示登录态不可继续使用。
- 部分接口 HTTP 200 仍可能返回业务失败，需要保留原始响应排查。

## 登录经验

IAM 登录不是普通用户名密码 POST：

1. 从 `loginIn` 跟随到 `ActionAuthChain`。
2. 解析 `authnLcKey`、`spAuthChainCode` 和 RSA JS。
3. 使用 JS 中公钥执行 PKCS1 v1.5 加密。
4. 加强认证时先发送验证码，再提交邮箱验证码。
5. 请求 `AuthnEngine` 并跟随 SSO。
6. 立即把 `ssologin` 的 `token/uid/ts` 交给 `session/login`。

`ssologin` token通常是一次性的，不能先在浏览器消费后再粘贴给服务。MFA 手动输入必须保持同一个进程和 cookie jar。

## 已知边界情况

### 当前教学周

`schoolCalendar/currentWeek` 可能因上游参数绑定返回 400。Agent 工具会根据当前学期开始日期按周一计算，并通过 `meta.source=calculated` 标记。

### 成绩排名

排名接口可能合法返回 `data: null`，常见原因包括账号权限、当前时间窗口或上游尚未生成排名。调用方不应无限重试。

### 课表和课程为空

暑假、寒假、学期未开始、培养方案尚未排课时都可能返回空列表。空列表不是 session 失效。

### 成绩字段

部分课程只提供等级制成绩，数字成绩或排名字段可能为空、负值或不存在。公开工具应同时保留原始代码和可读值，不自行推断成绩。

## API 调研记录

曾从工作台前端识别出约 29 个微服务和大量管理端端点。项目只保留学生账号可访问且明确只读的部分。

优先研究方向：

1. 学生课表、教师课表和教学任务。
2. 学生信息与教师信息。
3. 只读选课结果、轮次和考试安排。
4. 培养方案、课程标签和学分统计。
5. 教室、校历、节假日和基础字典。
6. 工作台消息、快捷入口和帮助中心。

不实现：

- AES 学号、附件路径加密和附件下载
- 选课、退课和申请写入
- 学籍、培养方案、排课等管理 CRUD
- 用户、角色和权限管理
- 工作流审批写入
- 研究生、毕设、迎新等管理端操作

## 模块和工具设计经验

- module 名称必须稳定，参数使用 Python snake_case，同时通过 alias 接受 HTTP camelCase。
- `/api/*` 不增加统一 envelope，避免改变上游结构。
- `/tools/tongji/*` 使用 `ToolSuccess`，自动解决学号、学期和周次依赖。
- 多步自然语言任务应下沉为一个聚合工具，而不是要求 Agent 串行调用多个 raw module。
- CLI 冷启动有固定成本；需要多次查询时启动常驻 HTTP 服务。
- `tongji call` 用于 raw 调试，`tongji tool` 用于单进程任务。

## 文档维护

`docs/api.md` 由 `scripts/generate_docs.py` 生成。module 或 tool 变化后必须重新生成，并由 CI 使用 `--check` 防止漂移。

本文件只记录仍然有效、可复用的开发结论，不保存临时抓包、真实账号数据或已失效的阶段计划。
