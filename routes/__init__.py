# Routes package
from .main import main_bp
from .api import api_bp
from .locomotive import locomotive_bp
from .auto_fill import auto_fill_bp
from .carriage import carriage_bp

__all__ = ['main_bp', 'api_bp', 'locomotive_bp', 'auto_fill_bp', 'carriage_bp']


def register_blueprints(app):
  app.register_blueprint(main_bp)
  app.register_blueprint(api_bp)
  app.register_blueprint(locomotive_bp)
  app.register_blueprint(auto_fill_bp)
  app.register_blueprint(carriage_bp)
