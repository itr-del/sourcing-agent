"""
decision_log/logger.py — 核心创新 3：决策追溯

每个关键决策结构化记录到 decision-log.json
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DecisionLogger:
    """本项目 Decision-log 记录器"""

    def __init__(self, log_file: str = "decision_log/decision-log.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.entries: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """加载已有日志"""
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    self.entries = json.load(f)
            except Exception:
                self.entries = []

    def _save(self):
        """持久化日志"""
        with open(self.log_file, 'w') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

    def log(self, task_id: str, context_snapshot: str,
            options: List[Dict[str, Any]], chosen: Optional[Dict[str, Any]],
            confidence: float, dissenting_opinions: List[str] = None):
        """
        记录一次决策

        Args:
            task_id: 任务 ID
            context_snapshot: 当时上下文摘要
            options: 候选方案列表
            chosen: 最终选择
            confidence: 信心度 0-1
            dissenting_opinions: 反对意见
        """
        entry = {
            "decision_id": f"D{len(self.entries) + 1:03d}",
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "phase": "Phase 1",
            "role": "Integrator",
            "context_snapshot": context_snapshot,
            "options_considered": options,
            "chosen": chosen,
            "rationale": self._generate_rationale(chosen, confidence) if chosen else None,
            "dissenting_opinions": dissenting_opinions or [],
            "confidence": confidence,
        }
        self.entries.append(entry)
        self._save()
        logger.info(f"📝 Decision-log: {entry['decision_id']} 任务 {task_id} 信心度 {confidence:.2f}")

    def _generate_rationale(self, chosen: Dict, confidence: float) -> str:
        return (
            f"综合评分 {chosen.get('final_score', 0):.3f}，"
            f"基于 4 维度加权（关键词/价格/信用/质量），"
            f"信心度 {confidence:.2f}。"
        )

    def export_markdown(self) -> str:
        """导出 Markdown 格式 decision-log"""
        lines = ["# Decision Log\n"]
        for e in self.entries:
            lines.append(f"\n## {e['decision_id']} — 任务 {e['task_id']}")
            lines.append(f"- 时刻：{e['timestamp']}")
            lines.append(f"- 决策者：{e['role']}")
            lines.append(f"- 上下文：{e['context_snapshot']}")
            lines.append(f"- 候选方案：")
            for opt in e["options_considered"]:
                lines.append(f"  - 排名 {opt.get('rank', '?')}：{opt.get('title', '')} (评分 {opt.get('score', 0):.3f})")
            lines.append(f"- 最终选择：{e['chosen'].get('title', '') if e['chosen'] else 'N/A'}")
            lines.append(f"- 选择理由：{e.get('rationale', 'N/A')}")
            lines.append(f"- 信心度：{e['confidence']:.2f}")
            if e.get('dissenting_opinions'):
                lines.append(f"- 反对意见：{e['dissenting_opinions']}")
        return "\n".join(lines)