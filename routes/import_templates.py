"""
导入模板 CRUD API（P3-1：从 routes/api.py 拆分）

自定义导入向导的模板管理（列表/创建/获取/更新/删除/复制）。
"""
import json
from flask import Blueprint, jsonify, request
from models import db, ImportTemplate
from utils.system_tables import SYSTEM_TABLES
import logging

logger = logging.getLogger(__name__)
import_templates_bp = Blueprint('import_templates', __name__, url_prefix='')

# 模板配置大小上限（防资源耗尽）
MAX_CONFIG_SIZE = 1024 * 1024  # 1MB


def _template_to_dict(t):
  return {
    'id': t.id,
    'name': t.name,
    'config': t.config,
    'created_at': t.created_at.isoformat() if t.created_at else None,
    'updated_at': t.updated_at.isoformat() if t.updated_at else None
  }


def _validate_config(config):
  """校验模板配置：类型、大小、表引用。返回 (ok, error)。"""
  if not isinstance(config, dict):
    return False, '模板配置必须是JSON对象'
  try:
    serialized = json.dumps(config)
  except (TypeError, ValueError):
    return False, '模板配置序列化失败'
  if len(serialized) > MAX_CONFIG_SIZE:
    return False, f'模板配置过大（超过 {MAX_CONFIG_SIZE // 1024}KB）'
  # 校验配置引用的表名必须在系统表白名单内
  sheet_mappings = config.get('sheet_mappings', [])
  if sheet_mappings and not isinstance(sheet_mappings, list):
    return False, 'sheet_mappings 必须是列表'
  if isinstance(sheet_mappings, list):
    for sm in sheet_mappings:
      if isinstance(sm, dict):
        table_name = sm.get('table_name')
        if table_name and table_name not in SYSTEM_TABLES:
          return False, f'配置引用了不存在的表: {table_name}'
  return True, None


@import_templates_bp.route('/api/import-templates', methods=['GET'])
def list_import_templates():
  """获取所有导入模板"""
  try:
    templates = ImportTemplate.query.order_by(ImportTemplate.updated_at.desc()).all()
    return jsonify({'success': True, 'templates': [_template_to_dict(t) for t in templates]})
  except Exception as e:
    logger.error(f"Failed to list import templates: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@import_templates_bp.route('/api/import-templates', methods=['POST'])
def create_import_template():
  """创建导入模板"""
  try:
    data = request.get_json()
    if not data:
      return jsonify({'success': False, 'error': '请求体不能为空'}), 400

    name = data.get('name')
    config = data.get('config')

    if not name:
      return jsonify({'success': False, 'error': '模板名称不能为空'}), 400
    if config is None:
      return jsonify({'success': False, 'error': '模板配置不能为空'}), 400
    ok, err = _validate_config(config)
    if not ok:
      return jsonify({'success': False, 'error': err}), 400

    template = ImportTemplate(name=name, config=config)
    db.session.add(template)
    db.session.commit()

    logger.info(f"Created import template: {template.id} - {template.name}")
    return jsonify({'success': True, 'template': _template_to_dict(template)}), 201

  except Exception as e:
    db.session.rollback()
    logger.error(f"Failed to create import template: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@import_templates_bp.route('/api/import-templates/<int:template_id>', methods=['GET'])
def get_import_template(template_id):
  """获取单个导入模板"""
  try:
    template = db.session.get(ImportTemplate, template_id)
    if not template:
      return jsonify({'success': False, 'error': '模板不存在'}), 404
    return jsonify({'success': True, 'template': _template_to_dict(template)})
  except Exception as e:
    logger.error(f"Failed to get import template: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@import_templates_bp.route('/api/import-templates/<int:template_id>', methods=['PUT'])
def update_import_template(template_id):
  """更新导入模板"""
  try:
    template = db.session.get(ImportTemplate, template_id)
    if not template:
      return jsonify({'success': False, 'error': '模板不存在'}), 404

    data = request.get_json()
    if not data:
      return jsonify({'success': False, 'error': '请求体不能为空'}), 400

    if 'name' in data:
      template.name = data['name']
    if 'config' in data:
      ok, err = _validate_config(data['config'])
      if not ok:
        return jsonify({'success': False, 'error': err}), 400
      template.config = data['config']

    db.session.commit()
    logger.info(f"Updated import template: {template.id} - {template.name}")
    return jsonify({'success': True, 'template': _template_to_dict(template)})

  except Exception as e:
    db.session.rollback()
    logger.error(f"Failed to update import template: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@import_templates_bp.route('/api/import-templates/<int:template_id>', methods=['DELETE'])
def delete_import_template(template_id):
  """删除导入模板"""
  try:
    template = db.session.get(ImportTemplate, template_id)
    if not template:
      return jsonify({'success': False, 'error': '模板不存在'}), 404

    template_name = template.name
    db.session.delete(template)
    db.session.commit()

    logger.info(f"Deleted import template: {template_id} - {template_name}")
    return jsonify({'success': True, 'message': '删除成功'})

  except Exception as e:
    db.session.rollback()
    logger.error(f"Failed to delete import template: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@import_templates_bp.route('/api/import-templates/<int:template_id>/copy', methods=['POST'])
def copy_import_template(template_id):
  """复制导入模板"""
  try:
    template = db.session.get(ImportTemplate, template_id)
    if not template:
      return jsonify({'success': False, 'error': '模板不存在'}), 404

    data = request.get_json()
    if not data or not data.get('name'):
      return jsonify({'success': False, 'error': '新模板名称不能为空'}), 400

    new_name = data['name'].strip()
    if not new_name:
      return jsonify({'success': False, 'error': '新模板名称不能为空'}), 400

    existing = ImportTemplate.query.filter_by(name=new_name).first()
    if existing:
      return jsonify({'success': False, 'error': '模板名称已存在'}), 400

    new_template = ImportTemplate(
      name=new_name,
      config=template.config.copy() if template.config else {}
    )
    db.session.add(new_template)
    db.session.commit()

    logger.info(f"Copied import template: {template_id} -> {new_template.id} ({new_name})")
    return jsonify({'success': True, 'template': _template_to_dict(new_template)})

  except Exception as e:
    db.session.rollback()
    logger.error(f"Failed to copy import template: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500
