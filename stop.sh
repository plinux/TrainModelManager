#!/bin/bash
# 火车模型管理系统 - 停止脚本
#
# 用法: ./stop.sh [选项]
#   --port N   只停止监听指定端口的进程
#
# 示例:
#   ./stop.sh              # 停止所有运行中的服务
#   ./stop.sh --port 8000  # 只停止端口 8000 的服务

# 进入脚本所在目录
cd "$(dirname "$0")"

PID_FILE="logs/app.pid"

# 解析参数
STOP_PORT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --port)
      STOP_PORT="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      echo "用法: ./stop.sh [--port 端口号]"
      exit 1
      ;;
  esac
done

if [ -n "$STOP_PORT" ]; then
  # 停止指定端口
  PID=$(lsof -ti :$STOP_PORT 2>/dev/null)
  if [ -n "$PID" ]; then
    echo "正在停止端口 $STOP_PORT 的服务 (PID: $PID)..."
    kill $PID
    echo "服务已停止"
    # 清理 PID 文件（如果匹配）
    if [ -f "$PID_FILE" ]; then
      SAVED_PID=$(cat "$PID_FILE")
      if [ "$SAVED_PID" = "$PID" ]; then
        rm -f "$PID_FILE"
      fi
    fi
  else
    echo "端口 $STOP_PORT 上没有运行的服务"
  fi
else
  # 停止所有服务
  STOPPED=0

  # 通过 PID 文件停止
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      echo "正在停止服务 (PID: $PID)..."
      kill "$PID"
      rm -f "$PID_FILE"
      echo "服务已停止"
      STOPPED=1
    else
      echo "PID 文件中的进程已不存在"
      rm -f "$PID_FILE"
    fi
  fi

  # 清理可能残留的 Python 进程（本项目的）
  REMAINING=$(ps aux | grep "python.*app" | grep -v grep | grep -v stop.sh | awk '{print $2}')
  if [ -n "$REMAINING" ]; then
    echo "清理残留进程..."
    for PID in $REMAINING; do
      kill "$PID" 2>/dev/null && echo "已停止进程 $PID"
    done
    STOPPED=1
  fi

  if [ "$STOPPED" -eq 0 ]; then
    echo "没有运行中的服务"
  fi
fi
