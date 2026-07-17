#!/bin/bash
# 每日定时推送脚本 — crontab 调用
# 1. 生成报告 2. 通过 OpenClaw webhook 推送到微信
cd /opt/ai-radar

LOG_FILE="data/logs/daily-push.log"
mkdir -p data/logs

echo "[$(date)] 开始每日推送" >> "$LOG_FILE"

# Step 1: 生成报告
REPORT=$(bash scripts/generate-report.sh 2>>"$LOG_FILE")

if [ -z "$REPORT" ]; then
    echo "[$(date)] 报告生成失败" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date)] 报告生成成功，长度: ${#REPORT}" >> "$LOG_FILE"

# Step 2: 保存报告
TODAY=$(date +%Y-%m-%d)
echo "$REPORT" > "data/reports/$TODAY.txt"

# Step 3: 通过 OpenClaw 发送消息到微信
# 使用 OpenClaw HTTP API 发送
curl -s --max-time 30 \
    "http://127.0.0.1:18743/api/send" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer c7fb375389a1b37ffc7e7a0b3ca9b8d6" \
    -d "$(python3 -c "
import json
report = '''$REPORT'''
print(json.dumps({
    'channel': 'openclaw-weixin',
    'to': 'o9cq80_dxx05q_9eq6fs7mlu-wt4@im.wechat',
    'message': report
}, ensure_ascii=False))
")" >> "$LOG_FILE" 2>&1

echo "[$(date)] 推送完成" >> "$LOG_FILE"
