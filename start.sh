#!/bin/bash
# 火车模型管理系统 - 启动脚本
#
# 用法: ./start.sh [选项]
#   --debug    开发模式（前台运行，自动重载）
#   --port N   指定端口号（默认 8000；仅生产模式生效，开发模式端口由 app.py 决定）
#
# 示例:
#   ./start.sh                # 生产模式，端口 8000
#   ./start.sh --debug        # 开发模式，端口 8000
#   ./start.sh --port 9000    # 生产模式，端口 9000
#   ./start.sh --debug --port 3000
#
# 生产模式 SECRET_KEY 管理（app.py 对生产环境 fail-fast，缺失即拒绝启动）:
#   优先级 环境变量 SECRET_KEY > 本地密钥文件 .secret_key。
#   首次启动自动生成随机密钥并持久化到 .secret_key（已 gitignore），
#   保证 session 跨重启连续；后续启动复用，无需手动配置。

# 进入脚本所在目录
cd "$(dirname "$0")"

# 显式指定虚拟环境解释器：不依赖 `source activate`，避免非交互 shell 下未生效
PY="./myenv/bin/python"
if [ ! -x "$PY" ]; then
  echo "错误: 未找到虚拟环境 Python ($PY)"
  echo "请先执行: python -m venv myenv && source myenv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 默认参数
DEBUG=0
PORT=8000

# 解析参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --debug)
      DEBUG=1
      shift
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      echo "用法: ./start.sh [--debug] [--port 端口号]"
      exit 1
      ;;
  esac
done

# 设置公共环境变量
export FLASK_APP=app.py

if [ "$DEBUG" -eq 1 ]; then
  # ===== 开发模式 =====
  export FLASK_DEBUG=1
  export FLASK_ENV=development

  echo "=========================================="
  echo "  火车模型管理系统 - 开发模式"
  echo "=========================================="
  echo "调试模式: 开启"
  echo "日志输出: 控制台"
  echo "访问地址: http://127.0.0.1:$PORT"
  echo "按 Ctrl+C 停止服务"
  echo "=========================================="

  exec "$PY" app.py
else
  # ===== 生产模式 =====
  export FLASK_DEBUG=0
  export FLASK_ENV=production

  # SECRET_KEY 持久化管理：环境变量优先；否则读取本地密钥文件；文件缺失则生成
  SECRET_FILE="./.secret_key"
  if [ -z "$SECRET_KEY" ]; then
    if [ -f "$SECRET_FILE" ]; then
      export SECRET_KEY="$(cat "$SECRET_FILE")"
    else
      export SECRET_KEY="$("$PY" -c 'import secrets; print(secrets.token_hex(32))')"
      printf '%s' "$SECRET_KEY" > "$SECRET_FILE"
      chmod 600 "$SECRET_FILE"
      echo "已生成 SECRET_KEY 并保存到 $SECRET_FILE（已加入 .gitignore，请勿提交）"
    fi
  fi

  # 创建日志目录
  mkdir -p logs

  LOG_FILE="logs/app.log"
  PID_FILE="logs/app.pid"

  # 检查是否已在运行（通过 PID 文件）
  if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
      echo "服务已在运行中 (PID: $OLD_PID)"
      echo "如需重启，请先运行: ./stop.sh"
      exit 1
    else
      rm -f "$PID_FILE"
    fi
  fi

  # 检查端口是否被占用
  if lsof -i :$PORT > /dev/null 2>&1; then
    echo "错误: 端口 $PORT 已被占用"
    echo "占用进程信息:"
    lsof -i :$PORT
    echo ""
    echo "请先停止占用端口的进程: ./stop.sh --port $PORT"
    exit 1
  fi

  echo "=========================================="
  echo "  火车模型管理系统 - 生产模式"
  echo "=========================================="
  echo "调试模式: 关闭"
  echo "日志文件: $LOG_FILE"
  echo "访问地址: http://127.0.0.1:$PORT"
  echo "=========================================="

  # 启动服务（后台运行，日志重定向；显式使用虚拟环境 Python）
  nohup "$PY" -c "
from app import app
import logging

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s %(name)s %(levelname)s %(message)s',
  handlers=[
    logging.FileHandler('$LOG_FILE'),
  ]
)

app.run(host='0.0.0.0', port=$PORT, debug=False)
" >> "$LOG_FILE" 2>&1 &

  # 保存 PID
  echo $! > "$PID_FILE"

  # 等待确认启动成功
  sleep 1
  if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "服务已启动 (PID: $(cat $PID_FILE))"
    echo "查看日志: tail -f $LOG_FILE"
  else
    echo "启动失败，请检查日志: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
  fi
fi
