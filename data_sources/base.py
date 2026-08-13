"""
MCP 数据源基类 (Model Context Protocol)

所有采购数据源（闲鱼、1688、京东工业等）都通过这个统一接口被 Master Agent 调用。
新增数据源只需继承 BaseSource 并实现 search() 方法。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseSource(ABC):
    """MCP 数据源抽象基类"""

    # 数据源标识（唯一）
    source_id: str = ""

    # 数据源名称（显示用）
    source_name: str = ""

    # 数据源类型（B2C/B2B/C2C）
    source_type: str = ""

    # 是否需要登录
    requires_auth: bool = False

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.healthy = False

    @abstractmethod
    async def search(self, query: str, price_range: tuple = None,
                     limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        在数据源中查找物料

        Args:
            query: 搜索关键词（如 "ESP32-S3"）
            price_range: (min, max) 价格区间
            limit: 返回结果数量

        Returns:
            List of products:
            [
                {
                    "title": "商品标题",
                    "price": 26.0,
                    "url": "商品链接",
                    "credit": "极好",
                    "quality_tags": ["包邮", "全新"],
                    "want_count": 628,
                    "source_id": "xianyu",
                    "raw": {...}
                }
            ]
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """数据源健康状态检查"""
        raise NotImplementedError

    def get_metadata(self) -> Dict[str, Any]:
        """数据源元信息（用于 MCP 注册表）"""
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "requires_auth": self.requires_auth,
            "healthy": self.healthy,
        }


class SourceError(Exception):
    """数据源调用异常"""
    pass


class SourceTimeout(SourceError):
    """数据源调用超时"""
    pass


class SourceAuthError(SourceError):
    """数据源鉴权失败（如 Cookie 过期）"""
    pass
