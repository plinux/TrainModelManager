"""
火车模型管理系统 - Flask 主应用（Blueprint 模块化架构）
"""
from flask import Flask, render_template
from config import Config
from models import db
from routes import register_blueprints
import logging
import os

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s %(name)s %(levelname)s %(message)s',
  handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
  """Flask 应用工厂函数"""
  app = Flask(__name__)
  app.config.from_object(config_class)

  db.init_app(app)
  register_blueprints(app)
  register_error_handlers(app)

  data_dir = app.config.get('DATA_DIR', 'data')
  if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)

  logger.info("Application initialized successfully")
  return app


def register_error_handlers(app):
  """注册错误处理器"""

  @app.errorhandler(404)
  def not_found(error):
    return render_template('404.html'), 404

  @app.errorhandler(500)
  def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


app = create_app()

if __name__ == '__main__':
  app.run(debug=os.getenv('FLASK_DEBUG') == '1', port=8000)
