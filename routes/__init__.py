# Routes package
from .main import main_bp
from .api import api_bp

__all__ = ['main_bp', 'api_bp']


def register_blueprints(app):
  """注册所有 Blueprint 到 Flask 应用"""
  app.register_blueprint(main_bp)
  app.register_blueprint(api_bp)
