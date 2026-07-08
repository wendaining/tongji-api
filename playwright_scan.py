"""
Playwright 全站 API 扫描器。

用已有的 1.tongji.edu.cn session cookie 启动浏览器，
依次访问各个核心页面，捕获所有 /api/ 请求。
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# ── 页面清单 ────────────────────────────────────────
PAGES = [
    # (url, label, wait_selector, extra_wait_ms)
    ("/workbench", "工作台", "div#app", 5000),
    ("/myBclCultureScheme", "培养方案", None, 5000),
    ("/oldStysteMyGrades", "成绩", None, 5000),
    ("/studentInfo", "学生信息", None, 4000),
    ("/teachingEval", "评教", None, 4000),
    ("/examArrange", "考试安排", None, 4000),
    ("/tutorMeeting", "导师见面会", None, 4000),
    ("/courseSelect", "选课", None, 4000),
    ("/schoolTutorMeeting", "导师见面会(老)", None, 4000),
    ("/attendance", "考勤", None, 4000),
    ("/classroomApply", "教室申请", None, 4000),
    ("/lecture", "讲座", None, 4000),
    ("/practice", "实践", None, 4000),
    ("/competition", "竞赛", None, 4000),
    ("/innovation", "创新创业", None, 4000),
    ("/internationalExchange", "国际交流", None, 4000),
    ("/scholarship", "奖学金", None, 4000),
    ("/partyActivity", "党建", None, 4000),
    ("/volunteer", "志愿者", None, 4000),
    ("/certificate", "证明", None, 4000),
    ("/design", "毕设", None, 4000),
    ("/myTimetable", "我的课表", None, 4000),
    ("/messageCenter", "消息中心", None, 4000),
    ("/myCalendar", "我的校历", None, 4000),
    ("/studentRoll", "学籍", None, 4000),
    ("/selectCourse", "选课(旧)", None, 4000),
    ("/crossMajorCourse", "跨学科选课", None, 4000),
]

# ── Cookie 配置 ──────────────────────────────────────
# 从 SessionStore 读取
try:
    from tongji.core.config import get_settings
    from tongji.core.session_store import SessionStore
    settings = get_settings()
    store = SessionStore(settings.session_store_path)
    JSESSIONID = store.get_jsessionid()
    SESSIONID = store.get_sessionid()
    COOKIE = f"JSESSIONID={JSESSIONID}; sessionid={SESSIONID}; language=cn"
    print(f"[INFO] Session loaded: JSESSIONID={JSESSIONID[:20]}... sessionid={SESSIONID[:20]}...")
except Exception as e:
    print(f"[ERROR] Failed to load session: {e}")
    sys.exit(1)

BASE_URL = settings.normalized_one_base_url.rstrip("/")


async def main():
    from playwright.async_api import async_playwright

    all_apis = {}  # url -> list of requests
    seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # 设置 cookie
        await context.add_cookies([
            {"name": "JSESSIONID", "value": JSESSIONID, "domain": ".1.tongji.edu.cn", "path": "/"},
            {"name": "sessionid", "value": SESSIONID, "domain": ".1.tongji.edu.cn", "path": "/"},
            {"name": "language", "value": "cn", "domain": ".1.tongji.edu.cn", "path": "/"},
        ])
        print(f"[INFO] Cookies set. Starting scan...\n")

        for url_path, label, wait_sel, wait_ms in PAGES:
            full_url = f"{BASE_URL}{url_path}"
            page_apis = []

            async def on_request(request):
                url = request.url
                method = request.method
                # 只捕获 /api/ 请求
                if "/api/" not in url:
                    return
                # 跳过静态资源
                if any(x in url for x in [".js?", ".css?", ".ico", ".png", ".jpg", ".svg", ".woff"]):
                    return
                # 跳过 non-blocking 第三方
                if "1.tongji.edu.cn" not in url:
                    return

                headers = dict(request.headers)
                # 脱敏：不记录 cookie/x-token 值
                if "cookie" in headers:
                    headers["cookie"] = "[REDACTED]"
                if "x-token" in headers:
                    headers["x-token"] = "[REDACTED]"

                try:
                    post_data = await request.post_data() if method == "POST" else None
                    if post_data and len(post_data) > 500:
                        post_data = post_data[:500] + "...[truncated]"
                except:
                    post_data = None

                entry = {
                    "method": method,
                    "url": url,
                    "headers": {k: v for k, v in headers.items() if k.lower() not in ("cookie", "x-token", "authorization")},
                }
                if post_data:
                    entry["body"] = post_data

                key = f"{method} {url}"
                if key not in seen:
                    seen.add(key)
                    page_apis.append(entry)

            page = await context.new_page()
            page.on("request", on_request)

            try:
                print(f"  [{label}] {full_url} ...", end=" ", flush=True)
                resp = await page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
                status = resp.status if resp else "?"
                print(f"HTTP {status}", end="", flush=True)

                # 等页面加载和 API 请求完成
                if wait_sel:
                    try:
                        await page.wait_for_selector(wait_sel, timeout=5000)
                    except:
                        pass
                await page.wait_for_timeout(wait_ms)

                # 尝试点击"查看更多"之类触发更多请求
                try:
                    more_btns = await page.query_selector_all("button, a, span")
                    for btn in more_btns:
                        try:
                            text = await btn.inner_text()
                            if any(k in text for k in ["更多", "查看", "详情", "展开", "加载"]):
                                await btn.click()
                                await page.wait_for_timeout(2000)
                                break
                        except:
                            pass
                except:
                    pass

                print(f" → {len(page_apis)} API calls")
                all_apis[label] = page_apis

            except Exception as e:
                print(f"ERROR: {e}")
                all_apis[label] = [{"error": str(e)}]

            finally:
                await page.close()

        await browser.close()

    # ── 输出结果 ──────────────────────────────────────
    output = {
        "scan_time": datetime.now().isoformat(),
        "total_pages": len(PAGES),
        "total_api_calls": len(seen),
        "pages": {},
    }

    for label, apis in sorted(all_apis.items()):
        output["pages"][label] = {
            "count": len(apis),
            "endpoints": apis,
        }

    out_path = os.path.join(os.path.dirname(__file__), "scan_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"扫描完成！共访问 {len(PAGES)} 个页面，捕获 {len(seen)} 个唯一 API 请求")
    print(f"结果已保存至: {out_path}")

    # 按服务分组汇总
    by_service = {}
    for label, apis in sorted(all_apis.items()):
        for api in apis:
            if "error" in api:
                continue
            path = api["url"].split("/api/")[-1] if "/api/" in api["url"] else api["url"]
            svc = path.split("/")[0] if "/" in path else "unknown"
            by_service.setdefault(svc, set()).add(f"{api['method']} /api/{path}")

    print(f"\n按服务分组（{len(by_service)} 个微服务）:")
    for svc, eps in sorted(by_service.items()):
        print(f"\n  [{svc}] ({len(eps)} 端点):")
        for ep in sorted(eps)[:10]:
            print(f"    {ep}")
        if len(eps) > 10:
            print(f"    ... 还有 {len(eps)-10} 个")


if __name__ == "__main__":
    asyncio.run(main())
