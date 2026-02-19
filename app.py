"""
火车模型管理系统 - Flask 主应用
使用 Blueprint 模块化架构

优化内容：
1. 模块化路由（Blueprints）
2. 统一错误处理和事务回滚
3. 公共辅助函数提取
4. 统一 API 响应格式
"""
from flask import Flask, render_template
from config import Config
from models import db
from routes import register_blueprints
import logging
import os

# 配置日志
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s %(name)s %(levelname)s %(message)s',
  handlers=[
    logging.FileHandler('app.log'),
    logging.StreamHandler()
  ]
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
  """Flask 应用工厂函数"""
  app = Flask(__name__)
  app.config.from_object(config_class)

  # 初始化数据库
  db.init_app(app)

  # 注册所有 Blueprint
  register_blueprints(app)

  # 注册错误处理器
  register_error_handlers(app)

  # 创建数据目录（如果不存在）
  data_dir = app.config.get('DATA_DIR', 'data')
  if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    logger.info(f"Created data directory: {data_dir}")

  # 启动时同步文件
  with app.app_context():
    from utils.file_sync import sync_data_directory
    sync_data_directory()

  logger.info("Application initialized successfully")
  return app


def register_error_handlers(app):
  """注册错误处理器"""

  @app.errorhandler(404)
  def not_found(error):
    """404 错误处理"""
    return render_template('404.html'), 404

  @app.errorhandler(500)
  def internal_error(error):
    """500 错误处理"""
    db.session.rollback()
    return render_template('500.html'), 500

  @app.errorhandler(Exception)
  def handle_exception(error):
    """全局异常处理"""
    db.session.rollback()
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return f"服务器错误: {str(error)}<script>setTimeout(()=>location.href='/', 3000);</script>", 500


# 创建应用实例
app = create_app()

if __name__ == '__main__':
  app.run(debug=True)
