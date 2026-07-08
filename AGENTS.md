# AGENTS.md

## 项目背景

`tongji-api` 是一个面向同济大学 `1.tongji.edu.cn` 系统的服务端 API 工具层。它为 AstrBot、agent、脚本以及其他自动化工具而构建，这些工具需要以结构化方式访问学校相关信息，如通知、日历数据、当前教学周和课程安排。

该项目并非前端网站。其主要职责是保留并文档化原始 1 系统 API 的调用规则，然后暴露一个小型的只读 HTTP 工具接口，供 agent 在理解用户通过 QQ、微信或其他聊天渠道发出的自然语言请求后调用。

## 核心方向

- 运行时流量必须指向 `https://1.tongji.edu.cn` 及其原始的 `/api/{service}/...` 端点。
- 不要针对同济开放平台 `https://api.tongji.edu.cn/v1/...` 进行开发。
- 不要引入开放平台的 `client_id`、`client_secret`、OAuth 作用域或 bearer token。
- 第一阶段使用持久化的 1 系统 `sessionid`；不存储密码和验证码。
- 第一阶段为只读：仅限会话、通知、日历和课程安排的查询。

## 预期流程

```text
QQ / 微信
  -> AstrBot / Agent
  -> tongji-api
  -> https://1.tongji.edu.cn/api/{service}/...
```

Agent 应调用此服务查询学校信息，然后将结构化响应以自然语言总结后返回给用户。

## 安全注意事项

- 将 `sessionid`、Cookie、SSO token 和授权头视为机密信息。
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
