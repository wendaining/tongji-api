# AGENTS.md

## 项目背景

`tongji-api` 是一个面向同济大学 `1.tongji.edu.cn` 系统的服务端 API 工具层。它为 AstrBot、agent、脚本以及其他自动化工具而构建，这些工具需要以结构化方式访问学校相关信息，如通知、日历数据、当前教学周和课程安排。

该项目并非前端网站。其主要职责是保留并文档化原始 1 系统 API 的调用规则，然后暴露一个小型的只读 HTTP 工具接口，供 agent 在理解用户通过 QQ、微信或其他聊天渠道发出的自然语言请求后调用。

## 核心方向

- 运行时流量必须指向 `https://1.tongji.edu.cn` 及其原始的 `/api/{service}/...` 端点。
- 不要针对同济开放平台 `https://api.tongji.edu.cn/v1/...` 进行开发。
- 不要引入开放平台的 `client_id`、`client_secret`、OAuth 作用域或 bearer token。
- 第一阶段按 XiaLing233 的状态机流程程序化登录 1 系统。
- IAM 学号和密码通过环境变量或本地配置提供；不得写入日志或 session 文件。
- MFA 支持 IMAP 自动读取或同进程手动输入，不保存验证码。
- 登录成功后持久化 1 系统的 `JSESSIONID` 和 `sessionid`。
- 第一阶段为只读：仅限会话、通知、日历和课程安排的查询。

## 接口调用规范（XiaLing233 参考实现）

本项目代码严格对齐 XiaLing233 / fetch-1-dot-tongji 的调用方式。
参考仓库：https://github.com/XiaLing233/fetch-1-dot-tongji

### 登录流程

登录模块完整复刻 `crawler/auth/loginout.py` 的 SSO 状态机流程：

1. GET `https://1.tongji.edu.cn/api/ssoservice/system/loginIn`（自动跟随重定向到 IAM 登录页）
2. 从页面提取 `authnLcKey`、RSA 脚本地址、`spAuthChainCode`
3. RSA 加密密码（PKCS1_v1_5 + Base64）
4. POST `ActionAuthChain`（form-encoded）提交凭据
5. 如需 MFA：POST `sendCheckCode.do` 发送邮箱验证码 → 用户手动提交
6. POST `AuthnEngine` 换取 Location
7. 跟随重定向到 `ssologin`，解析 token/uid/ts
8. POST `session/login` 换取 `sessionid`

任何时候修改登录相关代码，必须先对照 XiaLing233 的 `loginout.py` 和 `encrypt.py`。

### HTTP 客户端统一规范

所有对 `1.tongji.edu.cn` 的请求必须通过 `RawOneClient` 发出，并遵守以下规范：

**请求头**（全部使用浏览器风格，不暴露自建服务特征）：
```text
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Accept-Encoding: gzip, deflate, br, zstd
X-Token: <sessionid>
Cookie: JSESSIONID=<jsessionid>; sessionid=<sessionid>
```

**POST 请求体**：全部使用 `application/x-www-form-urlencoded`（form-encoded），不使用 JSON。这与 XiaLing233 的 `data=dict` + `urlencode()` 一致。

```python
# 正确：form-encoded
client.request("POST", "/api/...", data={"pageNum_": 1, "pageSize_": 20})

# 错误：不要绕过 RawOneClient 发送 JSON body
```

嵌套字段用 Spring MVC 点号扁平化：
```python
{"condition.trainingLevel": "", "condition.campus": ""}
```

**GET 请求**：查询参数使用 `params=` 传递，必要时附加 `t` 缓存时间戳（毫秒级 Unix 时间）：
```python
client.request("GET", "/api/.../findById", params={"id": id, "t": str(int(time.time() * 1000))})
```

### Cookie 与 session 管理

- `SessionStore` 持久化 `JSESSIONID` 和 `sessionid`，从 cookie jar 自动提取
- `get_cookie_header()` 构造完整的 Cookie 请求头
- 业务 API 调用自动注入 `X-Token` 和 `Cookie`
- Session 失效检测：状态码 401/403 或响应包含 `sessionid is not exist`

