#!/bin/bash
# 执行 Python 数据采集
set -e

cd "$(dirname "$0")/.."
echo "=== AI Radar 数据采集 ==="
python -m python.src.pipeline "$@"
echo "=== 采集完成 ==="
