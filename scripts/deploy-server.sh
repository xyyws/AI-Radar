#!/bin/bash
# AI Radar 云服务器部署脚本
# 在阿里云 OpenClaw 镜像服务器上执行
set -e

echo "=== AI Radar 云服务器部署 ==="

# 1. 安装 Python 依赖
echo "[1/5] 安装 Python 依赖..."
pip3 install pydantic httpx beautifulsoup4 feedparser

# 2. 安装 Node.js 依赖
echo "[2/5] 安装 Node.js 依赖..."
npm install

# 3. 创建数据目录
echo "[3/5] 创建数据目录..."
mkdir -p data/raw data/reports data/logs

# 4. 配置环境变量
echo "[4/5] 配置环境变量..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Gemini
GOOGLE_GENERATIVE_AI_API_KEY=你的Key粘贴到这里

# 数据源 API Keys (可选)
GITHUB_TOKEN=
TWITTER_BEARER_TOKEN=

# 输出
DATA_DIR=./data
EOF
    echo "请编辑 .env 文件，填入你的 Gemini API Key"
fi

# 5. 测试数据采集
echo "[5/5] 测试数据采集..."
python3 -m python.src.pipeline --sources github

echo ""
echo "=== 部署完成 ==="
echo ""
echo "接下来："
echo "1. 编辑 .env 填入 API Key"
echo "2. 运行完整采集: python3 -m python.src.pipeline --sources github arxiv huggingface openai deepmind"
echo "3. 测试 Agent: npx tsx typescript/src/orchestrator.ts refine"
echo "4. 配置 OpenClaw cron 定时推送"
echo ""
echo "=== 配置 OpenClaw 每日定时推送 ==="
echo "openclaw cron add --name ai-radar-daily --agent ai-radar --cron '30 7 * * *' --message '请生成今日 AI 情报报告' --channel openclaw-weixin --announce --timeout-seconds 120"
