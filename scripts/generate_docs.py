from __future__ import annotations

import argparse
from pathlib import Path

from tongji.modules import get_registry
from tongji.server import create_app

ROOT = Path(__file__).resolve().parents[1]

TOOL_CLI_NAMES = {
    "/tools/tongji/me": "me",
    "/tools/tongji/calendar/current-term": "current-term",
    "/tools/tongji/calendar/current-week": "current-week",
    "/tools/tongji/calendar": "calendar",
    "/tools/tongji/notices": "notices",
    "/tools/tongji/notices/unread-count": "unread-count",
    "/tools/tongji/notices/{notice_id}": "notice",
    "/tools/tongji/courses": "courses",
    "/tools/tongji/schedule/today": "schedule-today",
    "/tools/tongji/schedule/week": "schedule-week",
    "/tools/tongji/grades": "grades",
    "/tools/tongji/scores/rank": "score-rank",
    "/tools/tongji/exams": "exams",
}


def api_document() -> str:
    app = create_app()
    tool_routes = sorted(
        (
            route.path,
            next(iter(route.methods or {"GET"})),
            route.summary or route.name,
        )
        for route in app.routes
        if getattr(route, "path", "").startswith("/tools/tongji/")
    )
    lines = [
        "# API 文档",
        "",
        "本文件由 `scripts/generate_docs.py` 从 module registry 和 FastAPI 路由生成，"
        "请勿手工编辑。",
        "",
        "## 入口选择",
        "",
        "1. Agent 日常任务优先调用 `/tools/tongji/*`。",
        "2. 不启动服务时使用一次性的 `tongji tool` 聚合命令。",
        "3. `/api/*` 与 `tongji call` 仅用于 raw 数据和接口调试。",
        "",
        "常驻 HTTP 服务会复用进程、连接池和 session。连续执行多个 `tongji call` "
        "会重复冷启动，不适合 Agent 工作流。",
        "",
        "## Agent 工具",
        "",
        "| Method | HTTP Route | CLI Tool | Purpose |",
        "|---|---|---|---|",
    ]
    for path, method, summary in tool_routes:
        cli_name = TOOL_CLI_NAMES.get(path)
        cli = f"`tongji tool {cli_name}`" if cli_name else "-"
        lines.append(f"| `{method}` | `{path}` | {cli} | {summary} |")

    lines.extend(
        [
            "",
            "工具会自动补齐当前学生、当前学期和教学周。完整参数及响应模型以 `/openapi.json` 为准。",
            "",
            "### CLI 示例",
            "",
            "```bash",
            "uv run tongji tool notices --data '{\"page_size\":5}'",
            'uv run tongji tool notice --data \'{"notice_id":"..."}\'',
            "uv run tongji tool schedule-week",
            "uv run tongji tool grades",
            "uv run tongji tool score-rank",
            "```",
            "",
            "CLI tool 参数使用 snake_case。每条 `tongji tool` 命令只启动一次 Python。",
            "",
            "## Raw API Modules",
            "",
            "| Module | Method | Route | Description |",
            "|---|---|---|---|",
        ]
    )
    for module in get_registry().all():
        lines.append(
            f"| `{module.name}` | `{module.method}` | `{module.public_route}` | {module.summary} |"
        )

    lines.extend(
        [
            "",
            "raw 路由保留 1 系统原始字段和响应层级。CLI 调试示例：",
            "",
            "```bash",
            "uv run tongji modules",
            "uv run tongji call calendar_current_term",
            'uv run tongji call grades_list --data \'{"student_id":"student-demo"}\'',
            "```",
            "",
            "## 错误",
            "",
            "| Code | Meaning |",
            "|---|---|",
            "| `NO_SESSION` | 尚未保存 1 系统登录态 |",
            "| `SESSION_EXPIRED` | 登录态失效，`action_required=login` |",
            "| `UPSTREAM_ERROR` | 1 系统超时、不可达或返回 HTTP 错误 |",
            "| `VALIDATION_ERROR` | module 或 tool 参数不符合模型 |",
            "",
            "排名 `data: null`、课表空列表等属于合法业务结果，不属于上述错误。",
            "",
        ]
    )
    return "\n".join(lines)


def _write_or_check(path: Path, content: str, *, check: bool) -> bool:
    expected = content.rstrip() + "\n"
    if check:
        return path.exists() and path.read_text(encoding="utf-8") == expected
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    valid = _write_or_check(
        ROOT / "docs" / "api.md",
        api_document(),
        check=args.check,
    )
    if not valid:
        raise SystemExit("Generated documentation is out of date")


if __name__ == "__main__":
    main()
