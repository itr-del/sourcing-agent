"""
scenes/__init__.py — 核心创新 6：场景引擎

通过 YAML 配置定义场景，用户用 /场景名 一行触发
"""

# 内置场景配置（YAML）
SCENES = {
    "/bom": {
        "name": "BOM 物料采购",
        "trigger": "/bom <清单>",
        "params": ["bom_json"],
        "description": "对 BOM 物料清单自动采购评分",
        "output_format": "Top 3 推荐 + 评分依据 + 风险提示",
        "gates": "NORMAL",
    },
    "/price-compare": {
        "name": "跨平台价格对比",
        "trigger": "/price-compare <物料>",
        "params": ["material_name"],
        "description": "对单件物料多数据源比价",
        "output_format": "价格对比表 + 最优推荐",
        "gates": "LIGHT",
    },
    "/vendor-eval": {
        "name": "供应商评估",
        "trigger": "/vendor-eval <名称>",
        "params": ["vendor_name"],
        "description": "对单个供应商深度评估",
        "output_format": "信用档案 + 历史价格 + 风险提示",
        "gates": "STRICT",
    },
    "/bom-history": {
        "name": "BOM 历史追溯",
        "trigger": "/bom-history",
        "params": [],
        "description": "查看历史采购记录和决策日志",
        "output_format": "时间线 + decision-log",
        "gates": "OFF",
    },
}


def get_scene(trigger: str) -> dict:
    """根据 trigger 获取场景配置"""
    return SCENES.get(trigger)


def list_scenes() -> list:
    """列出所有场景"""
    return [
        {"trigger": k, "name": v["name"], "description": v["description"]}
        for k, v in SCENES.items()
    ]


__all__ = ["SCENES", "get_scene", "list_scenes"]