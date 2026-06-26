from .main import main_bp
from .api import api_bp
from .locomotive import locomotive_bp
from .auto_fill import auto_fill_bp
from .carriage import carriage_bp
from .trainset import trainset_bp
from .locomotive_head import locomotive_head_bp
from .options import options_bp
from .excel_io import excel_io_bp
from .system import system_bp
from .import_templates import import_templates_bp
from .custom_import import custom_import_bp
from .files import files_bp
def register_blueprints(app):
  for bp in [main_bp, api_bp, locomotive_bp, auto_fill_bp, carriage_bp, trainset_bp, locomotive_head_bp, options_bp, excel_io_bp, system_bp, import_templates_bp, custom_import_bp, files_bp]:
    app.register_blueprint(bp)
