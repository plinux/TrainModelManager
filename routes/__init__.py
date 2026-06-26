from .main import main_bp
from .api import api_bp
from .locomotive import locomotive_bp
from .auto_fill import auto_fill_bp
from .carriage import carriage_bp
from .trainset import trainset_bp

def register_blueprints(app):
  for bp in [main_bp, api_bp, locomotive_bp, auto_fill_bp, carriage_bp, trainset_bp]:
    app.register_blueprint(bp)
