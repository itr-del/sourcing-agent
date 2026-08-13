"""
gates/c3_consistency.py — C3 一致性门禁

目的：确保产物内部逻辑自洽
检查：数字不矛盾 / 章节一致 / 结论与论据匹配
依赖：必须 C1+C2 都通过才能跑
失败处理：标红矛盾处，反馈给 Integrator 自查
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class C3ConsistencyGate:
    """C3 一致性门禁 — 拓扑中段（依赖 C1+C2）"""

    def check(self, integrated_output: Dict[str, Any],
              c1_result: Dict[str, Any] = None,
              c2_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Args:
            integrated_output: Integrator 产出
            c1_result: C1 门禁结果
            c2_result: C2 门禁结果
        """
        # 前置门禁检查
        if c1_result and c1_result.get("status") == "FAIL":
            return {
                "gate": "C3",
                "name": "一致性门禁",
                "status": "SKIP",
                "violations": [],
                "blocking": True,
                "note": "C1 失败，跳过 C3",
            }
        if c2_result and c2_result.get("status") == "FAIL":
            return {
                "gate": "C3",
                "name": "一致性门禁",
                "status": "SKIP",
                "violations": [],
                "blocking": True,
                "note": "C2 失败，跳过 C3",
            }

        violations = []

        for task_id, data in integrated_output.items():
            top_3 = data.get("top_3", [])
            if not top_3:
                continue

            # 检查 1：价格单调性（Top 3 之间）
            scores = [p.get("final_score", 0) for p in top_3]
            if scores != sorted(scores, reverse=True):
                violations.append({
                    "task_id": task_id,
                    "type": "score_order",
                    "message": "Top 3 未按评分降序排列",
                    "severity": "high",
                })

            # 检查 2：评分依据与实际评分一致
            basis = data.get("scoring_basis", "")
            best = top_3[0]
            actual_score = best.get("final_score", 0)
            if f"{actual_score:.3f}" not in basis and "无推荐" not in basis:
                violations.append({
                    "task_id": task_id,
                    "type": "score_basis_mismatch",
                    "message": f"评分依据未反映实际评分 {actual_score:.3f}",
                    "severity": "medium",
                })

            # 检查 3：审计摘要与任务状态一致
            audit = data.get("audit_summary", "")
            risk_level = "high" in audit
            if risk_level and len(top_3) > 0:
                violations.append({
                    "task_id": task_id,
                    "type": "risk_top3",
                    "message": "高风险任务仍有 Top 3 推荐",
                    "severity": "medium",
                    "note": "应在推送时附更强提示",
                })

        status = "FAIL" if any(v["severity"] == "high" for v in violations) else "PASS"
        return {
            "gate": "C3",
            "name": "一致性门禁",
            "status": status,
            "violations": violations,
            "blocking": True,
        }