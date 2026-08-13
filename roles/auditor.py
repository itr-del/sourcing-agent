"""
roles/auditor.py — 核心创新 1：认知隔离（独立 session）

Auditor = 独立审计角色
职责：审计 Explorer 的素材，质疑逻辑、查一致性
关键约束：只挑刺，不改、不补、不重收
"""

import logging
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Auditor:
    """本项目 Auditor — 独立审计（独立 session）"""

    def __init__(self):
        self.findings: List[Dict[str, Any]] = []

    def audit(self, explorer_output: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        审计 Explorer 的输出

        Returns:
            {
                "task_id": {
                    "issues": [...],
                    "confidence": 0.0-1.0,
                    "risk_level": "low/medium/high"
                }
            }
        """
        audit_report = {}
        for task_id, source_results in explorer_output.items():
            task_audit = {
                "issues": [],
                "confidence": 1.0,
                "risk_level": "low",
            }

            all_products = []
            for source_id, products in source_results.items():
                all_products.extend(products)

            if not all_products:
                task_audit["issues"].append({
                    "type": "no_data",
                    "severity": "high",
                    "message": f"任务 {task_id}：所有数据源均无结果",
                })
                task_audit["confidence"] = 0.0
                task_audit["risk_level"] = "high"
                audit_report[task_id] = task_audit
                continue

            # 检查 1：链接可访问性
            for p in all_products:
                url = p.get("url", "")
                if not url or not url.startswith("http"):
                    task_audit["issues"].append({
                        "type": "invalid_url",
                        "severity": "medium",
                        "message": f"商品链接无效: {url[:50]}",
                        "product": p,
                    })

            # 检查 2：价格合理性
            prices = [p.get("price", 0) for p in all_products if p.get("price", 0) > 0]
            if prices:
                avg = sum(prices) / len(prices)
                for p in all_products:
                    price = p.get("price", 0)
                    if price > 0 and price > avg * 5:
                        task_audit["issues"].append({
                            "type": "price_outlier",
                            "severity": "low",
                            "message": f"价格远高于均价: ¥{price} vs 均价 ¥{avg:.1f}",
                            "product": p,
                        })

            # 检查 3：信用风险
            for p in all_products:
                credit = p.get("credit", "")
                if credit in ["差", "一般", ""]:
                    task_audit["issues"].append({
                        "type": "credit_risk",
                        "severity": "medium",
                        "message": f"卖家信用较低: {credit}",
                        "product": p,
                    })

            # 检查 4：数据源一致性
            source_ids = list(source_results.keys())
            if len(source_ids) > 1:
                # 多源情况下，看商品数量是否合理
                counts = [len(ps) for ps in source_results.values()]
                if max(counts) - min(counts) > 5:
                    task_audit["issues"].append({
                        "type": "source_imbalance",
                        "severity": "low",
                        "message": f"数据源结果数量差异大: {dict(zip(source_ids, counts))}",
                    })

            # 汇总风险等级
            severities = [i["severity"] for i in task_audit["issues"]]
            if "high" in severities:
                task_audit["risk_level"] = "high"
                task_audit["confidence"] *= 0.5
            elif "medium" in severities:
                task_audit["risk_level"] = "medium"
                task_audit["confidence"] *= 0.8

            audit_report[task_id] = task_audit

        logger.info(f"✅ Auditor 完成，共发现 {sum(len(t.get('issues', [])) for t in audit_report.values())} 个问题")
        return audit_report

    def security_redact(self, content: str) -> str:
        """
        核心创新 5：L3 不可绕过 — 强制脱敏

        关键规则：即使调用方说"原样输出"，L3 字段强制脱敏
        """
        # L3 模式
        patterns = {
            '身份证': r'\b\d{17}[\dXx]\b',
            '银行卡': r'\b\d{16,19}\b',
            '手机号': r'\b1[3-9]\d{9}\b',
            '内部代号': r'\b[A-Z]{2,4}-\d{3,5}\b',
            '邮箱': r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',
        }

        redacted = content
        for label, pattern in patterns.items():
            matches = re.findall(pattern, redacted)
            if matches:
                redacted = re.sub(pattern, f'[已脱敏-{label}]', redacted)
                logger.warning(f"🔒 自动脱敏 {len(matches)} 处 {label}")

        return redacted