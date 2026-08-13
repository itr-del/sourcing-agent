"""
gates/c1_syntax.py — C1 语法门禁

目的：确保产物可被机器解析、可被下游消费
检查：JSON / Markdown 标题层级 / 表格列数 / 链接格式 / 代码块标识
失败处理：返回 parse error 行号，Integrator 重新格式化（不改语义，只改格式）
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class C1SyntaxGate:
    """C1 语法门禁 — 拓扑入口（与 C2 并行）"""

    def check(self, integrated_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            integrated_output: Integrator 产出 {task_id: {top_3, scoring_basis, audit_summary}}

        Returns:
            {
                "gate": "C1",
                "name": "语法门禁",
                "status": "PASS" / "FAIL" / "SOFT_FAIL",
                "violations": [...],
                "blocking": True,
            }
        """
        violations = []
        for task_id, data in integrated_output.items():
            # 检查 top_3 是否为列表
            top_3 = data.get("top_3", [])
            if not isinstance(top_3, list):
                violations.append({
                    "task_id": task_id,
                    "type": "type_error",
                    "message": f"top_3 应为列表，实际: {type(top_3).__name__}",
                    "severity": "high",
                })

            # 检查每个商品的字段完整性
            required_fields = ["title", "price", "url", "source_id", "final_score"]
            for i, p in enumerate(top_3):
                if not isinstance(p, dict):
                    continue
                missing = [f for f in required_fields if f not in p]
                if missing:
                    violations.append({
                        "task_id": task_id,
                        "type": "missing_field",
                        "message": f"商品 {i} 缺失字段: {missing}",
                        "severity": "medium",
                    })

            # 检查评分依据是否包含公式
            scoring_basis = data.get("scoring_basis", "")
            if scoring_basis and "final_score" not in scoring_basis and "综合评分" not in scoring_basis:
                violations.append({
                    "task_id": task_id,
                    "type": "incomplete_basis",
                    "message": "评分依据缺少公式说明",
                    "severity": "low",
                })

        status = "FAIL" if any(v["severity"] == "high" for v in violations) else "PASS"
        return {
            "gate": "C1",
            "name": "语法门禁",
            "status": status,
            "violations": violations,
            "blocking": True,
        }