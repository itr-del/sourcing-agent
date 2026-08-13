"""
roles/explorer.py — TRIOI 革新 1：认知隔离（独立 session）

Explorer = 数据收集角色
职责：调度多个 MCP 数据源，收集商品 + 原始信息
关键约束：只收集，不写、不评
"""

import asyncio
import logging
from typing import List, Dict, Any
from data_sources import get_registry, register_xianyu

logger = logging.getLogger(__name__)


class Explorer:
    """TRIOI Explorer — 数据收集（独立 session）"""

    def __init__(self):
        self.registry = get_registry()
        # 自动注册已实现的数据源
        register_xianyu()

    async def collect(self, bom_items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        对 BOM 中每件物料并发调度数据源，收集原始素材

        Returns:
            {task_id: {source_id: [products]}}  —— 原始素材库
        """
        tasks = [
            self._collect_item(item) for item in bom_items
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for item, result in zip(bom_items, results):
            task_id = item.get("id", item.get("name"))
            if isinstance(result, Exception):
                logger.error(f"❌ {task_id} 收集失败: {result}")
                output[task_id] = {}
            else:
                output[task_id] = result
        return output

    async def _collect_item(self, item: Dict) -> Dict[str, List[Dict]]:
        """收集单件物料（调度所有已注册数据源）"""
        query = item.get("kw") or item.get("keywords") or item.get("name")
        price_range = tuple(item["price_range"]) if "price_range" in item else None

        logger.info(f"🔍 收集: {query} (价格区间: {price_range})")
        return await self.registry.search_all(
            query=query,
            price_range=price_range,
            limit_per=10,
        )


# CLI 入口
async def main():
    explorer = Explorer()
    sources = explorer.registry.list_sources()
    print(f"✅ Explorer 已就绪，已注册数据源: {[s.source_id for s in sources]}")

    # 示例：BOM 收集
    sample_bom = [{"id": "A03", "name": "ESP32-S3", "kw": "ESP32-S3", "price_range": [20, 50]}]
    results = await explorer.collect(sample_bom)
    print(f"\n📦 收集结果:")
    for task_id, source_results in results.items():
        for source_id, products in source_results.items():
            print(f"  {task_id} @ {source_id}: {len(products)} 个商品")


if __name__ == "__main__":
    asyncio.run(main())