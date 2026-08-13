"""
roles/integrator.py — 核心创新 1：认知隔离（独立 session）

Integrator = 综合产出角色
职责：综合 Explorer 素材 + Auditor 审计，写成最终产物
关键约束：不重收、不再走数据源、只综合
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class Integrator:
    """本项目 Integrator — 综合产出（独立 session）"""

    def __init__(self, weights=None):
        self.weights = weights or {
            "keyword": 0.25,
            "price": 0.25,
            "credit": 0.30,
            "quality": 0.20,
        }

    def integrate(self,
                   explorer_output,
                   auditor_output,
                   decision_logger=None):
        """
        综合产出 Explorer 素材 + Auditor 审计
        """
        integrated = {}

        for task_id, source_results in explorer_output.items():
            all_products = []
            for source_id, products in source_results.items():
                for p in products:
                    p_copy = p.copy()
                    p_copy["source_id"] = source_id
                    all_products.append(p_copy)

            if not all_products:
                integrated[task_id] = {
                    "top_3": [],
                    "scoring_basis": "无数据",
                    "audit_summary": auditor_output.get(task_id, {}).get("risk_level", "unknown"),
                }
                continue

            # 4 维度评分
            scored = []
            for p in all_products:
                score = self._calculate_score(p)
                p_copy = p.copy()
                p_copy["final_score"] = score
                p_copy["score_breakdown"] = {
                    "keyword": self._score_keyword(p),
                    "price": self._score_price(p),
                    "credit": self._score_credit(p),
                    "quality": self._score_quality(p),
                }
                scored.append(p_copy)

            # 排序取 Top 3
            scored.sort(key=lambda x: x["final_score"], reverse=True)
            top_3 = scored[:3]

            # 评分依据（可读化）
            scoring_basis = self._format_scoring_basis(top_3)

            # 审计摘要
            audit = auditor_output.get(task_id, {})
            audit_summary = (
                f"风险等级: {audit.get('risk_level', 'unknown')} | "
                f"置信度: {audit.get('confidence', 0):.2f} | "
                f"问题数: {len(audit.get('issues', []))}"
            )

            integrated[task_id] = {
                "top_3": top_3,
                "scoring_basis": scoring_basis,
                "audit_summary": audit_summary,
            }

            # 核心创新 3：记录决策日志
            if decision_logger and top_3:
                decision_logger.log(
                    task_id=task_id,
                    context_snapshot=(
                        f"Explorer 收集 {len(all_products)} 个商品，"
                        f"Auditor 报告 {len(audit.get('issues', []))} 个问题"
                    ),
                    options=[{
                        "rank": i + 1,
                        "title": p.get("title", ""),
                        "score": p.get("final_score", 0),
                        "source": p.get("source_id", "unknown"),
                        "rationale": self._format_option_rationale(p),
                    } for i, p in enumerate(top_3)],
                    chosen=top_3[0] if top_3 else None,
                    confidence=audit.get("confidence", 0.5),
                )

        logger.info(f"✅ Integrator 完成，产出 {len(integrated)} 个任务结果")
        return integrated

    def _calculate_score(self, product):
        return (
            self._score_keyword(product) * self.weights["keyword"]
            + self._score_price(product) * self.weights["price"]
            + self._score_credit(product) * self.weights["credit"]
            + self._score_quality(product) * self.weights["quality"]
        )

    def _score_keyword(self, p):
        return 0.8

    def _score_price(self, p):
        return 0.7

    def _score_credit(self, p):
        credit = p.get("credit", "")
        mapping = {"极好": 1.0, "优秀": 0.8, "良好": 0.6, "一般": 0.4, "差": 0.2, "": 0.5}
        return mapping.get(credit, 0.5)

    def _score_quality(self, p):
        want = p.get("want_count", 0)
        if want > 500: return 1.0
        if want > 100: return 0.8
        if want > 10: return 0.6
        return 0.4

    def _format_scoring_basis(self, top_3):
        if not top_3:
            return "无推荐"
        best = top_3[0]
        bd = best.get("score_breakdown", {})
        return (
            f"综合评分 {best['final_score']:.3f} = "
            f"关键词{bd.get('keyword', 0):.2f}×{self.weights['keyword']} + "
            f"价格{bd.get('price', 0):.2f}×{self.weights['price']} + "
            f"信用{bd.get('credit', 0):.2f}×{self.weights['credit']} + "
            f"质量{bd.get('quality', 0):.2f}×{self.weights['quality']}"
        )

    def _format_option_rationale(self, p):
        return (
            f"价格 ¥{p.get('price', 0)} · "
            f"信用 {p.get('credit', '未知')} · "
            f"想要数 {p.get('want_count', 0)} · "
            f"来源 {p.get('source_id', '?')}"
        )