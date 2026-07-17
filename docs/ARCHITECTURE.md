# AI Radar 系统架构文档

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户微信                              │
│                   (发送"生成今日报告")                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ iLink 协议
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  OpenClaw + ClawBot                          │
│              (微信官方个人 Agent 通道)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ 路由到 ai-radar Agent
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              TypeScript Layer (Agent 核心 + 交付)             │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Agent Core  │  │  Orchestrator│  │  Delivery          │  │
│  │  (LLM 提炼)  │  │  (端到端编排) │  │  (OpenClaw Skill)  │  │
│  └──────┬──────┘  └──────┬───────┘  └────────────────────┘  │
│         │                │                                   │
│  ┌──────┴──────┐  ┌──────┴───────┐                          │
│  │  Zod Schema │  │  Config      │                          │
│  │  (类型校验)  │  │  (环境配置)   │                          │
│  └─────────────┘  └──────────────┘                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ 读取 JSON
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Shared Contract Layer                       │
│                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ raw-intelligence.json│  │ daily-report.json   │           │
│  │ (JSON Schema SSoT)  │  │ (JSON Schema SSoT)  │           │
│  └─────────────────────┘  └─────────────────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │ 生成类型
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Python Layer (数据采集与预处理)                 │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Scrapers   │  │  Cleaners    │  │  Pipeline          │  │
│  │  (11源爬虫)  │  │  (数据清洗)   │  │  (编排入口)         │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Pydantic Models (从 JSON Schema 生成)               │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │ 输出
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     data/raw/                                │
│                radar_data.json (每日更新)                      │
└─────────────────────────────────────────────────────────────┘
```

## 2. 数据流

### 2.1 每日预采集流（定时触发）

```
Cron Job (每日 08:00)
    ↓
pipeline.py (并行调度 11 个 Scraper)
    ↓
每个 Scraper → scrape() → list[RawIntelligence]
    ↓
normalizer.py (清洗、去重、标准化)
    ↓
输出 data/raw/radar_data.json
```

### 2.2 用户触发流（微信消息）

```
用户微信："生成今日 AI 雷达报告"
    ↓
ClawBot (iLink) → OpenClaw
    ↓
OpenClaw 路由 → ai-radar Agent
    ↓
openclaw-skill.ts (TS Skill 入口)
    ↓
orchestrator.ts
    ├── 读取 data/raw/radar_data.json
    ├── 调用 Agent Core (LLM 提炼)
    │   ├── System Prompt (5 维度约束)
    │   ├── 输入: list[RawIntelligence]
    │   └── 输出: DailyAIRadarReport (Zod 校验)
    ├── formatter.ts (Markdown 排版)
    └── 返回给 OpenClaw → ClawBot → 用户微信
```

## 3. 技术选型

| 层 | 技术 | 版本 | 用途 |
|----|------|------|------|
| Python 运行时 | Python | 3.11+ | 数据采集层 |
| Python 包管理 | uv | latest | 依赖管理、虚拟环境 |
| Python HTTP | httpx | 0.27+ | 异步 HTTP 请求 |
| Python 解析 | beautifulsoup4 | 4.12+ | HTML 解析 |
| Python RSS | feedparser | 6.0+ | RSS/Atom 解析 |
| Python 浏览器 | playwright | 1.40+ | 需要 JS 渲染的页面抓取 |
| Python 类型 | pydantic | 2.5+ | 数据模型、JSON Schema 生成 |
| TS 运行时 | Node.js | 20+ | Agent 核心层 |
| TS 包管理 | pnpm | 9+ | 依赖管理 |
| TS 类型校验 | zod | 3.22+ | Agent 输出强类型校验 |
| TS AI SDK | ai (Vercel) | 3.0+ | LLM 调用抽象层 |
| TS 调度 | node-cron | 3.0+ | 定时任务 |
| 微信通道 | OpenClaw + ClawBot | latest | 官方 iLink 协议，合规推送 |
| LLM | Claude 3.5 Sonnet | - | 情报提炼主力模型 |

## 4. 类型同步策略

采用 **JSON Schema 作为 Single Source of Truth (SSoT)**：

```
shared/schema/raw-intelligence.json  (JSON Schema 定义)
         │                    │
         ▼                    ▼
    Python 侧              TS 侧
    pydantic generate       zod-to-json-schema (反向)
    → Pydantic Model        → Zod Schema
```

**工作流**：
1. 在 `shared/schema/` 中定义 JSON Schema
2. Python 侧：用 `datamodel-code-generator` 从 JSON Schema 生成 Pydantic 模型
3. TS 侧：手写 Zod schema（与 JSON Schema 对齐），或用工具生成
4. CI 中增加校验步骤，确保两侧类型与 JSON Schema 一致

## 5. 部署与调度

### 5.1 本地开发环境

```bash
# Python 环境
cd python && uv sync

# TS 环境
cd typescript && pnpm install

# 安装 OpenClaw 微信通道
npx -y @tencent-weixin/openclaw-weixin-cli@latest install
```

### 5.2 定时任务

```
┌─────────────────────────────────────────┐
│           node-cron (TS 侧)             │
│                                          │
│  每日 08:00                              │
│    └── spawn python pipeline.py          │
│        └── 输出 radar_data.json          │
│                                          │
│  用户触发 (随时)                          │
│    └── OpenClaw Skill → orchestrator.ts  │
│        └── 读取 radar_data.json          │
│        └── Agent 提炼 → 返回报告          │
└─────────────────────────────────────────┘
```

### 5.3 环境变量

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-xxx

# 数据源 API Keys (按需)
GITHUB_TOKEN=ghp_xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# OpenClaw
OPENCLAW_AGENT_ID=ai-radar
```

## 6. 目录结构说明

```
AI Radar/
├── docs/                    # 文档层：需求 + 架构
├── shared/schema/           # 契约层：JSON Schema SSoT
├── python/                  # 采集层：11 源爬虫 + 清洗
│   ├── src/models/          # Pydantic 模型（从 Schema 生成）
│   ├── src/scrapers/        # 爬虫适配器（可插拔）
│   ├── src/cleaners/        # 数据清洗
│   └── src/pipeline.py      # 编排入口
├── typescript/              # Agent 层：提炼 + 交付
│   ├── src/types/           # Zod Schema（从 Schema 生成）
│   ├── src/agent/           # Agent 核心逻辑
│   ├── src/delivery/        # OpenClaw Skill + 格式化
│   ├── src/orchestrator.ts  # 端到端编排
│   └── src/config.ts        # 配置管理
├── data/                    # 运行时数据
│   ├── raw/                 # Python 输出的原始 JSON
│   ├── reports/             # Agent 生成的报告
│   └── db/                  # SQLite (未来扩展)
└── scripts/                 # 运维脚本
```

## 7. 扩展性设计

### 7.1 新增数据源

只需 3 步：
1. 在 `python/src/scrapers/` 新建文件，实现 `ScraperInterface`
2. 在 `pipeline.py` 中注册新 Scraper
3. 在 `shared/schema/raw-intelligence.json` 的 `source` enum 中添加新值

### 7.2 更换 LLM

TS 侧通过 Vercel AI SDK 抽象 LLM 调用，更换模型只需修改 `config.ts` 中的模型配置。

### 7.3 多通道推送

Delivery 层采用策略模式，新增推送通道只需实现 `DeliveryInterface`。
