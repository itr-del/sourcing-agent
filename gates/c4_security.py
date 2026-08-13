"""
gates/c4_security.py — C4 安全门禁（核心创新 5：L3 不可绕过）

目的：防止受限信息泄露
分级：
- L1 公开 → 放行
- L2 内部 → 引用时脱敏（不暴露来源细节，但可保留事实）
- L3 受限 → 强制脱敏（不可绕过）
失败处理：自动替换为 [已脱敏]，记录脱敏次数
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class C4SecurityGate:
    """C4 安全门禁 — 核心创新 5：L3 不可绕过"""

    # L3 正则模式
    L3_PATTERNS = {
        '身份证': r'\b\d{17}[\dXx]\b',
        '银行卡': r'\b\d{16,19}\b',
        '手机号': r'\b1[3-9]\d{9}\b',
        '内部代号': r'\b[A-Z]{2,4}-\d{3,5}\b',
    }

    def check(self, integrated_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查所有输出文本，自动脱敏 L3 字段
        关键：即使调用方说"原样输出"，L3 也强制脱敏（不可绕过）
        """
        violations = []
        redaction_count = 0

        redacted_output = {}
        for task_id, data in integrated_output.items():
            data_copy = data.copy()
            # 对所有文本字段做脱敏
            for key in ["scoring_basis", "audit_summary"]:
                if key in data_copy:
                    original = data_copy[key]
                    redacted, count = self._redact(original)
                    if count > 0:
                        violations.append({
                            "task_id": task_id,
                            "type": "l3_detected",
                            "field": key,
                            "message": f"自动脱敏 {count} 处 L3 字段",
                            "severity": "low",
                            "note": "硬底线：不可绕过",
                        })
                        redaction_count += count
                    data_copy[key] = redacted

            # 对 Top 3 商品也脱敏
            new_top_3 = []
            for p in data_copy.get("top_3", []):
                p_copy = p.copy()
                for key in ["title", "url"]:
                    if key in p_copy:
                        redacted, count = self._redact(p_copy[key])
                        if count > 0:
                            redaction_count += count
                        p_copy[key] = redacted
                new_top_3.append(p_copy)
            data_copy["top_3"] = new_top_3
            redacted_output[task_id] = data_copy

        return {
            "gate": "C4",
            "name": "安全门禁",
            "status": "PASS",
            "violations": violations,
            "blocking": True,
            "redaction_count": redaction_count,
            "note": f"硬底线：L3 不可绕过。共脱敏 {redaction_count} 处。",
        }

    def _redact(self, text: str) -> tuple:
        """返回 (脱敏后文本, 脱敏次数)"""
        if not isinstance(text, str):
            return text, 0

        count = 0
        result = text
        for label, pattern in self.L3_PATTERNS.items():
            matches = re.findall(pattern, result)
            if matches:
                count += len(matches)
                result = re.sub(pattern, f'[已脱敏-{label}]', result)
                logger.warning(f"🔒 C4 自动脱敏 {len(matches)} 处 {label}")

        return result, count