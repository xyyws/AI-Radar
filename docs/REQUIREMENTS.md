# AI Radar 业务需求文档

## 1. 产品定位

AI Radar 是一个 **AI 情报过滤系统**，不是新闻聚合器。

核心理念：在 AI 行业信息严重过载的背景下，从 11 个数据源中自动筛选、提炼出具**范式转变**或**产业颠覆性**的核心事件，输出 500 字每日快报。

**不做**：新闻搬运、原文复制、公关稿转发。
**要做**：情报提炼、趋势研判、商业价值分析。

## 2. 目标用户

| 用户画像 | 核心诉求 |
|----------|----------|
| AI 从业者 | 快速了解行业动态，不错过关键技术突破 |
| 技术投资人 | 筛选有商业价值的 AI 进展，辅助投资决策 |
| 技术决策者 | 了解大厂动向和技术趋势，指导团队技术选型 |
| AI 研究者 | 追踪学术前沿和开源生态变化 |

## 3. 功能需求

### 3.1 数据采集（11 源）

| 数据源 | 类型 | 采集方式 | 优先级 |
|--------|------|----------|--------|
| GitHub Trending | 开源趋势 | API / 页面抓取 | P0 |
| Arxiv | 学术论文 | RSS / API | P0 |
| OpenAI Blog | 大厂动态 | RSS / 页面抓取 | P0 |
| Anthropic Blog | 大厂动态 | RSS / 页面抓取 | P0 |
| Google DeepMind | 大厂动态 | RSS / 页面抓取 | P1 |
| Meta AI | 大厂动态 | RSS / 页面抓取 | P1 |
| HuggingFace | 开源生态 | API / 页面抓取 | P0 |
| X (Twitter) | 社交媒体 | API / 抓取 | P1 |
| Reddit | 社区讨论 | API | P1 |
| 微信公众号 | 中文生态 | RSS 聚合 / 抓取 | P2 |
| 知乎 | 中文社区 | 页面抓取 | P2 |

### 3.2 Agent 情报提炼

Agent 角色定位：**顶级科技投资人 + 技术专家**

提炼维度（5 个核心问题）：

1. **是什么** — 事件/技术/产品的本质描述
2. **为什么重要** — 技术范式转变或产业颠覆性分析
3. **哪些公司开始用了** — 商业采纳情况（无线索时基于技术特性做商业研判，标注"研判"）
4. **未来趋势** — 短期和中期发展预判
5. **关键词/新名词** — 提取新出现的技术术语和概念

输出格式：
- 500 字中文快报
- 3-5 个核心事件
- 每个事件包含上述 5 个维度
- 末尾附关键词列表

### 3.3 微信推送

通过 **OpenClaw + 微信 ClawBot**（官方 iLink 协议）实现安全合规的个人 Agent 推送。

**触发方式**：用户在微信中发送"生成今日 AI 雷达报告"等指令，Agent 实时响应。

**接入流程**：
1. 安装 OpenClaw 微信通道：`npx -y @tencent-weixin/openclaw-weixin-cli@latest install`
2. 绑定 Agent：`openclaw agents add ai-radar`
3. 扫码配对：`openclaw channels login --channel openclaw-weixin`
4. 将 TS 提炼逻辑注册为 OpenClaw Skill（`get_today_radar`）

**ClawBot 安全特性**：
- 纯私密通道，其他微信用户无法添加
- 仅限单聊，不能被拉入群
- 采用腾讯官方 iLink 协议，不涉及自动化外挂，不封号

## 4. 非功能需求

| 需求 | 描述 |
|------|------|
| 定时预采集 | Python 爬虫每日定时执行，预写入 `radar_data.json` |
| 容错机制 | 单个数据源采集失败不影响整体流程，记录错误日志 |
| 可扩展性 | 新增数据源只需实现 `ScraperInterface` 基类 |
| 类型安全 | Python (Pydantic) ↔ TypeScript (Zod) 通过 JSON Schema 保持类型同步 |
| 隐私安全 | API Key 通过 `.env` 管理，不提交到代码仓库 |

## 5. 用户交互流程

```
用户在微信发送："生成今日 AI 雷达报告"
         ↓
ClawBot (iLink 协议) → OpenClaw
         ↓
OpenClaw 路由到 ai-radar Agent (TS Skill)
         ↓
TS Skill 读取 data/raw/radar_data.json（Python 预采集）
         ↓
Agent 调用大模型，按 5 维度提炼
         ↓
Zod 校验输出格式
         ↓
Markdown 排版 → 通过 ClawBot 回复到微信
```

## 6. 数据源字段映射

所有数据源最终统一为 `RawIntelligence` 格式：

```typescript
interface RawIntelligence {
  source: 'github' | 'arxiv' | 'openai' | 'anthropic' | 'deepmind' | 'meta' | 'huggingface' | 'twitter' | 'reddit' | 'wechat' | 'zhihu';
  title: string;
  url: string;
  rawContent: string;        // 原始内容（标题 + 摘要 / 正文片段）
  publishedAt: string;       // ISO 8601 时间戳
  language: 'en' | 'zh';
  metadata: Record<string, unknown>;  // 源特有字段
}
```

## 7. 输出报告格式

```typescript
interface DailyAIRadarReport {
  date: string;              // YYYY-MM-DD
  summary: string;           // 500 字总览
  events: RadarEvent[];
  keywords: string[];        // 关键词/新名词列表
}

interface RadarEvent {
  title: string;
  what: string;              // 是什么
  whyImportant: string;      // 为什么重要
  adoption: string;          // 哪些公司开始用了
  trend: string;             // 未来趋势
  tags: string[];
}
```
