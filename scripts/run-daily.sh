#!/bin/bash
# 端到端每日任务：采集 + 提炼 + 推送
set -e

cd "$(dirname "$0")/.."
echo "=== AI Radar 每日任务 ==="

echo "[1/3] 数据采集..."
python -m python.src.pipeline

echo "[2/3] Agent 提炼..."
npx tsx typescript/src/orchestrator.ts refine

echo "[3/3] 推送到微信..."
npx tsx typescript/src/orchestrator.ts push

echo "=== 每日任务完成 ==="