### 不在日志中打印的敏感字段

`sessionid`、`JSESSIONID`、`Cookie`、`X-Token`、`Authorization`、`token`、`j_password`、`sms_checkcode`、IAM 密码。

### 未实现 / 后续阶段

- AES 文件路径加密（`encrypt.py` 的 `getAESKeyAndIV` / `encryptFilePath`）
- 退出登录（`loginout.py` 的 `logout`）
- `currentWeek` 上游接口的参数绑定仍待确认，Agent 工具提供校历计算回退。

## 预期流程

```text
QQ / 微信
  -> AstrBot / Agent
  -> tongji-api
  -> https://1.tongji.edu.cn/api/{service}/...
```

Agent 应调用此服务查询学校信息，然后将结构化响应以自然语言总结后返回给用户。

## 安全注意事项

- 将 IAM 密码、验证码、`sessionid`、Cookie、SSO token 和授权头视为机密信息。
- 不要在日志、示例、测试或文档中打印机密信息。
- 第一阶段不包含写入 API、选课 API 和管理 API。
- 默认部署应为本地、私有或由服务 token 保护。

## Git 提交规范

使用双段式提交信息。

第一行必须使用英文 Conventional Commits 格式：

<type>(optional scope): <short English summary>

然后空一行。

空行之后，用中文撰写详细的提交说明。

允许的类型：

* feat：新功能
* fix：Bug 修复
* docs：仅文档变更
* style：不影响代码行为的格式变更
* refactor：既非修复也非功能的代码变更
* perf：性能改进
* test：添加或更新测试
* build：构建系统、依赖、包管理、Docker 或 uv 相关变更
* ci：CI/CD 变更，包括 GitHub Actions
* chore：不归入其他类型的维护任务
* revert：回退之前的提交

第一行规则：

* 仅使用英文。
* 保持简洁，尽量控制在 72 个字符以内。
* 类型使用小写。
* 使用祈使语气，如 "add"、"fix"、"update"、"remove"。
* 必要时使用 scope（作用域），例如：

  * feat(bot): add /status command
  * fix(parser): handle merged QQ chat records
  * ci(deploy): add SSH deployment workflow
  * build(docker): add production Dockerfile

中文详细说明规则：

* 使用中文。
* 说明变更内容。
* 必要时说明变更原因。
* 提及受影响的重要模块、文件或行为。
* 如有破坏性变更、迁移步骤或部署注意事项，请注明。
* 不要写模糊的描述，如"修改了一些代码"或"优化项目"。
* 保持详细说明简洁，通常 2~5 条要点。

推荐格式：

<type>(optional scope): <short English summary>

* 做了什么：……
* 为什么：……
* 影响范围：……
* 注意事项：……

示例：

feat(parser): support merged QQ chat records

* 做了什么：新增对 QQ 合并聊天记录的解析逻辑，支持从转发消息中提取文本内容。
* 为什么：方便用户直接发送合并聊天记录，让 bot 能够读取并整理上下文。
* 影响范围：主要影响聊天记录解析模块和消息处理流程。
* 注意事项：后续需要补充更多真实 QQ 消息格式的测试样例。

ci(deploy): add GitHub Actions SSH deployment

* 做了什么：新增 GitHub Actions 工作流，通过 SSH 登录服务器并自动拉取、构建、重启服务。
* 为什么：减少手动部署步骤，保证每次推送后都能以一致流程发布。
* 影响范围：影响部署流程、服务器目录结构和环境变量配置。
* 注意事项：需要在 GitHub Secrets 中配置服务器地址、用户名、SSH 私钥和部署路径。

build(docker): add production Docker setup

* 做了什么：新增 Dockerfile 和 docker-compose.yml，用于容器化运行 QQ Bot。
* 为什么：方便在服务器上稳定部署，并减少本地环境和服务器环境差异。
* 影响范围：影响项目启动方式、依赖安装方式和生产环境运行流程。
* 注意事项：部署前需要确认 .env 文件和挂载目录配置正确。
