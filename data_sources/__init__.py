"""
数据源 MCP Adapter 包

每个数据源（闲鱼/1688/京东工业等）都通过实现 BaseSource 接口成为可插拔的 MCP adapter。
"""

from .base import BaseSource, SourceError, SourceTimeout, SourceAuthError
from .registry import get_registry, SourceRegistry
from .xianyu_source import XianyuSource, register as register_xianyu

__all__ = [
    "BaseSource",
    "SourceError",
    "SourceTimeout",
    "SourceAuthError",
    "SourceRegistry",
    "get_registry",
    "XianyuSource",
    "register_xianyu",
]
