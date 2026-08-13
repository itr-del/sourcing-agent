# 🛶 xianyu-bom-hunter

> 闲鱼 BOM 自动化采购 Agent — 按硬件物料清单，每天自动跑闲鱼搜索、4 维度评分、推送 TOP 3 到飞书。

为"桨板跟拍船"项目（29 件 BOM）设计，已成功跑通全量搜索 → 评分 → 推送 → 飞书多维表格同步。

## ✨ 核心能力

- 🛒 **闲鱼自动搜索**：Playwright + cookie 注入，无登录墙
- ⭐ **4 维度智能评分**：关键词匹配 + 价格区间 + 卖家信用 + 商品质量
- 📊 **TOP 3 推荐**：每件物料挑 3 个最匹配的卖家
- 💬 **飞书推送**：HTML 报告 + Markdown 摘要 + bitable 同步
- ⏰ **定时任务**：每日 10:00 自动跑（cronjob）

## 🏆 4 维度评分公式

```
final_score = 关键词匹配 × 0.25 + 价格区间 × 0.25 + 卖家信用 × 0.30 + 商品质量 × 0.20
```

权重说明：
- **卖家信用 30%**（最重要）
- **关键词匹配 25%** + **价格区间 25%**
- **商品质量 20%**（包邮/全新/想要数加权）

## 📦 安装

```bash
git clone https://github.com/itr-del/xianyu-bom-hunter.git
cd xianyu-bom-hunter
pip install playwright httpx
playwright install chromium
```

## 🔑 配置 Cookie（关键！）

闲鱼搜索需要登录态。**不要把你的 cookie 提交到 git！**（已加入 .gitignore）

1. 在 Kiwi Browser / Chrome 安装 Cookie Editor 扩展
2. 登录 https://www.goofish.com
3. 导出 cookie 为 JSON 格式
4. 保存到 `cookies/xianyu.json`

## 🚀 使用

### 单次跑批

```bash
python3 run_pipeline.py
```

### 跑完后推送飞书

```bash
python3 feishu_push.py
```

### 同步到飞书多维表格

```bash
python3 feishu_bitable.py
```

## 📁 文件结构

```
xianyu-bom-hunter/
├── xianyu_search.py      # 主爬虫：Playwright + cookie + 4维度评分
├── run_pipeline.py        # 调度：multiprocessing Pool + 1路串行 + 3秒间隔
├── feishu_push.py         # 飞书消息推送（HTML附件 + Markdown摘要）
├── feishu_bitable.py      # 飞书多维表格 upsert
├── bom_tasks.json         # 29 件 BOM 物料清单
├── cookies/
│   └── xianyu.json        # 闲鱼登录 cookie（gitignore，必须自己填）
└── output/                # 跑批产物（gitignore）
    ├── bom_hunt_report.md
    ├── bom_hunt_report.html
    └── search_results.json
```

## 🛶 BOM 物料

29 件物料，分 3 组：

- **方案 A（7件）**：低成本入门 — 打窝船 + L298N + ESP32-S3 + GPS + 蓝牙 + GoPro5 + 2S 锂电池
- **方案 B（16件）**：高端进阶 — Pixhawk + 树莓派4B + Coral TPU + GoPro9 + Storm32 云台 + ...
- **共用（6件）**：B6AC 充电器 + O型圈 + 电烙铁 + 热缩管 + 万用表 + 尼龙扎带

详见 `bom_tasks.json`。

## ⚙️ 核心参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 并发数 | 1 | 服务器内存仅 2GB，必须串行 |
| 请求间隔 | 3秒 | 避开闲鱼风控 |
| 超时 | 75秒/任务 | 单任务超过 75s 跳过 |
| 浏览器 | Chromium | headless + 阻塞图片/字体 |

## 🐛 已知坑

1. **不要多路并发** — 2GB 内存服务器会爆 swap
2. **必须 3 秒间隔** — 闲鱼限流，频繁请求会触发"商品列表加载中"
3. **cookie 7-30 天失效** — 关键字段：`_m_h5_tk`, `token`, `sid`, `unb`
4. **v6 卡死 bug** — 长跑可能触发 chromium worker hang，重启即可

## 📜 License

MIT

## 🙏 致谢

- [playwright-python](https://github.com/microsoft/playwright-python)
- [goofish](https://www.goofish.com) — 闲鱼
- [飞书开放平台](https://open.feishu.cn)