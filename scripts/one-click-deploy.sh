#!/bin/bash
# AI Radar 一键部署脚本 — 粘贴到阿里云服务器终端执行
set -e

echo "=== AI Radar 一键部署 ==="

# 安装依赖
pip3 install pydantic httpx beautifulsoup4 feedparser 2>/dev/null || pip install pydantic httpx beautifulsoup4 feedparser

# 创建项目目录
mkdir -p /opt/ai-radar
cd /opt/ai-radar

# 下载项目（从本地 scp 或 git，这里用内联方式创建核心文件）
mkdir -p python/src/{models,scrapers,cleaners} typescript/src/{types,agent,delivery} shared/schema data/{raw,reports,logs} scripts

# 安装 npm 依赖
cat > package.json << 'PKGEOF'
{
  "name": "ai-radar",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "orchestrate": "tsx typescript/src/orchestrator.ts"
  },
  "dependencies": {
    "zod": "^3.22.0",
    "ai": "^3.0.0",
    "@ai-sdk/google": "^1.0.0",
    "node-cron": "^3.0.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "tsx": "^4.7.0",
    "@types/node": "^20.10.0",
    "@types/node-cron": "^3.0.0"
  }
}
PKGEOF

npm install 2>/dev/null || echo "npm install failed, try manually"

# 创建 .env
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
GOOGLE_GENERATIVE_AI_API_KEY=你的Key粘贴到这里
ENVEOF
    echo ">>> 请编辑 /opt/ai-radar/.env 填入 Gemini API Key <<<"
fi

# 测试网络连通性
echo "测试网络..."
curl -s https://github.com/trending -o /dev/null -w "GitHub: %{http_code}\n" --max-time 10
curl -s https://export.arxiv.org/rss/cs.AI -o /dev/null -w "Arxiv: %{http_code}\n" --max-time 10

echo ""
echo "=== 基础环境就绪 ==="
echo ""
echo "接下来需要："
echo "1. 编辑 .env: nano /opt/ai-radar/.env"
echo "2. 上传项目代码: scp -r 'AI Radar'/* root@服务器IP:/opt/ai-radar/"
echo "3. 测试采集: python3 -m python.src.pipeline --sources github"
echo "4. 配置定时: openclaw cron add --name ai-radar-daily --agent ai-radar --cron '30 7 * * *' --message '请生成今日AI情报报告' --channel openclaw-weixin --announce"
