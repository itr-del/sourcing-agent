"""
roles/__init__.py — TRIOI 角色包
"""

from .explorer import Explorer
from .auditor import Auditor
from .integrator import Integrator

__all__ = ["Explorer", "Auditor", "Integrator"]