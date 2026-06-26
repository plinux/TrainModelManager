"""
自定义 Excel 导入向导 Blueprint（从 routes/api.py 拆分）

包含:
  - /api/custom-import/tables:    获取可用的系统表配置
  - /api/custom-import/parse:     解析 Excel 文件（Sheet 和列信息）
  - /api/custom-import/preview:   预览导入数据（含冲突检测）
  - /api/custom-import/execute:   执行导入

执行函数已拆分到 utils/importers/executors.py:
  - execute_system_table_import
  - execute_locomotive_import
  - execute_trainset_import
  - execute_locomotive_head_import
  - execute_carriage_import
  - execute_model_series_import
  - execute_model_model_import
"""
from flask import Blueprint, request, jsonify
from models import db
from utils.system_tables import get_table_display_info, SYSTEM_TABLES
from utils.excel_safety import validate_excel_upload
from utils.importers.executors import (
  MODEL_CLASS_MAP,
  execute_system_table_import,
  execute_locomotive_import,
  execute_trainset_import,
  execute_locomotive_head_import,
  execute_carriage_import,
  execute_model_series_import,
  execute_model_model_import,
)
import logging
import json

logger = logging.getLogger(__name__)
custom_import_bp = Blueprint('custom_import', __name__, url_prefix='')


