@echo off
chcp 65001 >nul
cd /d "C:\Users\041120XL\Desktop\AI Radar"

echo [%date% %time%] AI Radar 每日任务开始 >> data\logs\daily.log

echo [1/2] 数据采集...
python -m python.src.pipeline --sources github arxiv huggingface openai deepmind >> data\logs\daily.log 2>&1

echo [2/2] Agent 提炼...
npx tsx --no-warnings typescript/src/orchestrator.ts refine >> data\logs\daily.log 2>&1

echo [%date% %time%] AI Radar 每日任务完成 >> data\logs\daily.log
