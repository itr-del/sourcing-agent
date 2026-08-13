"""
闲鱼 MCP Adapter (当前主实现)

通过 Playwright + 注入 cookie 模拟登录态搜索闲鱼商品。
当前 Sourcing-Agent 唯一已实现的数据源。

未来计划：每个数据源（1688、京东工业等）都将实现同样的 MCP 接口，
企业可通过 MCP 协议自主入驻到 Sourcing-Agent 平台。
"""

import asyncio
import logging
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from .base import BaseSource, SourceError

logger = logging.getLogger(__name__)


class XianyuSource(BaseSource):
    """闲鱼数据源（MCP Adapter）"""

    source_id = "xianyu"
    source_name = "闲鱼"
    source_type = "C2C"
    requires_auth = True

    BASE_URL = "https://www.goofish.com"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.cookie_file = self.config.get("cookie_file", "~/.hermes/cookies/xianyu.json")
        self.headless = self.config.get("headless", True)
        self.timeout_ms = self.config.get("timeout_ms", 30000)

    async def health_check(self) -> bool:
        """检查闲鱼可达性"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                await page.goto(self.BASE_URL, timeout=self.timeout_ms)
                title = await page.title()
                await browser.close()
                self.healthy = "闲鱼" in title or "goofish" in title.lower()
                return self.healthy
        except Exception as e:
            logger.error(f"闲鱼健康检查失败: {e}")
            self.healthy = False
            return False

    async def search(self, query: str, price_range: tuple = None,
                     limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """在闲鱼搜索商品"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                context = await browser.new_context()
                await self._load_cookies(context)

                page = await context.new_page()
                search_url = f"{self.BASE_URL}/?q={query}"
                await page.goto(search_url, timeout=self.timeout_ms)
                await page.wait_for_timeout(2000)

                products = await self._extract_products(page, limit)

                if price_range:
                    min_p, max_p = price_range
                    products = [
                        p for p in products
                        if min_p <= p.get("price", 0) <= max_p
                    ]

                return products
            except Exception as e:
                logger.error(f"闲鱼搜索失败: {e}")
                raise SourceError(f"闲鱼搜索失败: {e}")
            finally:
                await browser.close()

    async def _load_cookies(self, context):
        import os
        import json
        cookie_path = os.path.expanduser(self.cookie_file)
        if not os.path.exists(cookie_path):
            logger.warning(f"Cookie 文件不存在: {cookie_path}")
            return
        with open(cookie_path) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

    async def _extract_products(self, page, limit: int) -> List[Dict[str, Any]]:
        """从页面提取商品数据"""
        try:
            elements = await page.query_selector_all("div[class*='feeds-item-wrap']")
            products = []
            for el in elements[:limit]:
                try:
                    title_el = await el.query_selector("a[class*='title']")
                    title_text = await title_el.inner_text() if title_el else "未知"

                    price_el = await el.query_selector("span[class*='price']")
                    price_text = await price_el.inner_text() if price_el else "0"
                    price = float(re.sub(r"[^\d.]", "", price_text) or 0)

                    credit_el = await el.query_selector("div[class*='credit']")
                    credit = await credit_el.inner_text() if credit_el else ""

                    want_el = await el.query_selector("div[class*='want']")
                    want_text = await want_el.inner_text() if want_el else "0"
                    want_count = int(re.sub(r"[^\d]", "", want_text) or 0)

                    link_el = await el.query_selector("a")
                    link = await link_el.get_attribute("href") if link_el else ""

                    products.append({
                        "title": title_text,
                        "price": price,
                        "url": self.BASE_URL + link if link and link.startswith("/") else link,
                        "credit": credit,
                        "quality_tags": [],
                        "want_count": want_count,
                        "source_id": self.source_id,
                    })
                except Exception:
                    continue
            return products
        except Exception as e:
            logger.error(f"提取商品失败: {e}")
            return []


def register():
    """注册到 MCP Registry"""
    from .registry import get_registry
    registry = get_registry()
    source = XianyuSource()
    registry.register(source)
    return source
