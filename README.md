# 🤖 Sourcing-Agent｜面向中小制造企业的 AI 采购工程师

> **多源采购 Agent 平台 — 通过 MCP 协议接入各企业供应商，让 BOM 物料采购从"手搓找熟人"升级为"Agent 自动跨平台比价"**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![GOAI 2026](https://img.shields.io/badge/GOAI-2026-red.svg)](https://www.goaigroup.com)

[English](README.en.md) ｜ 中文

---

## 🎯 一句话定位

> **Sourcing-Agent = 通用 BOM 采购 Agent 平台**，按物料清单（BOM）每天自动跨平台比价，4 维度智能评分，Top 3 推荐直接推送。让中小制造企业也能享受大企业级采购数字化能力。

## 💎 为什么是这个项目？

在中国制造业占全球 **30%**、AI 渗透率仅 **9.6%**（vs 国际平均 34%）的当下，中小企业"手搓到量产"最痛的环节是**采购**——找源慢、比价难、决策无依据、风险不可控。

传统方案要么贵（SAP Ariba 年费 100 万）、要么缺评分（1688）、要么缺 B2B 信用（闲鱼）。**Sourcing-Agent 填补这个空白**。

## ✨ 核心特性

### 🔌 多源采购（MCP 协议 + Agent Talk）

- **当前已实现**：闲鱼 data source（Playwright + cookie 注入）
- **未来接入**（通过 MCP 协议）：
  - 1688 MCP Server
  - 京东工业 MCP Server
  - 拼多多 MCP Server
  - 阿里巴巴 B2B MCP Server
  - 各企业自建 MCP Server
- **架构**：每个数据源都是一个独立的 MCP adapter，主 Agent 通过统一接口调度

### ⭐ 4 维度智能评分

```
final_score = 关键词匹配 × 0.25
            + 价格区间   × 0.25
            + 卖家信用   × 0.30
            + 商品质量   × 0.20
```

权重依据：**信用 30% 最高**——跨平台采购最大风险源是供应商信用，我们用 AI 把长尾 C2C 信用转化为可量化的采购决策依据。

### 📤 全自动推送

- 飞书消息推送（实时）
- 飞书多维表格同步（结构化记录）
- cron 每日 10:00 自动跑批（无需人工）
- 邮件 / Webhook / 自定义渠道（未来扩展）

### 🛠️ 真实场景验证

已在"桨板跟拍船"硬件项目（29 件 BOM）端到端跑通：

| 指标 | 数据 |
|------|------|
| 跑通率 | **100%**（29/29）|
| 跑批时间 | **5 分钟** |
| TOP 1 信用分布 | **100% 信用"极好"** |
| 平均评分 | **0.68** |

## 🏗️ 技术架构

```
[用户 BOM 输入]
     ↓
[Master Agent（任务规划）]
     ↓
[MCP Registry]
     ├─→ 闲鱼 MCP Server（当前实现）
     ├─→ 1688 MCP Server（未来）
     ├─→ 京东工业 MCP Server（未来）
     └─→ ... 更多企业 MCP Server
     ↓
[4 维度评分引擎]
     ↓
[Top 3 推荐 + 评分依据]
     ↓
[飞书推送 + 多维表格]
     ↓
[每日 cron 自动运行]
```

### 当前实现（v0.1）

- ✅ Master Agent（任务规划 + 异常处理）
- ✅ 闲鱼 MCP adapter（Playwright + cookie 注入）
- ✅ 4 维度评分引擎（关键词/价格/信用/质量）
- ✅ 飞书推送（消息 + 多维表格）
- ✅ cron 定时任务

### 未来规划（v1.0+）

- 🔜 1688 MCP adapter
- 🔜 京东工业 MCP adapter
- 🔜 拼多多 MCP adapter
- 🔜 MCP Registry（动态注册/发现）
- 🔜 Agent Talk 平台接入（让其他 Agent 调用 Sourcing-Agent）

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/itr-del/sourcing-agent.git
cd sourcing-agent

# 2. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env：填入 FEISHU_APP_ID / SECRET / 数据源凭证

# 4. 准备 BOM
cp bom_tasks.example.json bom_tasks.json

# 5. 运行跑批
python3 run_pipeline.py
```

## 📦 文件结构

```
sourcing-agent/
├── master_agent.py          # 主 Agent（任务规划）
├── run_pipeline.py          # 调度脚本
├── data_sources/            # 数据源 MCP adapter
│   ├── base.py              # MCP 数据源基类
│   ├── registry.py          # 数据源注册表
│   └── feishu_b_mcp.py      # 闲鱼 MCP adapter（当前实现）
├── scoring/                 # 评分引擎
│   └── four_dimension.py    # 4 维度评分
├── push/                    # 推送层
│   ├── feishu_message.py    # 飞书消息
│   └── feishu_bitable.py    # 飞书多维表格
├── cron/                    # 定时任务
├── bom_tasks.example.json   # BOM 模板
├── output/                  # 跑批产物
└── tests/                   # 测试
```

## 📚 文档导航

- [DEMO.md](docs/DEMO.md) — Demo 视频 + 演示指南
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 详细架构 + MCP 协议设计
- [ROADMAP.md](docs/ROADMAP.md) — 未来规划
- [COMPLIANCE.md](docs/COMPLIANCE.md) — 数据合规与边界声明
- [GOAI_SUBMISSION.md](docs/GOAI_SUBMISSION.md) — GOAI 参赛材料

## 🎯 适用场景

- 🛶 **桨板/水上运动硬件**（亲历案例）
- 🤖 **机器人创业团队**
- 🚁 **无人机硬件项目**
- 🚗 **智能车/汽车后市场改装**
- 🥽 **AI 智能眼镜供应链**
- 🏭 **IoT 设备创业**
- 🎓 **高校实验室物料采购**

## 🔒 边界声明

> ⚠️ Sourcing-Agent 是**辅助采购决策的工具**，不替代专业采购人员的判断。
> - Agent 推荐 ≠ 自动下单（所有决策必须人工确认）
> - 仅适用公开数据源，不抓取个人隐私
> - 不适用于金融/医疗/汽车控制/教育评价等高风险场景
> - 详见 [COMPLIANCE.md](docs/COMPLIANCE.md)

## 📜 License

**MIT License** © 2026 王嘉亿 (itr-del)

## 🏆 参赛信息

本项目参加 **GOAI 2026 无界应用 · AI+工业制造赛道**。

办赛方：GOAI 组委会 · 魔搭（阿里达摩院）· 蚂蚁集团

## 📞 联系

- **GitHub**: [@itr-del](https://github.com/itr-del)
- **项目主页**: https://github.com/itr-del/sourcing-agent
- **邮箱**: 待提供

---

<sub>🤖 Sourcing-Agent — 让中小制造企业也能享受大企业级采购数字化能力</sub>