# 🤖 Sourcing-Agent｜MCP 多源采购 Agent 平台（TRIOI 版）

> **TRIOI 工程化闭环 + MCP 多源架构 + Agent Harness 哲学** — 把研究/分析/决策类 AI 任务的"群体思维、黑箱、幻觉、合规"四大根本问题，用工程化方法论解决。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![TRIOI](https://img.shields.io/badge/TRIOI-4%E9%98%B6%E6%AE%B5-green.svg)]()
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)]()
[![GOAI 2026](https://img.shields.io/badge/GOAI-2026-red.svg)](https://www.goaigroup.com)

[English](README.en.md) ｜ 中文

---

## 🎯 一句话定位

> **Sourcing-Agent = TRIOI 化 MCP 多源采购 Agent**，按 BOM 物料清单自动跨数据源调度搜索，4 维度评分，Top 3 推荐直接推送。

## 🧬 TRIOI 4 阶段流程（革新核心）

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Phase 1         │  │ Phase 2         │  │ Phase 3         │  │ Phase 4         │
│ 三角色并行       │→ │ 5 道门禁 DAG    │→ │ decision-log    │→ │ 交付 + 复盘     │
│ (认知隔离)       │  │ (质量过滤)       │  │ (决策追溯)       │  │ (可审计)         │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Phase 1：三角色并行（认知隔离 ⭐ 革新 1）

| 角色 | 职责 | 关键约束 |
|------|------|---------|
| **Explorer** | 调度 MCP 数据源、收集原始素材 | **只收集，不写、不评** |
| **Auditor** | 独立审计素材、查一致性 | **只挑刺，不改、不补** |
| **Integrator** | 综合产出最终报告 | **只综合，不重收** |

**独立 session + 独立 prompt + 独立工具集 + 互不可见**——解决 AI 群体思维。

### Phase 2：5 道门禁 DAG（拓扑依赖 ⭐ 革新 2）

```
        C1 语法门禁      C2 引用门禁
            │                │
            └────────┬───────┘
                     ▼
                 C3 一致性门禁
                     │
              ┌──────┴──────┐
              ▼             ▼
          C4 安全门禁   C5 可执行性门禁
```

| 门禁 | 检查 | 失败处理 |
|------|------|---------|
| **C1** 语法 | JSON/Markdown 可解析 | 重新格式化 |
| **C2** 引用 | 链接真实、信源等级 | 删/换信源 |
| **C3** 一致性 | Top 3 不矛盾 | 标红矛盾处 |
| **C4** 安全 | L1/L2/L3 分级（**不可绕过**） | 强制脱敏 |
| **C5** 可执行性 | 含下一步动作、责任主体 | 补 owner |

### Phase 3：decision-log（决策追溯 ⭐ 革新 3）

每个评分决策结构化记录：
- `context_snapshot`（上下文）
- `options_considered`（候选商品）
- `chosen`（最终选择）
- `rationale`（选择理由）
- `dissenting_opinions`（反对意见）
- `confidence`（信心度）

### Phase 4：交付三件套

1. **任务主交付**（Top 3 推荐 + 评分依据）
2. **decision-log.md**（决策追溯）
3. **gates-report.md**（5 道门禁结果）

## 🔌 MCP 多源架构

```
[用户 BOM 输入]
     ↓
[Master Agent — TRIOI 4 阶段]
     ↓
[MCP Registry — 数据源注册表]
     ├─→ 闲鱼 MCP Server（B 级 · 当前实现）
     ├─→ 1688 MCP Server（A 级 · 短期）
     ├─→ 京东工业 MCP Server（A 级 · 短期）
     ├─→ 拼多多 MCP Server（B 级 · 中期）
     └─→ 各企业自建 MCP Server
     ↓
[5 道门禁 DAG（拓扑依赖）]
     ↓
[飞书推送 + 多维表格]
```

**信源分级**（每个数据源标记等级，关键论断必须有 S/A 级支撑）：

| 等级 | 数据源 | 可信度 |
|------|--------|--------|
| **A** | 1688 / 京东工业 / 阿里巴巴 B2B | 高 |
| **B** | 闲鱼 / 拼多多 / 淘宝 | 中 |
| **C** | 微店 / 自媒体 | 低（需标"未核验"） |
| **D** | 内部数据库 / 传闻 | 最低（不可单独支撑关键论断） |

## 🎬 场景引擎（YAML 配置化）

```bash
/bom <清单>            # BOM 物料采购
/price-compare <物料>  # 跨平台价格对比
/vendor-eval <名称>    # 供应商深度评估
/bom-history           # 历史追溯
```

## ✨ TRIOI 革新 vs 普通 AI 方法论

| 维度 | 普通方法论 | TRIOI 革新 | 效果 |
|------|-----------|-----------|------|
| 角色 | 一个 LLM 串行 | **3 独立 session 互不可见** | 解决群体思维 |
| 质量检查 | 全跑或全不跑 | **拓扑依赖 + fail-fast** | 节省 50% 时间 |
| 决策 | 黑箱 | **decision-log 结构化** | 可审计、可质疑 |
| 信源 | 不分级 | **S/A/B/C/D 强规则** | 解决幻觉 |
| 安全 | 用户要求就绕过 | **L3 不可绕过** | 解决隐私泄露 |
| 工作流 | 每次重写 | **YAML 场景引擎** | 一行触发 |

## 🚀 快速开始

```bash
git clone https://github.com/itr-del/sourcing-agent.git
cd sourcing-agent
pip install -r requirements.txt
playwright install chromium

# 跑 BOM 跑批
python3 master_agent.py --bom bom_tasks.json

# TRIOI 4 阶段流程（带决策日志 + 门禁报告）
python3 master_agent.py --bom bom_tasks.json --gates NORMAL
```

## 📁 文件结构

```
sourcing-agent/
├── master_agent.py           # TRIOI 4 阶段流程编排
├── roles/                    # TRIOI 3 角色（认知隔离）
│   ├── explorer.py           # 数据收集
│   ├── auditor.py            # 独立审计
│   └── integrator.py         # 综合产出
├── gates/                    # 5 道门禁（拓扑 DAG）
│   ├── c1_syntax.py
│   ├── c2_reference.py
│   ├── c3_consistency.py
│   ├── c4_security.py        # L3 不可绕过
│   └── c5_executable.py
├── decision_log/             # 决策追溯（YAML 结构化）
│   └── logger.py
├── source_grading/           # 信源分级 S/A/B/C/D
│   └── __init__.py
├── scenes/                   # 场景引擎（YAML 配置）
│   └── __init__.py
├── data_sources/             # MCP adapter 包
│   ├── base.py
│   ├── registry.py
│   └── xianyu_source.py
├── scoring/                  # 4 维度评分引擎
├── push/                     # 飞书推送
├── run_pipeline.py
├── bom_tasks.json
└── README.md
```

## 🎯 适用场景

- 🛶 **桨板/水上运动硬件**（亲历案例）
- 🤖 **机器人创业团队**
- 🚁 **无人机硬件项目**
- 🥽 **AI 智能眼镜供应链**
- 🏭 **IoT 设备创业**

## 🔒 边界声明

> ⚠️ Sourcing-Agent 是辅助采购决策的工具，**不替代专业采购人员的判断**。
> - Agent 推荐 ≠ 自动下单（所有决策必须人工确认）
> - 仅适用公开数据源，不抓取个人隐私
> - 不适用于金融/医疗/汽车控制/教育评价等高风险场景
> - L3 字段强制脱敏（不可绕过）

## 📜 License

**MIT License** © 2026 王嘉亿 (itr-del)

## 🏆 参赛信息

本项目参加 **GOAI 2026 无界应用 · AI+工业制造赛道**。

办赛方：GOAI 组委会 · 魔搭（阿里达摩院）· 蚂蚁集团

**参赛亮点**：
- TRIOI 4 阶段方法论（AI 任务的工程化闭环）
- MCP 多源架构（每个企业可自主入驻）
- 5 道门禁（拓扑依赖 DAG）
- decision-log 决策追溯（可审计）
- 信源分级 S/A/B/C/D
- L3 不可绕过（安全底线）

## 📞 联系

- **GitHub**: [@itr-del](https://github.com/itr-del)
- **项目主页**: https://github.com/itr-del/sourcing-agent
- **邮箱**: 13918029394@163.com

---

<sub>🤖 Sourcing-Agent — TRIOI + MCP + Agent Harness 哲学融合的工程化多源采购 Agent 平台</sub>