# AI Radar

> 每日自动采集 11 个 AI 数据源，智能过滤 + LLM 提炼，通过 Server酱 / 微信 ClawBot 自动推送 500 字投资级情报简报。

## 功能特性

- **11 源数据采集**：GitHub Trending、Arxiv、OpenAI、DeepMind、HuggingFace、Reddit、Twitter、微信公众号、知乎等
- **智能过滤引擎**：源特异性评分（GitHub stars 对数 + 时间衰减、Reddit score + comments 等），100+ 原始数据精选 top 30
- **证据溯源**：每条情报自动附带原始 URL、关键指标、发布时间，确保报告可追溯
- **LLM 深度提炼**：小米 mimo-v2.5-pro 模型，投资级自由写作风格，非模板化输出
- **双通道推送**：Server酱（稳定通知）+ 微信 ClawBot（交互式查询）
- **全链路自动化**：crontab 定时执行，零人工干预

## 架构

```
┌─────────────────────────────────────────────────┐
│              调度层 (Linux crontab)               │
├─────────────────────────────────────────────────┤
│  采集层 (Python)  │  过滤层  │  提炼层 (LLM)    │
│  httpx + bs4      │  评分引擎 │  mimo-v2.5-pro  │
├─────────────────────────────────────────────────┤
│              交付层 (Server酱 + ClawBot)          │
└─────────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 |
|---|---|
| 数据采集 | Python 3.11 · httpx · BeautifulSoup4 · feedparser |
| 智能过滤 | 自研评分算法 · 相似度去重 · 时间衰减 |
| Agent 提炼 | Anthropic SDK · Xiaomi mimo-v2.5-pro |
| 推送交付 | Server酱 API · OpenClaw ClawBot (iLink) |
| 定时调度 | Linux crontab · Shell 脚本 |
| 类型同步 | Pydantic ↔ Zod (JSON Schema SSoT) |
| 部署 | 阿里云 ECS · Ubuntu |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- 小米 Mimo API Key
- Server酱 SendKey

### 安装

```bash
# 克隆项目
git clone https://github.com/xyyws/AI-Radar.git
cd AI-Radar

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 配置

编辑 `.env`：

```env
# 小米 Mimo API Key
MIMO_API_KEY=你的Key

# Server酱 SendKey（SCT 开头）
SERVER_CHAN_KEY=SCTxxxxxxxxxxxx

# 推送开关
PUSH_ENABLED=true
```

### 运行

```bash
# 手动采集
python -m python.src.pipeline --sources github arxiv huggingface openai deepmind

# 手动生成报告
bash scripts/generate-report.sh

# 手动推送
bash scripts/daily-push.sh
```

### 定时任务

```bash
# 添加 crontab
crontab -e

# 每天 7:00 采集，7:30 推送
0 7 * * * cd /path/to/AI-Radar && python3 -m python.src.pipeline --sources github arxiv huggingface openai deepmind >> data/logs/collect.log 2>&1
30 7 * * * bash /path/to/AI-Radar/scripts/daily-push.sh
```

## 数据源

| 数据源 | 状态 | 采集方式 |
|--------|------|---------|
| GitHub Trending | ✓ | httpx + BeautifulSoup |
| Arxiv | ✓ | feedparser (RSS) |
| OpenAI Blog | ✓ | feedparser (RSS) |
| DeepMind Blog | ✓ | feedparser (RSS) |
| HuggingFace | ✓ | hf-mirror.com 国内镜像 API |
| Reddit | ✓ | httpx + JSON API |
| Twitter/X | ○ | 需要 Bearer Token |
| 微信公众号 | ○ | 需要 RSS 聚合 |
| 知乎 | ○ | 需要登录态 |
| Anthropic Blog | ○ | 服务器网络受限 |
| Meta AI Blog | ○ | 服务器网络受限 |

## 项目结构

```
AI-Radar/
├── python/                    # 数据采集层
│   └── src/
│       ├── scrapers/          # 11 源爬虫适配器
│       ├── cleaners/          # 数据清洗 + 智能过滤
│       ├── models/            # Pydantic 数据模型
│       └── pipeline.py        # 采集编排入口
├── typescript/                # Agent 核心 + 交付层
│   └── src/
│       ├── agent/             # LLM 调用 + 输出解析
│       ├── delivery/          # 推送通道（Server酱 + ClawBot）
│       ├── types/             # Zod Schema
│       ├── generate-report.ts # 独立报告生成脚本
│       └── orchestrator.ts    # 端到端编排
├── shared/schema/             # JSON Schema (类型同步 SSoT)
├── scripts/                   # Shell 脚本
├── data/                      # 运行时数据（已 gitignore）
└── docs/                      # 架构文档
```

## 每日运行流程

```
7:00  crontab → Python 采集 5 源数据 → radar_data.json
7:30  crontab → 生成报告 → Server酱 + ClawBot 双推微信
```

## 简历亮点

- **多源异构融合**：针对不同数据源设计独立评分策略，100+ 条精选 top 30
- **证据溯源**：每条情报附原始 URL + 关键指标，解决 LLM 幻觉问题
- **零人工干预**：从采集到推送全自动，每日运营成本趋近于零
- **双通道保障**：Server酱 + ClawBot 并行推送，消息必达
- **可扩展架构**：新增数据源只需实现 ScraperInterface

## License

MIT
