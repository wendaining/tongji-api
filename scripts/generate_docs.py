from __future__ import annotations

import argparse
from pathlib import Path

from tongji.modules import get_registry
from tongji.server import create_app

ROOT = Path(__file__).resolve().parents[1]


def api_reference() -> str:
    lines = [
        "# Raw API Reference",
        "",
        "本文件由 `scripts/generate_docs.py` 从 module registry 生成，请勿手工编辑。",
        "",
        "| Module | Method | Route | Description |",
        "|---|---|---|---|",
    ]
    for module in get_registry().all():
        lines.append(
            f"| `{module.name}` | `{module.method}` | `{module.public_route}` | {module.summary} |"
        )
    lines.extend(
        [
            "",
            "所有 raw 路由保留 1 系统原始字段和响应层级。"
            "参数定义及响应 schema 以 `/openapi.json` 为准。",
            "",
        ]
    )
    return "\n".join(lines)


def agent_tools() -> str:
    app = create_app()
    routes = sorted(
        (
            route.path,
            next(iter(route.methods or {"GET"})),
            route.summary or route.name,
        )
        for route in app.routes
        if getattr(route, "path", "").startswith("/tools/tongji/")
    )
    lines = [
        "# Agent / AstrBot Tools",
        "",
        "本文件由 `scripts/generate_docs.py` 生成。Agent 应优先调用本页工具，"
        "不要直接拼接 1 系统上游参数。",
        "",
        "| Method | Route | Purpose |",
        "|---|---|---|",
    ]
    for path, method, summary in routes:
        lines.append(f"| `{method}` | `{path}` | {summary} |")
    lines.extend(
        [
            "",
            "## 调用规则",
            "",
            "- 通知、公告、教务消息：调用 `/tools/tongji/notices`，追问详情时再调用详情。",
            "- 当前周、学期、校历：调用 `/tools/tongji/calendar/*`。",
            "- 今天或本周课程：调用 `/tools/tongji/schedule/today` 或 `schedule/week`。",
            "- 成绩与考试：分别调用 `/tools/tongji/grades` 和 `/tools/tongji/exams`。",
            "- `SESSION_EXPIRED` 且 `action_required=login` 时，提示管理员重新登录。",
            "- 默认只调用只读工具，不向聊天用户索要 IAM 密码、验证码或 Cookie。",
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
    results = [
        _write_or_check(
            ROOT / "docs" / "api-reference.md",
            api_reference(),
            check=args.check,
        ),
        _write_or_check(
            ROOT / "docs" / "agent-tools.md",
            agent_tools(),
            check=args.check,
        ),
    ]
    if not all(results):
        raise SystemExit("Generated documentation is out of date")


if __name__ == "__main__":
    main()
