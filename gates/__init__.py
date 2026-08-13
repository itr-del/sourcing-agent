"""
gates/__init__.py — TRIOI 革新 2：5 道门禁（拓扑依赖 DAG）

门禁拓扑图：
                C1 语法门禁    C2 引用门禁
                    │              │
                    └──────┬───────┘
                           ▼
                       C3 一致性门禁
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                C4 安全门禁   C5 可执行性门禁

执行流程：C1+C2 并行 → C3 依赖 → C4+C5 并行 → fail-fast
"""

from .c1_syntax import C1SyntaxGate
from .c2_reference import C2ReferenceGate
from .c3_consistency import C3ConsistencyGate
from .c4_security import C4SecurityGate
from .c5_executable import C5ExecutableGate

# 严格度档位
STRICT = "STRICT"
NORMAL = "NORMAL"
LIGHT = "LIGHT"
OFF = "OFF"

__all__ = [
    "C1SyntaxGate",
    "C2ReferenceGate",
    "C3ConsistencyGate",
    "C4SecurityGate",
    "C5ExecutableGate",
    "STRICT", "NORMAL", "LIGHT", "OFF",
]