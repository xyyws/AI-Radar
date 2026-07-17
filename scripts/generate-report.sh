#!/bin/bash
# 轻量报告生成脚本 — 直接调小米 API，不依赖 Node.js
cd /opt/ai-radar

DATA_FILE="data/raw/radar_data.json"
REPORT_DIR="data/reports"
TODAY=$(date +%Y-%m-%d)
REPORT_FILE="$REPORT_DIR/$TODAY.txt"

# 检查数据
if [ ! -f "$DATA_FILE" ] || [ "$(python3 -c "import json; d=json.load(open('$DATA_FILE')); print(d.get('total_items',0))")" = "0" ]; then
    echo "数据未采集" >&2
    exit 1
fi

# 提取 top 30 条数据
PAYLOAD=$(python3 -c "
import json
with open('$DATA_FILE') as f:
    data = json.load(f)
items = [{'source': i['source'], 'title': i['title'], 'rawContent': i.get('rawContent','')[:500]} for i in data['items'][:30]]
print(json.dumps(items, ensure_ascii=False))
")

SYSTEM='你是顶级科技投资人兼 AI 技术专家。你有预采集的数据，不需要搜索。

写法自由，不要用固定模板。每个事件的写法根据内容决定。
排除：公关稿、营销内容、小版本更新。

输出格式：
📡 AI Radar {日期}
{一句话定调}
{正文：3-5个事件，自由写作}
---
关键词：{词1} | {词2} | {词3}

总字数 500-800 字。中文输出。'

USER_MSG="以下是今日预采集的 AI 领域原始情报。请提炼 3-5 个最有价值的事件，写一篇情报简报。

数据：
$PAYLOAD"

# 调用小米 API
RESPONSE=$(curl -s --max-time 90 \
    'https://token-plan-cn.xiaomimimo.com/anthropic/v1/messages' \
    -H 'Content-Type: application/json' \
    -H 'x-api-key: tp-cpsc4hmutgjg8zl2zrz0ynyj8oa7e9mb2ezaa9joupqrwhqq' \
    -H 'anthropic-version: 2023-06-01' \
    -d "$(python3 -c "
import json
system = '''$SYSTEM'''
user = '''$USER_MSG'''
print(json.dumps({
    'model': 'mimo-v2.5-pro',
    'max_tokens': 4096,
    'system': system,
    'messages': [{'role': 'user', 'content': user}]
}, ensure_ascii=False))
")")

# 提取文本
REPORT=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for block in data.get('content', []):
        if block.get('type') == 'text':
            print(block['text'])
except Exception as e:
    print(f'解析失败: {e}', file=sys.stderr)
")

if [ -z "$REPORT" ]; then
    echo "报告生成失败" >&2
    echo "$RESPONSE" | head -5 >&2
    exit 1
fi

# 保存报告
mkdir -p "$REPORT_DIR"
echo "$REPORT" > "$REPORT_FILE"

# 输出报告
echo "$REPORT"