@custom_import_bp.route('/api/custom-import/tables', methods=['GET'])
def get_custom_import_tables():
  """
  获取自定义导入可用的系统表配置

  返回所有可映射的系统表和模型表信息，用于前端下拉菜单

  Returns:
    JSON: {
      'success': True,
      'tables': [
        {
          'name': str,           # 表名
          'display_name': str,   # 显示名称
          'category': str,       # 类别: 'system' 或 'model'
          'tooltip': str,        # 可选，提示文本
          'has_set_detection': bool  # 可选，是否支持套装检测
        },
        ...
      ]
    }
  """
  try:
    tables = get_table_display_info()
    return jsonify({
      'success': True,
      'tables': tables
    })

  except Exception as e:
    logger.error(f"Failed to get custom import tables: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@custom_import_bp.route('/api/custom-import/parse', methods=['POST'])
def parse_custom_import_file():
  """
  解析 Excel 文件，返回 Sheet 和列信息

  Request:
    multipart/form-data with 'file' field containing Excel file

  Returns:
    JSON: {
      'success': True,
      'filename': str,
      'sheets': [
        {
          'name': str,       # Sheet 名称
          'columns': list,   # 列名列表
          'row_count': int   # 数据行数
        },
        ...
      ]
    }
  """
  try:
    if 'file' not in request.files:
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not file.filename.lower().endswith('.xlsx'):
      return jsonify({'success': False, 'error': '文件格式错误，请上传Excel文件'}), 400

    try:
      workbook = validate_excel_upload(file)
    except ValueError as e:
      return jsonify({'success': False, 'error': str(e)}), 400
    sheets = []

    for sheet_name in workbook.sheetnames:
      sheet = workbook[sheet_name]
      columns = []
      # Read first row as column headers
      for cell in sheet[1]:
        if cell.value is not None:
          columns.append(str(cell.value))

      # Count data rows
      row_count = 0
      for row in sheet.iter_rows(min_row=2, values_only=True):
        if any(cell is not None for cell in row):
          row_count += 1

      sheets.append({
        'name': sheet_name,
        'columns': columns,
        'row_count': row_count
      })

    logger.info(f"Parsed Excel file: {file.filename}, {len(sheets)} sheets")
    return jsonify({
      'success': True,
      'filename': file.filename,
      'sheets': sheets
    })

  except Exception as e:
    logger.error(f"Parse Excel failed: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@custom_import_bp.route('/api/custom-import/preview', methods=['POST'])
def preview_custom_import():
  """
  预览自定义导入数据，检测冲突

  Request:
    multipart/form-data with:
      - 'file': Excel file
      - 'config': JSON string containing mapping configuration

  Config structure:
    {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'},
        ...
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True},
            {'source': '官网', 'target': 'search_url', 'required': False}
          ],
          'conflict_mode': 'overwrite'
        },
        ...
      }
    }

  Returns:
    JSON: {
      'success': True,
      'previews': [
        {
          'table_name': 'brand',
          'display_name': '品牌',
          'row_count': 10,
          'conflicts': [
            {'type': '唯一名称冲突', 'field': 'name', 'value': 'xxx', 'message': '...'}
          ],
          'warnings': ['未映射字段: search_url'],
          'missing_required': ['scale']
        }
      ],
      'has_conflicts': False,
      'can_proceed': True
    }
  """
  try:
    # 验证文件
    if 'file' not in request.files:
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not file.filename.lower().endswith('.xlsx'):
      return jsonify({'success': False, 'error': '文件格式错误，请上传Excel文件'}), 400

    # 验证配置
    config_str = request.form.get('config')
    if not config_str:
      return jsonify({'success': False, 'error': '缺少映射配置'}), 400

    try:
      config = json.loads(config_str)
    except json.JSONDecodeError:
      return jsonify({'success': False, 'error': '配置格式错误，必须是有效的JSON'}), 400

    # 解析 Excel 文件
    try:
      workbook = validate_excel_upload(file)
    except ValueError as e:
      return jsonify({'success': False, 'error': str(e)}), 400

    # 构建工作表数据
    sheets_data = {}
    for sheet_name in workbook.sheetnames:
      sheet = workbook[sheet_name]
      headers = []
      data = []

      for row_idx, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if row_idx == 1:
          headers = [str(cell) if cell is not None else '' for cell in row]
        else:
          if any(cell is not None for cell in row):
            row_dict = {}
            for i, cell in enumerate(row):
              if i < len(headers) and headers[i]:
                row_dict[headers[i]] = cell
            data.append(row_dict)

      sheets_data[sheet_name] = {'headers': headers, 'data': data}

    # 处理预览
    previews = []
    has_conflicts = False
    can_proceed = True

    sheet_mappings = config.get('sheet_mappings', [])
    column_mappings = config.get('column_mappings', {})

    for mapping in sheet_mappings:
      sheet_name = mapping.get('sheet_name')
      table_name = mapping.get('table_name')

      if not sheet_name or not table_name:
        continue

      # 获取表配置
      table_config = SYSTEM_TABLES.get(table_name)
      if not table_config:
        logger.warning(f"Unknown table name: {table_name}")
        continue

      # 获取列映射
      column_mapping = column_mappings.get(table_name, {})
      columns = column_mapping.get('columns', [])

      # 构建源列名到目标字段名的映射
      source_to_target = {}
      for col in columns:
        source = col.get('source')
        target = col.get('target')
        if source and target:
          source_to_target[source] = target

      # 检查缺失的必填字段
      missing_required = []
      mapped_targets = set(source_to_target.values())
      for field in table_config.get('fields', []):
        if field.get('required') and field.get('name') not in mapped_targets:
          missing_required.append(field.get('name'))

      if missing_required:
        can_proceed = False

      # 生成警告（未映射的可选字段）
      warnings = []
      for field in table_config.get('fields', []):
        field_name = field.get('name')
        if not field.get('required') and field_name not in mapped_targets:
          warnings.append(f"未映射字段: {field_name}")

      # 获取工作表数据
      sheet_data = sheets_data.get(sheet_name, {})
      rows = sheet_data.get('data', [])
      row_count = len(rows)

      # 检测冲突
      conflicts = []
      model_class = MODEL_CLASS_MAP.get(table_name)

      if model_class and row_count > 0:
        for row in rows:
          # 映射行数据到目标字段
          mapped_row = {}
          for source_col, target_field in source_to_target.items():
            value = row.get(source_col)
            mapped_row[target_field] = value

          # 检查唯一约束
          for field in table_config.get('fields', []):
            field_name = field.get('name')

            # 检查 unique 约束
            if field.get('unique'):
              value = mapped_row.get(field_name)
              if value:
                existing = model_class.query.filter_by(**{field_name: value}).first()
                if existing:
                  conflicts.append({
                    'type': '唯一名称冲突',
                    'field': field_name,
                    'value': str(value),
                    'message': f"{table_config.get('display_name')} '{value}' 已存在"
                  })
                  has_conflicts = True

            # 检查 unique_in_scale 约束
            if field.get('unique_in_scale'):
              value = mapped_row.get(field_name)
              scale = mapped_row.get('scale')
              if value and scale:
                existing = model_class.query.filter_by(
                  scale=scale,
                  **{field_name: value}
                ).first()
                if existing:
                  conflicts.append({
                    'type': '比例内唯一冲突',
                    'field': field_name,
                    'value': f"{scale} 比例 - {value}",
                    'message': f"{field.get('display', field_name)} '{value}' 在比例 '{scale}' 中已存在"
                  })
                  has_conflicts = True

      previews.append({
        'table_name': table_name,
        'display_name': table_config.get('display_name', table_name),
        'row_count': row_count,
        'conflicts': conflicts,
        'warnings': warnings,
        'missing_required': missing_required
      })

    logger.info(f"Preview completed: {len(previews)} tables, has_conflicts={has_conflicts}, can_proceed={can_proceed}")

    return jsonify({
      'success': True,
      'previews': previews,
      'has_conflicts': has_conflicts,
      'can_proceed': can_proceed
    })

  except Exception as e:
    logger.error(f"Preview custom import failed: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@custom_import_bp.route('/api/custom-import/execute', methods=['POST'])
def execute_custom_import():
  """
  执行自定义导入

  Request:
    multipart/form-data with:
      - 'file': Excel file
      - 'config': JSON string containing mapping configuration

  Config structure:
    {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'},
        ...
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True},
            {'source': '官网', 'target': 'search_url', 'required': False}
          ],
          'conflict_mode': 'overwrite'
        },
        ...
      }
    }

  Returns:
    JSON: {
      'success': True,
      'summary': {'brand': 10, 'locomotive': 5, ...},
      'errors': [],
      'message': '导入完成'
    }
  """
  try:
    # 验证文件
    if 'file' not in request.files:
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not file.filename.lower().endswith('.xlsx'):
      return jsonify({'success': False, 'error': '文件格式错误，请上传Excel文件'}), 400

    # 验证配置
    config_str = request.form.get('config')
    if not config_str:
      return jsonify({'success': False, 'error': '缺少映射配置'}), 400

    try:
      config = json.loads(config_str)
    except json.JSONDecodeError:
      return jsonify({'success': False, 'error': '配置格式错误，必须是有效的JSON'}), 400

    # 解析 Excel 文件
    try:
      workbook = validate_excel_upload(file)
    except ValueError as e:
      return jsonify({'success': False, 'error': str(e)}), 400

    # 构建工作表数据
    sheets_data = {}
    for sheet_name in workbook.sheetnames:
      sheet = workbook[sheet_name]
      headers = []
      data = []

      for row_idx, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if row_idx == 1:
          headers = [str(cell) if cell is not None else '' for cell in row]
        else:
          if any(cell is not None for cell in row):
            row_dict = {}
            for i, cell in enumerate(row):
              if i < len(headers) and headers[i]:
                row_dict[headers[i]] = cell
            data.append(row_dict)

      sheets_data[sheet_name] = {'headers': headers, 'data': data, 'sheet': sheet}

    # 执行导入
    summary = {}
    errors = []
    all_warnings = []

    sheet_mappings = config.get('sheet_mappings', [])
    column_mappings = config.get('column_mappings', {})

    for mapping in sheet_mappings:
      sheet_name = mapping.get('sheet_name')
      table_name = mapping.get('table_name')

      if not sheet_name or not table_name:
        continue

      # 获取表配置
      table_config = SYSTEM_TABLES.get(table_name)
      if not table_config:
        logger.warning(f"Unknown table name: {table_name}")
        continue

      # 获取列映射
      column_mapping = column_mappings.get(table_name, {})
      columns = column_mapping.get('columns', [])
      conflict_mode = column_mapping.get('conflict_mode', 'skip')

      # 构建源列名到目标字段名的映射
      source_to_target = {}
      for col in columns:
        source = col.get('source')
        target = col.get('target')
        if source and target:
          source_to_target[source] = target

      # 构建字段配置字典
      field_configs = {f['name']: f for f in table_config.get('fields', [])}

      # 获取工作表数据
      sheet_data = sheets_data.get(sheet_name, {})
      rows = sheet_data.get('data', [])

      if not rows:
        summary[table_name] = 0
        continue

      try:
        count = 0

        # 系统信息表
        if table_name in ['brand', 'depot', 'merchant', 'power_type', 'chip_interface', 'chip_model']:
          count = execute_system_table_import(table_name, table_config, rows, source_to_target, conflict_mode)

        # 系列表
        elif table_name in ['locomotive_series', 'carriage_series', 'trainset_series']:
          count = execute_model_series_import(table_name, rows, source_to_target, conflict_mode)

        # 车型表
        elif table_name in ['locomotive_model', 'carriage_model', 'trainset_model']:
          count = execute_model_model_import(table_name, rows, source_to_target, field_configs, conflict_mode)

        # 模型数据表
        elif table_name == 'locomotive':
          count = execute_locomotive_import(rows, source_to_target, field_configs, conflict_mode)
        elif table_name == 'trainset':
          count = execute_trainset_import(rows, source_to_target, field_configs, conflict_mode)
        elif table_name == 'locomotive_head':
          count = execute_locomotive_head_import(rows, source_to_target, field_configs, conflict_mode)
        elif table_name == 'carriage':
          # 获取套装检测模式（默认使用合并单元格检测）
          set_detection_mode = column_mapping.get('set_detection_mode', 'merged')
          result = execute_carriage_import(
            rows, source_to_target, field_configs, conflict_mode,
            sheet=sheet_data.get('sheet'),
            headers=sheet_data.get('headers', []),
            set_detection_mode=set_detection_mode
          )
          count = result['count']
          if result.get('warnings'):
            all_warnings.extend([f"车厢: {w}" for w in result['warnings']])

        summary[table_name] = count

      except Exception as e:
        db.session.rollback()
        errors.append(f"{table_config.get('display_name', table_name)}: {str(e)}")
        logger.error(f"Error importing table {table_name}: {str(e)}", exc_info=True)

    if errors:
      return jsonify({
        'success': False,
        'error': '部分导入失败: ' + '; '.join(errors),
        'summary': summary
      }), 400

    logger.info(f"Custom import completed: {summary}")
    response = {
      'success': True,
      'summary': summary,
      'errors': [],
      'message': '导入完成'
    }
    if all_warnings:
      response['warnings'] = all_warnings
    return jsonify(response)

  except Exception as e:
    db.session.rollback()
    logger.error(f"Execute custom import failed: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500
