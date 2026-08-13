#!/usr/bin/env python3
"""
调度脚本：执行搜索任务 → 生成 Markdown + HTML 报告 → 调用飞书推送
"""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from xianyu_search import run_batch

OUTPUT_DIR = SKILL_DIR.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BOM_PATH = SKILL_DIR / "bom_tasks.json"
TASKS_PATH = OUTPUT_DIR / "search_results.json"
REPORT_MD = OUTPUT_DIR / "bom_hunt_report.md"
REPORT_HTML = OUTPUT_DIR / "bom_hunt_report.html"


def load_bom() -> dict:
    return json.loads(BOM_PATH.read_text(encoding="utf-8"))


def render_md(bom: dict, results: list) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    has_cookie = any(r.get("status") not in ("suggestion",) for r in results)

    # 统计
    total = len(results)
    matched = sum(1 for r in results if r.get("items"))
    login_blocked = sum(1 for r in results if r.get("status") == "login_required")
    exceptions = sum(1 for r in results if r.get("status") == "exception")
    suggestions = sum(1 for r in results if r.get("status") == "suggestion")

    lines = []
    lines.append(f"# 🚤 桨板跟拍船 BOM 闲鱼采购日报 ({ts})")
    lines.append("")
    lines.append(f"**项目**：{bom['project']}  ")
    lines.append(f"**总任务数**：{total}  ")
    lines.append(f"**模式**：{'🟢 Cookie已注入（自动搜索）' if has_cookie else '🟡 无Cookie（搜索建议模式）'}  ")
    lines.append("")
    lines.append("## 📊 搜索概览")
    lines.append("")
    lines.append("| 指标 | 数量 |")
    lines.append("|------|------|")
    lines.append(f"| 匹配到商品的任务 | {matched} |")
    lines.append(f"| 被登录墙挡住 | {login_blocked} |")
    lines.append(f"| 异常/超时 | {exceptions} |")
    lines.append(f"| 搜索建议（无cookie） | {suggestions} |")
    lines.append("")
    if not has_cookie:
        lines.append("> 💡 **提示**：当前为「搜索建议模式」。如需 Agent 全自动抓取商品，请按以下步骤提供闲鱼 cookie：")
        lines.append("> ")
        lines.append("> 1. 在本地浏览器登录 `goofish.com`（网页版）")
        lines.append("> 2. 打开 DevTools → Application → Cookies → 复制所有 `.goofish.com` 域名下的 cookie")
        lines.append("> 3. 另存为 JSON 数组格式 `[{name, value, domain, path}]`，上传到 `~/.hermes/cookies/xianyu.json`")
        lines.append("> 4. 重跑 `python3 run_pipeline.py` 即可全自动抓取")
        lines.append("")

    # 分组
    by_cat = {}
    for r in results:
        t = next((x for x in bom["tasks"] if x["id"] == r["id"]), {})
        cat = t.get("category", "其他")
        by_cat.setdefault(cat, []).append((t, r))

    for cat in ["船体结构", "动力推进", "控制电子", "拍摄与云台", "电池与电源", "防水与密封", "工具与耗材"]:
        if cat not in by_cat:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        for t, r in by_cat[cat]:
            plan_tag = {"A": "🅰️方案A", "B": "🅱️方案B", "both": "🔗共用"}[t.get("plan", "?")]
            ess_tag = "🔴必备" if t.get("essential") else "⚪可选"
            lines.append(f"### {r['id']} {t['name']}  {plan_tag} {ess_tag}")
            lines.append("")
            pr_lo, pr_hi = t.get("price_range", [0, 0])
            lines.append(f"- 💰 价格区间：¥{pr_lo} - ¥{pr_hi}")
            lines.append(f"- 🔍 关键词：`{' / '.join(t.get('keywords', [])[:4])}`")
            lines.append(f"- 🔗 闲鱼链接：[直接搜索]({r.get('search_url', 'https://www.goofish.com/search?q=' + t.get('keywords', [''])[0])})")
            lines.append("")

            if r.get("items"):
                lines.append(f"**找到 {len(r['items'])} 个匹配商品**")
                lines.append("")
                lines.append("| 评分 | 价格 | 标题 | 链接 |")
                lines.append("|------|------|------|------|")
                for it in r["items"][:5]:
                    title = (it.get("title") or "—")[:50]
                    price = f"¥{it['price']:.0f}" if it.get("price") else "—"
                    score = it.get("score", 0)
                    href = it.get("href", "#")
                    lines.append(f"| {score:.2f} | {price} | {title} | [打开]({href}) |")
                lines.append("")
            elif r.get("status") == "login_required":
                lines.append("⚠️ **被登录墙挡住**：未登录态下闲鱼不展示搜索结果。请提供 cookie 启用全自动模式。")
                lines.append("")
            elif r.get("status") == "no_match":
                lines.append(f"ℹ️ 页面已加载但未匹配到关键词（{r.get('error','')}）")
                lines.append("")
            elif r.get("status") == "suggestion":
                lines.append("📋 **建议清单**：大王可点击上方闲鱼链接手动浏览，或提供 cookie 启用自动抓取。")
                lines.append("")

    lines.append("---")
    lines.append(f"*本报告由 `xianyu-bom-hunter` skill 自动生成于 {ts}*")
    return "\n".join(lines)


def render_html(md_content: str) -> str:
    """简单 Markdown → HTML 包装（实际推送仍以 Markdown 为主，HTML 用于可选附件）"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>BOM 闲鱼采购日报</title>
<style>
body {{ font-family: 'Inter', 'Noto Sans SC', sans-serif; max-width: 920px; margin: 24px auto; padding: 0 16px; background: #0f172a; color: #e2e8f0; line-height: 1.7; }}
h1 {{ color: #38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 8px; }}
h2 {{ color: #22d3ee; margin-top: 32px; }}
h3 {{ color: #f1f5f9; background: rgba(56,189,248,0.08); padding: 8px 12px; border-radius: 8px; border-left: 4px solid #0ea5e9; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid rgba(255,255,255,0.1); padding: 8px; text-align: left; }}
th {{ background: rgba(56,189,248,0.15); }}
a {{ color: #38bdf8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
blockquote {{ border-left: 4px solid #f59e0b; padding: 8px 16px; background: rgba(245,158,11,0.06); margin: 12px 0; }}
code {{ background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
</style>
</head>
<body>
<pre style="white-space: pre-wrap; font-family: inherit;">{md_content.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')}</pre>
</body>
</html>"""


def main():
    bom = load_bom()
    tasks = bom["tasks"]
    print(f"[pipeline] {len(tasks)} tasks loaded")
    print(f"[pipeline] running search...")
    results = run_batch(tasks)
    TASKS_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_md(bom, results)
    REPORT_MD.write_text(md, encoding="utf-8")
    REPORT_HTML.write_text(render_html(md), encoding="utf-8")
    print(f"[pipeline] markdown → {REPORT_MD}")
    print(f"[pipeline] html → {REPORT_HTML}")

    # 自动推送飞书
    if "--no-push" not in sys.argv:
        try:
            from feishu_push import push_report
            push_report(md, REPORT_HTML)
        except Exception as e:
            print(f"[pipeline] push failed: {e}")

    # 自动同步到飞书多维表格
    if "--no-bitable" not in sys.argv:
        try:
            from feishu_bitable import build_records, push_to_bitable
            records = build_records(bom["tasks"], results)
            meta = push_to_bitable(records)
            print(f"[pipeline] bitable synced: {meta['url']}")
        except Exception as e:
            print(f"[pipeline] bitable sync failed: {e}")


if __name__ == "__main__":
    main()