#!/bin/bash
# 停止生产环境服务

# 进入脚本所在目录
cd "$(dirname "$0")"

PID_FILE="logs/app.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if ps -p "$PID" > /dev/null 2>&1; then
    echo "正在停止服务 (PID: $PID)..."
    kill "$PID"
    rm -f "$PID_FILE"
    echo "服务已停止"
  else
    echo "服务未运行"
    rm -f "$PID_FILE"
  fi
else
  echo "未找到 PID 文件，服务可能未运行"
fi
