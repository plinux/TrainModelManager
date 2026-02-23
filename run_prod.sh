#!/bin/bash
# 生产环境启动脚本
# - 关闭 DEBUG 模式
# - 日志重定向到 logs/app.log
# - 后台运行
#
# 用法: ./run_prod.sh [端口号]
# 示例: ./run_prod.sh 8080

# 进入脚本所在目录
cd "$(dirname "$0")"

# 激活虚拟环境
source myenv/bin/activate

# 创建日志目录
mkdir -p logs

# 设置环境变量
export FLASK_APP=app.py
export FLASK_DEBUG=0
export FLASK_ENV=production

# 日志文件路径
LOG_FILE="logs/app.log"
PID_FILE="logs/app.pid"

# 端口参数，默认 5000
PORT=${1:-5000}

# 检查端口是否被占用
check_port() {
  if lsof -i :$PORT > /dev/null 2>&1; then
    return 0  # 端口被占用
  else
    return 1  # 端口空闲
  fi
}

# 检查是否已在运行（通过 PID 文件）
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if ps -p "$OLD_PID" > /dev/null 2>&1; then
    echo "服务已在运行中 (PID: $OLD_PID)"
    echo "如需重启，请先运行: ./stop_prod.sh"
    exit 1
  else
    rm -f "$PID_FILE"
  fi
fi

# 检查端口是否被其他进程占用
if check_port; then
  echo "错误: 端口 $PORT 已被占用"
  echo "占用进程信息:"
  lsof -i :$PORT
  echo ""
  echo "请先停止占用端口的进程，或使用其他端口: ./run_prod.sh <端口号>"
  exit 1
fi

echo "=========================================="
echo "  火车模型管理系统 - 生产模式"
echo "=========================================="
echo "调试模式: 关闭"
echo "日志文件: $LOG_FILE"
echo "访问地址: http://127.0.0.1:$PORT"
echo "=========================================="

# 启动服务（后台运行，日志重定向）
nohup python -c "
from app import app
import logging

# 重新配置日志（仅文件输出）
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s %(name)s %(levelname)s %(message)s',
  handlers=[
    logging.FileHandler('$LOG_FILE'),
  ]
)

# 关闭调试模式，监听所有网卡
app.run(host='0.0.0.0', port=$PORT, debug=False)
" >> "$LOG_FILE" 2>&1 &

# 保存 PID
echo $! > "$PID_FILE"

# 等待一下确认启动成功
sleep 1
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
  echo "服务已启动 (PID: $(cat $PID_FILE))"
  echo "查看日志: tail -f $LOG_FILE"
else
  echo "启动失败，请检查日志: $LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
fi
