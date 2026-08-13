#!/usr/bin/env python3
"""
闲鱼搜索爬虫 - 桨板跟拍船 BOM 采购 Agent 核心
- 有 cookie：Playwright 注入 → 真实搜索 → 提取商品卡片
- 无 cookie：返回"今日搜索建议清单"，附带跳转链接，大王自行点击

支持来源：
  - 主源：闲鱼 goofish.com（需登录 cookie）
  - 备源：搜索建议模式（无cookie时生成可点击链接）
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth

CHROME = "/home/ubuntu/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
COOKIE_PATH = Path.home() / ".hermes" / "cookies" / "xianyu.json"

SEARCH_URL = "https://www.goofish.com/search?q={q}"


def _load_cookies() -> Optional[List[Dict[str, Any]]]:
    """读取大王导出的闲鱼 cookie（标准 JSON 数组格式，name/value/domain/path 字段）"""
    if not COOKIE_PATH.exists():
        return None
    try:
        cookies = json.loads(COOKIE_PATH.read_text(encoding="utf-8"))
        if isinstance(cookies, list) and cookies:
            return cookies
    except Exception as e:
        print(f"[search] cookie parse error: {e}")
    return None


def _build_stealth() -> Stealth:
    return Stealth(
        navigator_user_agent=True,
        navigator_user_agent_override=UA,
        navigator_languages_override=("zh-CN", "zh"),
        navigator_platform_override="MacIntel",
        init_scripts_only=True,
    )


def _build_context(p, cookies: Optional[List[Dict[str, Any]]]) -> BrowserContext:
    ctx = p.chromium.launch(
        headless=True, executable_path=CHROME, args=["--no-sandbox"]
    ).new_context(
        viewport={"width": 1440, "height": 900},
        user_agent=UA,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    if cookies:
        try:
            cleaned = []
            for c in cookies:
                cleaned.append({
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c.get("domain", ".goofish.com"),
                    "path": c.get("path", "/"),
                })
            ctx.add_cookies(cleaned)
            print(f"[search] injected {len(cleaned)} cookies")
        except Exception as e:
            print(f"[search] cookie inject error: {e}")
    _build_stealth().apply_stealth_sync(ctx)
    return ctx


def _check_login_wall(page: Page) -> bool:
    """检测是否被登录墙挡住（iframe 加载 login.htm）"""
    try:
        if page.locator("iframe#baxia-dialog-content").count() > 0:
            return True
        if page.locator("iframe[src*='passport.goofish.com']").count() > 0:
            return True
        if "哎哟喂" in page.content():
            return True
    except Exception:
        pass
    return False


def _extract_items(page: Page) -> List[Dict[str, Any]]:
    """单次 evaluate 提取所有商品卡片（含列表页就能拿到的卖家信息）

    每张卡返回：
      href, title, price, seller (昵称/地区), seller_info {credit_level, is_free_ship, condition}
    """
    try:
        result = page.evaluate(r"""() => {
            const cards = document.querySelectorAll('a[class*="feeds-item-wrap"]');
            const out = [];
            for (let i = 0; i < Math.min(cards.length, 20); i++) {
                const card = cards[i];
                try {
                    const href = card.getAttribute('href') || '';
                    if (href.indexOf('item?id') < 0 && href.indexOf('goofish.com/item') < 0) continue;
                    const titleEl = card.querySelector('[class*="main-title"]');
                    const title = titleEl ? (titleEl.textContent || '').trim() : '';
                    const numEl = card.querySelector('[class*="number--"]');
                    const decEl = card.querySelector('[class*="decimal--"]');
                    let price = null;
                    if (numEl) {
                        const n = parseFloat((numEl.textContent || '0').trim());
                        let d = 0;
                        if (decEl) {
                            const txt = (decEl.textContent || '0').replace(/[^0-9]/g, '');
                            d = txt ? parseFloat('0.' + txt) : 0;
                        }
                        price = n + d;
                    }
                    const sellerEl = card.querySelector('[class*="seller-text--"]');
                    const seller = sellerEl ? (sellerEl.textContent || '').trim() : '';
                    // 卖家信息（列表页直接抓）
                    const cardHtml = card.outerHTML;
                    const cardText = card.innerText || '';
                    // 信用等级
                    let credit_level = null;
                    const cm = cardHtml.match(/credit-container[^>]*>[\s\S]*?title="卖家信用(极好|优秀|良好|较差)"/);
                    if (cm) credit_level = cm[1];
                    // 包邮
                    const is_free_ship = cardText.indexOf('包邮') >= 0;
                    // 成色
                    let condition = null;
                    if (cardText.indexOf('几乎全新') >= 0) condition = '几乎全新';
                    else if (cardText.indexOf('全新') >= 0) condition = '全新';
                    else if (/9\s*成\s*新|9成新/.test(cardText)) condition = '9成新';
                    // 想要数（列表页卡片右下显示）
                    let want_count = null;
                    const wm = cardText.match(/(\d+)\s*人想要/);
                    if (wm) want_count = parseInt(wm[1]);
                    out.push({
                        href: href.startsWith('http') ? href : (href.startsWith('//') ? 'https:' + href : 'https://www.goofish.com' + href),
                        title: title,
                        price: price,
                        seller: seller,
                        seller_info: {
                            credit_level: credit_level,
                            is_free_ship: is_free_ship,
                            condition: condition,
                            want_count: want_count,
                        },
                    });
                } catch(e) {}
            }
            return out;
        }""", )
        out = []
        for it in (result or []):
            href = it.get("href", "")
            if not href.startswith("http"):
                href = "https://www.goofish.com" + href
            out.append({
                "href": href,
                "title": (it.get("title") or "")[:120],
                "price": it.get("price"),
                "seller": it.get("seller", ""),
                "snippet": (it.get("title") or "")[:200],
                "seller_info": it.get("seller_info") or {},  # 修复：保留列表页拿到的卖家信息
            })
        return out
    except Exception as e:
        return []


def _check_login_wall(page: Page) -> bool:
    """检测登录墙"""
    try:
        if page.locator("iframe#baxia-dialog-content").count() > 0:
            return True
    except Exception:
        pass
    return False


def _extract_card_seller_info(card_html: str, card_text: str) -> Dict[str, Any]:
    """从列表页单张商品卡片里提取卖家信息（在列表页直接抓，不开详情页）

    返回字段（缺失则 None/False）：
      credit_level : str  - "极好" / "优秀" / "良好" / "较差"
      is_free_ship : bool - 是否包邮
      condition    : str  - "全新" / "几乎全新" / "9成新"
    """
    default = {"credit_level": None, "is_free_ship": False, "condition": None}
    try:
        # 信用等级：从 credit-container 内的 gradient-image-text 的 title 抓
        m = re.search(r'credit-container[^>]*>.*?title="卖家信用(极好|优秀|良好|较差)"', card_html, re.DOTALL)
        if m:
            default["credit_level"] = m.group(1)
        # 包邮：标题或描述里出现"包邮"
        if "包邮" in card_text:
            default["is_free_ship"] = True
        # 成色：标题里出现"全新"/"几乎全新"/"9成新"
        if "几乎全新" in card_text:
            default["condition"] = "几乎全新"
        elif "全新" in card_text:
            default["condition"] = "全新"
        elif "9成新" in card_text or "9 成新" in card_text:
            default["condition"] = "9成新"
    except Exception:
        pass
    return default


def _extract_seller_info(page: Page) -> Dict[str, Any]:
    """兼容旧接口：从详情页抓（保留但不再主用，列表页已抓够数据）"""
    default = {"credit_level": None, "want_count": None, "is_free_ship": False, "condition": None, "is_verified": False}
    try:
        info = page.evaluate(r"""() => {
            const text = document.body.innerText || '';
            let credit_level = null;
            // 优先抓当前商品（不是推荐位）：找带"卖家信用"且在指定容器内
            const m = document.body.innerHTML.match(/credit-container[^>]*>.*?title="卖家信用(极好|优秀|良好|较差)"/);
            if (m) credit_level = m[1];
            if (!credit_level) {
                const tm = text.match(/信用(极好|优秀|良好|较差)/);
                if (tm) credit_level = tm[1];
            }
            return { credit_level };
        }""")
        if isinstance(info, dict):
            return {**default, **info}
    except Exception:
        pass
    return default


def _credit_score(credit_level: Optional[str]) -> float:
    """卖家信用 0~1"""
    return {"极好": 1.0, "优秀": 0.75, "良好": 0.5, "较差": 0.2}.get(credit_level or "", 0.3)


def _want_score(want: Optional[int]) -> float:
    """想要数 0~1"""
    if want is None:
        return 0.0
    if want >= 200: return 1.0
    if want >= 100: return 0.8
    if want >= 50:  return 0.6
    if want >= 20:  return 0.4
    if want >= 5:   return 0.2
    return 0.1


def _condition_score(condition: Optional[str]) -> float:
    """成色 0~1"""
    return {"全新": 1.0, "几乎全新": 0.85, "9成新": 0.7}.get(condition or "", 0.4)


def _score(item: Dict[str, Any], task: Dict[str, Any], seller_info: Optional[Dict[str, Any]] = None) -> float:
    """综合评分（0~1）
    维度权重（大王要求：优质、低价、卖家信用好）：
      关键词匹配  25%  - 标题/描述命中关键词比例
      价格区间    25%  - 排名 + 区间奖励/惩罚
      卖家信用    30%  - 极好/优秀/良好/较差（详情页抓）
      商品质量    20%  - 想要数 + 包邮 + 成色 + 实名（详情页抓）
    """
    text = (item.get("title", "") + " " + item.get("snippet", "")).lower()
    keywords = [k.lower() for k in task.get("keywords", []) + task.get("spec_filters", [])]

    # 1. 关键词匹配（25%）
    if keywords:
        hits = sum(1 for k in keywords if k in text)
        kw_score = hits / len(keywords)
    else:
        kw_score = 0.0

    # 2. 价格区间（25%）
    price = item.get("price")
    pr_lo, pr_hi = task.get("price_range", [0, 99999])
    if price is None:
        price_score = 0.3
    elif pr_lo <= price <= pr_hi:
        # 在区间里：离中位数越近越好
        mid = (pr_lo + pr_hi) / 2
        spread = (pr_hi - pr_lo) / 2 if pr_hi > pr_lo else 1
        dist = abs(price - mid) / spread
        price_score = 1.0 - 0.4 * dist  # 中位数=1.0, 区间边界=0.6
    else:
        if price < pr_lo:
            ratio = (pr_lo - price) / max(pr_lo, 1)
        else:
            ratio = (price - pr_hi) / max(pr_hi, 1)
        price_score = max(0.0, 0.5 - ratio * 0.5)  # 偏离 100% = 0 分

    # 3. 卖家信用（30%）— 仅在有详情页数据时计分
    if seller_info:
        seller_score = _credit_score(seller_info.get("credit_level"))
    else:
        seller_score = 0.0  # 没进详情页 = 0

    # 4. 商品质量（20%）— 仅在有详情页数据时计分
    if seller_info:
        quality = (
            _want_score(seller_info.get("want_count")) * 0.5
            + (0.15 if seller_info.get("is_free_ship") else 0.0)
            + _condition_score(seller_info.get("condition")) * 0.35
        )
        quality_score = min(1.0, quality)
    else:
        quality_score = 0.0

    final = (
        kw_score * 0.25
        + price_score * 0.25
        + seller_score * 0.30
        + quality_score * 0.20
    )
    return round(min(1.0, final), 3)


def search_one(task: Dict[str, Any], ctx: BrowserContext, debug: bool = False) -> Dict[str, Any]:
    """执行单个搜索任务（同步版）
    流程：
      1. 搜索列表页 → 提取 20 个商品（含卖家信用/包邮/成色，列表页直接拿，不再开详情页）
      2. 综合评分 → 排序 → 输出 Top 5
    """
    keyword = task["keywords"][0] if task.get("keywords") else task.get("name", "")
    url = SEARCH_URL.format(q=quote_plus(keyword))
    page = ctx.new_page()
    # 阻断图片/字体等加速（每个详情页省 2-3 秒）
    page.route("**/*", lambda route: route.abort() if route.request.resource_type in ("image", "media", "font") else route.continue_())
    result = {"id": task["id"], "keyword": keyword, "url": url, "status": "ok", "items": [], "error": None}
    try:
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(15000)
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        # 等 React 渲染的商品卡片出现（关键！闲鱼用 mtop 异步 API + React 渲染）
        try:
            page.wait_for_selector('a[class*="feeds-item-wrap"]', timeout=10000, state="attached")
        except Exception:
            pass  # 找不到就继续走，_extract_items 会返回 0 条
        # 多等 1.5 秒让 React 完成渲染（信用/想要数等字段异步填充）
        time.sleep(1.5)

        if _check_login_wall(page):
            result["status"] = "login_required"
            result["error"] = "闲鱼登录墙挡住"
            return result

        items = _extract_items(page)
        # 列表页直接含 seller_info，直接评分
        scored = []
        for it in items:
            s = _score(it, task, seller_info=it.get("seller_info"))
            if s > 0:
                it["score"] = round(s, 3)
                scored.append(it)
        scored.sort(key=lambda x: x["score"], reverse=True)

        result["items"] = scored[:5]
        result["detail_checked"] = 0  # 不再开详情页
        if not scored:
            result["status"] = "no_match"
            result["error"] = f"页面已加载但未匹配 (共{len(items)}条卡片)"
    except Exception as e:
        result["status"] = "exception"
        result["error"] = str(e)[:200]
    finally:
        try:
            page.close()
        except Exception:
            pass
    return result


def generate_suggestions(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """无cookie时的降级模式：生成搜索建议清单（含可点击的闲鱼链接）"""
    out = []
    for t in tasks:
        primary_kw = t["keywords"][0] if t.get("keywords") else t.get("name", "")
        url = SEARCH_URL.format(q=quote_plus(primary_kw))
        out.append({
            "id": t["id"],
            "name": t.get("name"),
            "plan": t.get("plan"),
            "essential": t.get("essential"),
            "category": t.get("category"),
            "price_range": t.get("price_range"),
            "keywords": t.get("keywords", []),
            "spec_filters": t.get("spec_filters", []),
            "primary_keyword": primary_kw,
            "search_url": url,
            "status": "suggestion",
            "items": [],
        })
    return out


def _run_one_in_subprocess(task_json: str, cookie_path: str) -> Dict[str, Any]:
    """在子进程中执行 search_one（每项独立 browser，超时由父进程控制）"""
    import tempfile, shutil
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    task = json.loads(task_json)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME, args=["--no-sandbox"])
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=UA,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        try:
            cookies = json.loads(Path(cookie_path).read_text(encoding="utf-8"))
            cleaned = []
            for c in cookies:
                cleaned.append({
                    "name": c["name"], "value": c["value"],
                    "domain": c.get("domain", ".goofish.com"),
                    "path": c.get("path", "/"),
                })
            ctx.add_cookies(cleaned)
        except Exception:
            pass
        Stealth(
            navigator_user_agent=True, navigator_user_agent_override=UA,
            navigator_languages_override=("zh-CN","zh"), navigator_platform_override="MacIntel",
            init_scripts_only=True,
        ).apply_stealth_sync(ctx)

        try:
            return search_one(task, ctx)
        finally:
            try: browser.close()
            except Exception: pass


def _subprocess_worker(task_json: str, cookie_path: str) -> Dict[str, Any]:
    """顶层子进程 worker（spawn 模式需要可 pickle）
    直接返回结果 dict，供 Pool.apply_async().get() 获取
    """
    try:
        return _run_one_in_subprocess(task_json, cookie_path)
    except Exception as e:
        kw = ""
        try:
            t = json.loads(task_json)
            kw = t.get("keywords", [""])[0]
        except Exception:
            pass
        return {
            "id": "?", "status": "exception", "items": [],
            "error": str(e)[:200], "keyword": kw, "url": "",
        }


def run_batch(tasks: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """批量执行所有搜索任务
    - 3 路并发（Pool 限流，避免 29 个 Chrome 同时跑爆内存）
    - 每项 75 秒硬性超时（详情页 8 个 × 8s ≈ 60s + 列表 5s + 缓冲）
    - 列表+详情双阶段评分：先按关键词+价格排序筛 Top 8，进详情抓卖家信用后重排
    """
    cookies = _load_cookies()
    if not cookies:
        print("[search] 无 cookie，降级为搜索建议模式")
        return generate_suggestions(tasks)

    print(f"[search] 已加载 cookie，开始批量搜索 {len(tasks)} 项（3 路并发 + 75s 超时）")
    import multiprocessing as mp
    import tempfile

    MAX_CONCURRENT = 1  # 1 路串行（防闲鱼风控，限流）
    TASK_TIMEOUT = 35   # 列表 5s + 详情 3×6s + 缓冲 ≈ 30s
    INTER_TASK_DELAY = 3  # 每个任务结束后 sleep 3 秒（模拟人类节奏）

    ctx = mp.get_context("spawn")
    cookie_tmp = Path(tempfile.mkdtemp(prefix="xianyu_cookies_")) / "cookies.json"
    cookie_tmp.write_text(json.dumps(cookies, ensure_ascii=False), encoding="utf-8")

    # 提交所有任务到 Pool（3 路并发）
    pool = ctx.Pool(MAX_CONCURRENT)
    async_results = []
    for i, t in enumerate(tasks):
        kw = t["keywords"][0] if t.get("keywords") else t.get("name", "")
        print(f"[search] {i+1}/{len(tasks)} {t['id']} {kw}", flush=True)
        ar = pool.apply_async(
            _subprocess_worker,
            (json.dumps(t, ensure_ascii=False), str(cookie_tmp)),
        )
        async_results.append((i, t, ar, kw))

    # 等待所有任务结束
    pool.close()
    pool.join()

    # 收集结果
    results: List[Dict[str, Any]] = []
    for i, t, ar, kw in async_results:
        try:
            r = ar.get(timeout=TASK_TIMEOUT)
            if not r.get("url"):
                r["url"] = SEARCH_URL.format(q=quote_plus(kw))
            results.append(r)
        except mp.TimeoutError:
            print(f"  ⚠️ {t['id']} 超时 (>{TASK_TIMEOUT}s)", flush=True)
            results.append({
                "id": t["id"], "status": "timeout", "items": [],
                "error": f"{TASK_TIMEOUT}s 超时", "keyword": kw,
                "url": SEARCH_URL.format(q=quote_plus(kw)),
            })
        except Exception as e:
            results.append({
                "id": t["id"], "status": "exception", "items": [],
                "error": str(e)[:200], "keyword": kw,
                "url": SEARCH_URL.format(q=quote_plus(kw)),
            })
        time.sleep(INTER_TASK_DELAY)

    try:
        shutil.rmtree(cookie_tmp.parent)
    except Exception:
        pass

    return results


def main():
    import sys
    bom_path = Path(__file__).parent / "bom_tasks.json"
    out_path = Path(__file__).parent.parent / "output" / "search_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bom = json.loads(bom_path.read_text(encoding="utf-8"))
    tasks = bom["tasks"]
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        tasks = [tasks[idx]]
    results = run_batch(tasks)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[search] wrote {out_path}")


if __name__ == "__main__":
    main()