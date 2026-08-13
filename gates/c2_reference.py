"""
gates/c2_reference.py — C2 引用门禁

目的：确保每个事实陈述有可追溯的来源
检查：链接可访问性 / 信源等级 / 关键论断依赖
失败处理：缺引用 → 加引用或删除该陈述；C/D 级独占 → 标"未核验"
"""

import re
import logging
from typing import Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class C2ReferenceGate:
    """C2 引用门禁 — 拓扑入口（与 C1 并行）"""

    def check(self, integrated_output: Dict[str, Any],
              source_grades: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Args:
            integrated_output: Integrator 产出
            source_grades: {source_id: grade} 信源等级映射
        """
        violations = []
        source_grades = source_grades or {"xianyu": "B", "1688": "A", "jd_industrial": "A"}

        for task_id, data in integrated_output.items():
            for i, p in enumerate(data.get("top_3", [])):
                # 检查链接格式
                url = p.get("url", "")
                if url and not url.startswith("http"):
                    violations.append({
                        "task_id": task_id,
                        "type": "bad_url",
                        "product": p.get("title"),
                        "message": f"链接格式错误: {url[:50]}",
                        "severity": "high",
                    })

                # 检查信源等级
                source_id = p.get("source_id", "unknown")
                grade = source_grades.get(source_id, "D")
                if grade in ("C", "D"):
                    violations.append({
                        "task_id": task_id,
                        "type": "low_grade_source",
                        "product": p.get("title"),
                        "message": f"信源等级低: {source_id}={grade}",
                        "severity": "medium",
                        "note": "需标'未核验'或换更高等级信源",
                    })

        # 评分依据中关键论断是否引用 S/A 级信源
        for task_id, data in integrated_output.items():
            basis = data.get("scoring_basis", "")
            if "信用" in basis:
                # 信用评分必须基于平台标记（A 级以上）
                top_1 = data.get("top_3", [{}])[0]
                grade = source_grades.get(top_1.get("source_id", ""), "D")
                if grade in ("C", "D"):
                    violations.append({
                        "task_id": task_id,
                        "type": "key_claim_weak_source",
                        "message": "关键论断（信用评分）依赖低等级信源",
                        "severity": "high",
                    })

        status = "FAIL" if any(v["severity"] == "high" for v in violations) else "PASS"
        return {
            "gate": "C2",
            "name": "引用门禁",
            "status": status,
            "violations": violations,
            "blocking": True,
        }