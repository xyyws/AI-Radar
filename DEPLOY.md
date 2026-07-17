# AI Radar 云服务器部署指南

## 前提条件
- 阿里云服务器（OpenClaw 预装镜像）
- Gemini API Key
- 已通过 OpenClaw 微信扫码配对

## 部署步骤

### 1. 上传代码到服务器

```bash
# 在本地执行
scp -r "C:/Users/041120XL/Desktop/AI Radar" root@你的服务器IP:/opt/ai-radar
```

### 2. SSH 登录服务器

```bash
ssh root@你的服务器IP
cd /opt/ai-radar
```

### 3. 运行部署脚本

```bash
chmod +x scripts/deploy-server.sh
bash scripts/deploy-server.sh
```

### 4. 配置 API Key

```bash
nano .env
# 填入: GOOGLE_GENERATIVE_AI_API_KEY=你的Key
```

### 5. 测试完整流程

```bash
# 数据采集
python3 -m python.src.pipeline --sources github arxiv huggingface openai deepmind

# Agent 提炼
npx tsx typescript/src/orchestrator.ts refine
```

### 6. 配置 OpenClaw 每日定时推送

```bash
# 确保 gateway 运行中
openclaw gateway start

# 添加每日 8:00 定时任务
openclaw cron add \
  --name "ai-radar-daily" \
  --agent ai-radar \
  --cron "30 7 * * *" \
  --message "请生成今日 AI 情报报告" \
  --channel openclaw-weixin \
  --announce \
  --timeout-seconds 120

# 验证定时任务
openclaw cron list
```

### 7. 配置数据采集定时任务

```bash
# 添加 crontab 定时采集（每天 7:00）
crontab -e
# 添加以下行:
0 7 * * * cd /opt/ai-radar && python3 -m python.src.pipeline --sources github arxiv huggingface openai deepmind >> data/logs/collect.log 2>&1
```

## 完成后的运行流程

```
每天 7:00  →  crontab 触发 Python 数据采集
每天 7:30  →  OpenClaw cron 触发 Agent 提炼 + 微信推送
每天 8:00  →  你的微信 ClawBot 收到今日 AI 情报
```

## 常见问题

**Q: OpenClaw cron 报错 "scope upgrade pending approval"**
A: 在微信 ClawBot 中发送任意消息，触发配对授权，然后重试 cron add 命令。

**Q: 数据采集失败**
A: 检查网络连通性: `curl -s https://github.com/trending -o /dev/null -w "%{http_code}"`

**Q: Agent 提炼失败**
A: 检查 .env 中的 API Key 是否正确: `cat .env | grep GOOGLE`
