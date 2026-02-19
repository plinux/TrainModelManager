# Routes package
from .main import main_bp
from .locomotive import locomotive_bp
from .carriage import carriage_bp
from .trainset import trainset_bp
from .locomotive_head import locomotive_head_bp
from .options import options_bp
from .api import api_bp
from .system import system_bp
from .files import files_bp

__all__ = [
  'main_bp',
  'locomotive_bp',
  'carriage_bp',
  'trainset_bp',
  'locomotive_head_bp',
  'options_bp',
  'api_bp',
  'system_bp',
  'files_bp'
]


def register_blueprints(app):
  """注册所有 Blueprint 到 Flask 应用"""
  app.register_blueprint(main_bp)
  app.register_blueprint(locomotive_bp)
  app.register_blueprint(carriage_bp)
  app.register_blueprint(trainset_bp)
  app.register_blueprint(locomotive_head_bp)
  app.register_blueprint(options_bp)
  app.register_blueprint(api_bp)
  app.register_blueprint(system_bp)
  app.register_blueprint(files_bp)
