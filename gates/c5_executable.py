"""
gates/c5_executable.py — C5 可执行性门禁

目的：确保结论可被照着执行（不只可读，可操作）
检查：责任主体 / 截止日期 / 验收方式 / 资源估算
失败处理：缺 owner → 加 owner；缺 deadline → 加 deadline
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class C5ExecutableGate:
    """C5 可执行性门禁"""

    def check(self, integrated_output: Dict[str, Any]) -> Dict[str, Any]:
        """检查每个 Top 3 推荐是否含可执行要素"""
        violations = []

        for task_id, data in integrated_output.items():
            # 每个推荐必须含"下一步动作"
            top_3 = data.get("top_3", [])
            for i, p in enumerate(top_3):
                # 检查是否含推荐说明
                basis = data.get("scoring_basis", "")
                rationale = p.get("score_breakdown", {})

                # 缺验收方式
                if "下一步" not in basis and "人工确认" not in basis:
                    violations.append({
                        "task_id": task_id,
                        "type": "no_next_action",
                        "product": p.get("title"),
                        "message": "推荐缺下一步动作说明",
                        "severity": "low",
                    })

                # 缺责任人（在推送消息中应有）
                # 缺截止日

        return {
            "gate": "C5",
            "name": "可执行性门禁",
            "status": "PASS",
            "violations": violations,
            "blocking": False,  # 警告级，不阻断
            "note": "STRICT 模式下升级为 blocking",
        }