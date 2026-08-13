"""
MCP 数据源注册表 — Master Agent 通过这个注册表发现和调度数据源
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from .base import BaseSource

logger = logging.getLogger(__name__)


class SourceRegistry:
    """数据源注册表（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sources = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, source: BaseSource):
        """注册一个数据源"""
        if not isinstance(source, BaseSource):
            raise TypeError(f"必须是 BaseSource 子类, 收到 {type(source)}")
        self._sources[source.source_id] = source
        logger.info(f"✅ 注册数据源: {source.source_id} ({source.source_name})")

    def unregister(self, source_id: str):
        """注销数据源"""
        if source_id in self._sources:
            del self._sources[source_id]
            logger.info(f"❌ 注销数据源: {source_id}")

    def get(self, source_id: str) -> Optional[BaseSource]:
        """获取数据源"""
        return self._sources.get(source_id)

    def list_sources(self) -> List[BaseSource]:
        """列出所有数据源"""
        return list(self._sources.values())

    def list_metadata(self) -> List[Dict[str, Any]]:
        """列出所有数据源元信息"""
        return [s.get_metadata() for s in self._sources.values()]

    async def search_all(self, query: str, price_range: tuple = None,
                          source_ids: List[str] = None, limit_per: int = 10) -> Dict[str, List[Dict]]:
        """
        并发在多个数据源搜索

        Returns:
            {source_id: [products]}
        """
        targets = source_ids or list(self._sources.keys())
        sources = [self._sources[si] for si in targets if si in self._sources]

        tasks = [
            self._safe_search(s, query, price_range, limit_per)
            for s in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                logger.error(f"❌ {source.source_id} 搜索失败: {result}")
                output[source.source_id] = []
            else:
                output[source.source_id] = result
        return output

    async def _safe_search(self, source: BaseSource, query: str,
                            price_range: tuple, limit: int) -> List[Dict]:
        """带异常处理的搜索"""
        try:
            return await source.search(query, price_range, limit)
        except Exception as e:
            logger.error(f"搜索失败 [{source.source_id}]: {e}")
            return []


# 全局注册表实例
registry = SourceRegistry()


def get_registry() -> SourceRegistry:
    """获取全局注册表"""
    return registry
