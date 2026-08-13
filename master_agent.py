"""
Sourcing-Agent Master Agent

接收 BOM 物料清单，调度多个 MCP 数据源，4 维度评分，推送 Top 3 推荐。
"""

import asyncio
import logging
from typing import List, Dict, Any
from data_sources import get_registry, register_xianyu

logger = logging.getLogger(__name__)


class MasterAgent:
    """Master Agent — BOM 调度中心"""

    def __init__(self):
        self.registry = get_registry()
        # 自动注册已实现的数据源
        register_xianyu()

    async def search_bom(self, bom_items: List[Dict],
                          source_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """
        对 BOM 中每件物料并发搜索

        Args:
            bom_items: [{"id": "A03", "name": "ESP32-S3", "price_range": [20, 50]}, ...]
            source_ids: 限定数据源（如 ["xianyu"]），None = 全部已注册

        Returns:
            {task_id: {"source_id": [products]}}
        """
        tasks = [
            self._search_item(item, source_ids)
            for item in bom_items
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for item, result in zip(bom_items, results):
            task_id = item.get("id", item.get("name"))
            if isinstance(result, Exception):
                logger.error(f"任务 {task_id} 失败: {result}")
                output[task_id] = {}
            else:
                output[task_id] = result
        return output

    async def _search_item(self, item: Dict, source_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """搜索单件物料"""
        query = item.get("kw") or item.get("keywords") or item.get("name")
        price_range = tuple(item["price_range"]) if "price_range" in item else None

        return await self.registry.search_all(
            query=query,
            price_range=price_range,
            source_ids=source_ids,
            limit_per=10,
        )


# CLI 入口
async def main():
    agent = MasterAgent()
    sources = agent.list_sources()
    print(f"✅ 已注册数据源: {[s.source_id for s in sources]}")

    # 健康检查
    for s in sources:
        healthy = await s.health_check()
        print(f"  - {s.source_name}: {'✅ 健康' if healthy else '❌ 不可用'}")


if __name__ == "__main__":
    asyncio.run(main())
