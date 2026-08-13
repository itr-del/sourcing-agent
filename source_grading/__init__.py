"""
source_grading/__init__.py — 核心创新 4：信源分级 S/A/B/C/D

等级定义：
- S 级：制度性信源（央媒、政府、学术、官方）
- A 级：头部权威媒体 + 头部行业报告
- B 级：地方媒体 + 垂直行业
- C 级：自媒体 + UGC
- D 级：未标明出处的内部材料 + 传闻

强制规则：
- 关键论断必须有 S 或 A 级支撑
- 多源交叉时至少 1 个 S/A 级
- C/D 级单用必须标"未核验"
"""

# 各数据源的默认等级
SOURCE_GRADES = {
    # 计划接入
    "1688": "A",          # 阿里 B2B
    "jd_industrial": "A", # 京东工业
    "alibaba_b2b": "A",   # 阿里巴巴国际站
    "pinduoduo": "B",     # 拼多多（B2C 综合）
    "weidian": "C",       # 微店（个人店）
    
    # 当前已实现
    "xianyu": "B",        # 闲鱼 C2C（公开搜索结果，但缺 B2B 信用）
    
    # 其他
    "taobao": "B",        # 淘宝（C2C）
    "internal_db": "D",   # 内部数据库
}


def get_grade(source_id: str) -> str:
    """获取数据源的信源等级"""
    return SOURCE_GRADES.get(source_id, "D")


def grade_to_label(grade: str) -> str:
    """等级转可读标签"""
    mapping = {
        "S": "制度性信源",
        "A": "权威信源",
        "B": "中等可信",
        "C": "低可信",
        "D": "未核验",
    }
    return mapping.get(grade, "未知")


__all__ = ["SOURCE_GRADES", "get_grade", "grade_to_label"]