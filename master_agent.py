"""
master_agent.py — TRIOI 4 阶段流程改造版

Phase 1: 3 角色并行生成（Explorer/Auditor/Integrator 独立 session）
Phase 2: 5 道门禁自检（拓扑依赖 DAG）
Phase 3: decision-log 决策追溯
Phase 4: 交付 + 复盘
"""

import asyncio
import logging
from typing import Dict, Any, List

from roles import Explorer, Auditor, Integrator
from gates import (
    C1SyntaxGate, C2ReferenceGate, C3ConsistencyGate,
    C4SecurityGate, C5ExecutableGate,
    STRICT, NORMAL, LIGHT, OFF
)
from decision_log import DecisionLogger
from source_grading import get_grade
from scenes import get_scene, list_scenes

logger = logging.getLogger(__name__)


class MasterAgent:
    """TRIOI 化 Master Agent — 4 阶段流程"""

    def __init__(self, gate_strictness: str = NORMAL):
        # 3 角色
        self.explorer = Explorer()
        self.auditor = Auditor()
        self.integrator = Integrator()

        # 5 道门禁
        self.c1 = C1SyntaxGate()
        self.c2 = C2ReferenceGate()
        self.c3 = C3ConsistencyGate()
        self.c4 = C4SecurityGate()
        self.c5 = C5ExecutableGate()

        # decision-log
        self.decision_logger = DecisionLogger()

        # 门禁严格度
        self.gate_strictness = gate_strictness

        logger.info(f"✅ Master Agent 就绪（门禁严格度: {gate_strictness}）")

    async def run(self, bom_items: List[Dict]) -> Dict[str, Any]:
        """
        TRIOI 4 阶段流程

        Returns:
            {
                "integrated": ...,
                "gates_report": ...,
                "decision_log_md": ...,
            }
        """
        # ===== Phase 1: 3 角色并行 =====
        logger.info("=" * 60)
        logger.info("Phase 1: 三角色并行（认知隔离）")
        logger.info("=" * 60)

        # Explorer：调度数据源，收集素材
        explorer_output = await self.explorer.collect(bom_items)

        # Auditor：独立审计（不依赖 Explorer 内部推理）
        auditor_output = self.auditor.audit(explorer_output)

        # Integrator：综合产出（看到的是素材 + 审计，不是内部推理）
        integrated = self.integrator.integrate(
            explorer_output,
            auditor_output,
            decision_logger=self.decision_logger,
        )

        # ===== Phase 2: 5 道门禁自检（拓扑 DAG）=====
        logger.info("=" * 60)
        logger.info("Phase 2: 5 道门禁自检（拓扑依赖）")
        logger.info("=" * 60)

        gates_report = await self._run_gates(integrated)

        # ===== Phase 3: decision-log =====
        logger.info("=" * 60)
        logger.info("Phase 3: decision-log")
        logger.info("=" * 60)

        decision_log_md = self.decision_logger.export_markdown()

        # ===== Phase 4: 交付 =====
        logger.info("=" * 60)
        logger.info("Phase 4: 交付")
        logger.info("=" * 60)

        return {
            "integrated": integrated,
            "gates_report": gates_report,
            "decision_log_md": decision_log_md,
        }

    async def _run_gates(self, integrated_output: Dict) -> Dict:
        """5 道门禁（拓扑依赖 DAG）"""
        results = {}

        # Step 1: C1 + C2 并行
        c1_result = self.c1.check(integrated_output)
        c2_result = self.c2.check(integrated_output, {
            "xianyu": get_grade("xianyu"),
        })
        results["C1"] = c1_result
        results["C2"] = c2_result

        # Step 2: C3 依赖前两者
        c3_result = self.c3.check(integrated_output, c1_result, c2_result)
        results["C3"] = c3_result

        # Step 3: C4 + C5 并行（与 C3 独立）
        c4_result = self.c4.check(integrated_output)
        c5_result = self.c5.check(integrated_output)
        results["C4"] = c4_result
        results["C5"] = c5_result

        # 严格度控制
        if self.gate_strictness == OFF:
            for k in results:
                results[k]["status"] = "PASS"
                results[k]["note"] = "OFF 模式：跳过门禁"
        elif self.gate_strictness == LIGHT:
            # LIGHT 仅 C2/C4 blocking
            for k in ["C1", "C3", "C5"]:
                results[k]["blocking"] = False
                results[k]["status"] = "PASS" if not results[k].get("violations") else "WARNING"

        # fail-fast 短路
        for k, r in results.items():
            if r.get("status") == "FAIL" and r.get("blocking", True):
                logger.error(f"❌ {k} 门禁失败，触发 fail-fast")
                return results

        # 汇总
        pass_count = sum(1 for r in results.values() if r["status"] == "PASS")
        logger.info(f"✅ 门禁完成：{pass_count}/5 PASS")
        return results


# CLI 入口
async def main():
    agent = MasterAgent(gate_strictness=NORMAL)

    # 场景测试
    scenes = list_scenes()
    print(f"✅ 已注册场景:")
    for s in scenes:
        print(f"  {s['trigger']}: {s['name']}")

    # 示例跑批
    sample_bom = [
        {"id": "A03", "name": "ESP32-S3", "kw": "ESP32-S3", "price_range": [20, 50]},
        {"id": "B05", "name": "螺旋桨保护罩", "kw": "螺旋桨保护罩", "price_range": [50, 150]},
    ]

    print(f"\n🚀 开始 TRIOI 4 阶段流程（{len(sample_bom)} 个任务）...")
    result = await agent.run(sample_bom)

    print(f"\n📊 结果汇总:")
    print(f"  任务数：{len(result['integrated'])}")
    print(f"  门禁：{sum(1 for r in result['gates_report'].values() if r['status'] == 'PASS')}/5 PASS")
    print(f"  decision-log 条目：{len(agent.decision_logger.entries)}")


if __name__ == "__main__":
    asyncio.run(main())