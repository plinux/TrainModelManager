#!/bin/bash
# 开发环境启动脚本
# - 启用 DEBUG 模式
# - 日志输出到控制台
# - 自动重载代码修改

# 进入脚本所在目录
cd "$(dirname "$0")"

# 激活虚拟环境
source myenv/bin/activate

# 设置环境变量
export FLASK_APP=app.py
export FLASK_DEBUG=1
export FLASK_ENV=development

echo "=========================================="
echo "  火车模型管理系统 - 开发模式"
echo "=========================================="
echo "调试模式: 开启"
echo "日志输出: 控制台"
echo "访问地址: http://127.0.0.1:5000"
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 启动 Flask 开发服务器
python app.py
