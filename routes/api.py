"""
API 路由 Blueprint

历史说明：
  此 Blueprint 原先承载多种 API 端点，现已按功能拆分到独立模块：

  - 自动填充（/api/auto-fill/*）           → routes/auto_fill.py
  - 轻模型管理（/api/light-*）             → routes/light_models.py
  - 导入模板（/api/import-templates）       → routes/import_templates.py
  - 传统 Excel 导入导出（/api/import|export/excel） → routes/excel_io.py
  - 自定义导入向导（/api/custom-import/*）   → routes/custom_import.py

  本文件仅保留 api_bp 定义，以维持向后兼容（routes/__init__.py 仍导入 api_bp）。
  新代码请直接添加到对应的功能模块，不要向此文件追加端点。
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='')
