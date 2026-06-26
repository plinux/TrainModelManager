"""
文件管理 API 路由 Blueprint

提供模型文件的上传、下载、预览、删除等功能
"""

import os
import zipfile
import tempfile
import logging
import random
from datetime import datetime, date, timezone
from flask import Blueprint, request, jsonify, send_file, send_from_directory, current_app, after_this_request
from werkzeug.utils import secure_filename
from models import db, ModelFile, FunctionKey
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead, Brand
from utils.file_sync import (
  get_model_folder_path, ensure_folder_exists,
  get_model_files, get_mime_type,
  get_absolute_file_path, sanitize_path_segment
)
from utils.function_table_parser import (
  parse_function_table, save_function_keys, get_function_keys,
  update_function_keys, export_function_keys_excel
)

logger = logging.getLogger(__name__)
files_bp = Blueprint('files', __name__, url_prefix='/api/files')


# 模型类型映射
MODEL_CLASS_MAP = {
  'locomotive': Locomotive,
  'carriage': CarriageSet,
  'trainset': Trainset,
  'locomotive_head': LocomotiveHead
}


def allowed_file(filename: str, file_type: str) -> bool:
  """
  检查文件扩展名是否允许

  Args:
    filename: 文件名
    file_type: 文件类型

  Returns:
    是否允许
  """
  if '.' not in filename:
    return False

  ext = filename.rsplit('.', 1)[1].lower()
  allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {})
  return ext in allowed_extensions.get(file_type, set())


def get_model_info(model_type: str, model_id: int) -> dict:
  """
  获取模型信息（品牌、货号）

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    包含 brand_abbreviation 和 item_number 的字典
  """
  model_class = MODEL_CLASS_MAP.get(model_type)
  if not model_class:
    return None

  model = db.session.get(model_class, model_id)
  if not model:
    return None

  brand = db.session.get(Brand, model.brand_id)
  if not brand:
    return None

  return {
    'brand_abbreviation': brand.abbreviation or '',
    'item_number': model.item_number or ''
  }


def generate_filename(file_type: str, brand_abbreviation: str, item_number: str,
                      original_filename: str = None) -> str:
  """
  生成存储文件名

  Args:
    file_type: 文件类型
    brand_abbreviation: 品牌缩写
    item_number: 货号
    original_filename: 原始文件名（用于说明书）

  Returns:
    生成的文件名
  """
  # 安全处理品牌缩写和货号
  safe_brand = secure_filename(brand_abbreviation)
  safe_item = secure_filename(item_number)
  base_name = f"{safe_brand}_{safe_item}"

  if file_type == 'image':
    # 图片：品牌_货号.扩展名
    ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'jpg'
    return f"{base_name}.{ext.lower()}"

  elif file_type == 'function_table':
    # 数码功能表：品牌_货号_FunctionKey.扩展名
    ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'pdf'
    return f"{base_name}_FunctionKey.{ext.lower()}"

  elif file_type == 'manual':
    # 说明书：品牌_货号_Manual_原始文件名
    safe_original = secure_filename(original_filename)
    return f"{base_name}_Manual_{safe_original}"

  return original_filename


@files_bp.route('/upload', methods=['POST'])
def upload_file():
  """
  上传文件

  请求参数:
    - model_type: 模型类型
    - model_id: 模型ID
    - file_type: 文件类型 (image/manual/function_table)
    - file: 文件

  返回:
    成功: {"success": true, "file": {...}}
    失败: {"success": false, "error": "错误信息"}
  """
  try:
    model_type = request.form.get('model_type')
    model_id = request.form.get('model_id', type=int)
    file_type = request.form.get('file_type')
    file = request.files.get('file')

    # 参数验证
    if not model_type or model_type not in MODEL_CLASS_MAP:
      return jsonify({'success': False, 'error': '无效的模型类型'}), 400

    if not model_id:
      return jsonify({'success': False, 'error': '缺少模型ID'}), 400

    if not file_type or file_type not in ['image', 'manual', 'function_table']:
      return jsonify({'success': False, 'error': '无效的文件类型'}), 400

    # 先头车不能上传数码功能表
    if model_type == 'locomotive_head' and file_type == 'function_table':
      return jsonify({'success': False, 'error': '先头车模型不能上传数码功能表'}), 400

    if not file or file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not allowed_file(file.filename, file_type):
      return jsonify({'success': False, 'error': '不支持的文件格式'}), 400

    # 获取模型信息
    model_info = get_model_info(model_type, model_id)
    if not model_info:
      return jsonify({'success': False, 'error': '模型不存在或缺少品牌/货号信息'}), 404

    brand_abbreviation = model_info['brand_abbreviation']
    item_number = model_info['item_number']
    if not item_number:
      return jsonify({'success': False, 'error': '模型缺少货号信息'}), 400

    # 生成存储文件名
    new_filename = generate_filename(file_type, brand_abbreviation, item_number, file.filename)

    # 获取存储路径
    folder_path = get_model_folder_path(model_type, brand_abbreviation, item_number)
    if not ensure_folder_exists(folder_path):
      return jsonify({'success': False, 'error': '创建存储目录失败'}), 500

    file_path = os.path.join(folder_path, new_filename)

    # 先保存新文件落盘，避免"删旧后新文件保存失败"导致旧文件丢失
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    folder_name = sanitize_path_segment(f"{brand_abbreviation}_{item_number}")
    relative_path = os.path.join(sanitize_path_segment(model_type), folder_name, new_filename)

    # 查找待替换的旧记录（图片/功能表唯一覆盖；说明书按原名去重）
    old_records = []
    if file_type in ['image', 'function_table']:
      old = ModelFile.query.filter_by(
        model_type=model_type, model_id=model_id, file_type=file_type
      ).first()
      if old:
        old_records.append(old)
    elif file_type == 'manual':
      old = ModelFile.query.filter_by(
        model_type=model_type, model_id=model_id, file_type=file_type,
        original_filename=file.filename
      ).first()
      if old:
        old_records.append(old)

    # 新记录入库 + 旧记录删除在同一事务（原子）
    new_record = ModelFile(
      model_type=model_type,
      model_id=model_id,
      file_type=file_type,
      file_path=relative_path,
      original_filename=file.filename,
      file_size=file_size,
      mime_type=get_mime_type(new_filename),
      uploaded_at=datetime.now(timezone.utc)
    )
    db.session.add(new_record)
    for old in old_records:
      db.session.delete(old)
    db.session.commit()

    # 事务提交成功后再删除旧物理文件（删除失败则保留，由文件同步清理）
    for old in old_records:
      try:
        os.remove(get_absolute_file_path(old.file_path))
      except FileNotFoundError:
        pass
      except OSError as remove_err:
        logger.warning(f"删除旧物理文件失败: {remove_err}")

    logger.info(f"文件上传成功: {relative_path}")

    # 数码功能表上传后自动解析
    function_keys = None
    if file_type == 'function_table':
      try:
        parsed = parse_function_table(file_path, new_record.mime_type)
        if parsed:
          saved_keys = save_function_keys(
            model_type, model_id, parsed,
            source_file_id=new_record.id
          )
          function_keys = [k.to_dict() for k in saved_keys]
          logger.info(f"功能表解析成功: {len(saved_keys)} 个功能键")
        else:
          logger.warning(f"功能表解析未提取到数据: {relative_path}")
      except Exception as parse_err:
        logger.error(f"功能表解析失败: {parse_err}")

    result = {
      'success': True,
      'file': new_record.to_dict()
    }
    if function_keys is not None:
      result['function_keys'] = function_keys

    return jsonify(result)

  except Exception as e:
    db.session.rollback()
    logger.error(f"文件上传失败: {str(e)}")
    return jsonify({'success': False, 'error': '上传失败，请稍后重试'}), 500


@files_bp.route('/download/<int:file_id>')
def download_file(file_id):
  """
  下载文件

  Args:
    file_id: 文件记录ID
  """
  file_record = db.get_or_404(ModelFile, file_id)

  try:
    file_path = get_absolute_file_path(file_record.file_path)
  except ValueError:
    return jsonify({'success': False, 'error': '非法文件路径'}), 400

  if not os.path.exists(file_path):
    return jsonify({'success': False, 'error': '文件不存在'}), 404

  return send_file(
    file_path,
    as_attachment=True,
    download_name=file_record.original_filename
  )


@files_bp.route('/view/<int:file_id>')
def view_file(file_id):
  """
  预览文件（在浏览器中打开）

  Args:
    file_id: 文件记录ID
  """
  file_record = db.get_or_404(ModelFile, file_id)

  try:
    file_path = get_absolute_file_path(file_record.file_path)
  except ValueError:
    return jsonify({'success': False, 'error': '非法文件路径'}), 400

  if not os.path.exists(file_path):
    return jsonify({'success': False, 'error': '文件不存在'}), 404

  return send_file(
    file_path,
    as_attachment=False,
    mimetype=file_record.mime_type
  )


@files_bp.route('/delete/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
  """
  删除文件

  Args:
    file_id: 文件记录ID

  Returns:
    {"success": true} 或 {"success": false, "error": "错误信息"}
  """
  try:
    file_record = db.get_or_404(ModelFile, file_id)

    # 删除物理文件（校验路径未越出 DATA_DIR）
    try:
      file_path = get_absolute_file_path(file_record.file_path)
    except ValueError:
      return jsonify({'success': False, 'error': '非法文件路径'}), 400

    try:
      os.remove(file_path)
    except FileNotFoundError:
      pass

    # 删除数据库记录
    db.session.delete(file_record)
    db.session.commit()

    logger.info(f"文件删除成功: {file_record.file_path}")

    return jsonify({'success': True})

  except Exception as e:
    db.session.rollback()
    logger.error(f"文件删除失败: {str(e)}")
    return jsonify({'success': False, 'error': '删除失败，请稍后重试'}), 500


@files_bp.route('/list/<model_type>/<int:model_id>')
def list_files(model_type, model_id):
  """
  获取模型的文件列表

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    {"success": true, "files": {...}}
  """
  if model_type not in MODEL_CLASS_MAP:
    return jsonify({'success': False, 'error': '无效的模型类型'}), 400

  files = get_model_files(model_type, model_id)

  return jsonify({
    'success': True,
    'files': files
  })


@files_bp.route('/export-all')
def export_all_files():
  """
  导出所有模型文件为 ZIP

  Returns:
    ZIP 文件下载
  """
  try:
    data_dir = current_app.config.get('DATA_DIR', 'data')

    if not os.path.exists(data_dir):
      return jsonify({'success': False, 'error': '数据目录不存在'}), 404

    # 创建临时文件
    temp_fd, temp_path = tempfile.mkstemp(suffix='.zip')
    os.close(temp_fd)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = random.randint(1000, 9999)
    zip_filename = f'TMM_ModelFiles_{timestamp}_{random_suffix}.zip'

    # 创建 ZIP 文件
    with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
      for root, dirs, files in os.walk(data_dir):
        for file in files:
          file_path = os.path.join(root, file)
          arcname = os.path.relpath(file_path, data_dir)
          zipf.write(file_path, arcname)

    logger.info(f"文件导出成功: {zip_filename}")

    # 响应完成后清理临时文件（Unix 下 send_file 已打开句柄，unlink 不影响发送）
    @after_this_request
    def _cleanup_export_temp(response):
      try:
        os.unlink(temp_path)
      except OSError:
        pass
      return response

    return send_file(
      temp_path,
      as_attachment=True,
      download_name=zip_filename,
      mimetype='application/zip'
    )

  except Exception as e:
    logger.error(f"文件导出失败: {str(e)}")
    return jsonify({'success': False, 'error': '导出失败，请稍后重试'}), 500


@files_bp.route('/model/<model_type>/<int:model_id>')
def get_model_detail(model_type, model_id):
  """
  获取模型详情（包含文件信息）

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    模型详情和文件信息
  """
  model_class = MODEL_CLASS_MAP.get(model_type)
  if not model_class:
    return jsonify({'success': False, 'error': '无效的模型类型'}), 400

  model = db.get_or_404(model_class, model_id)

  # 获取模型属性
  result = {
    'id': model.id,
    'type': model_type,
    'attributes': {}
  }

  # 获取关联数据
  if model.brand:
    result['attributes']['brand'] = model.brand.name
  if hasattr(model, 'series') and model.series:
    result['attributes']['series'] = model.series.name
  if hasattr(model, 'model') and model.model:
    result['attributes']['model'] = model.model.name
  if hasattr(model, 'power_type') and model.power_type:
    result['attributes']['power_type'] = model.power_type.name
  if hasattr(model, 'depot') and model.depot:
    result['attributes']['depot'] = model.depot.name
  if model.merchant:
    result['attributes']['merchant'] = model.merchant.name
  # 获取灯型号名称
  if hasattr(model, 'light_model') and model.light_model:
    result['attributes']['light_model'] = model.light_model.name

  # 获取基本属性
  for column in model.__table__.columns:
    col_name = column.name
    if col_name not in ['id', 'brand_id', 'series_id', 'model_id', 'power_type_id',
                        'depot_id', 'merchant_id', 'chip_interface_id', 'chip_model_id',
                        'light_model_id']:
      value = getattr(model, col_name)
      if value is not None:
        if isinstance(value, (datetime, date)):
          value = value.isoformat()
        result['attributes'][col_name] = value

  # 获取文件信息
  result['files'] = get_model_files(model_type, model_id)

  return jsonify({
    'success': True,
    'model': result
  })


# ==================== 数码功能键 API ====================

@files_bp.route('/function-keys/<model_type>/<int:model_id>', methods=['GET'])
def get_keys(model_type, model_id):
  """
  获取模型的功能键数据

  Args:
    model_type: 模型类型 (locomotive/trainset)
    model_id: 模型ID

  Returns:
    {"success": true, "keys": [...]}
  """
  if model_type not in ['locomotive', 'trainset']:
    return jsonify({'success': False, 'error': '该模型类型不支持功能键'}), 400

  keys = get_function_keys(model_type, model_id)
  return jsonify({
    'success': True,
    'keys': keys
  })


@files_bp.route('/function-keys/<model_type>/<int:model_id>', methods=['PUT'])
def update_keys(model_type, model_id):
  """
  更新模型的功能键数据(覆盖写入)

  Args:
    model_type: 模型类型
    model_id: 模型ID

  请求体:
    {"keys": [{"key_number": 0, "function_name": "...", "description": "..."}]}

  Returns:
    {"success": true, "keys": [...]}
  """
  if model_type not in ['locomotive', 'trainset']:
    return jsonify({'success': False, 'error': '该模型类型不支持功能键'}), 400

  data = request.get_json()
  if not data or 'keys' not in data:
    return jsonify({'success': False, 'error': '缺少 keys 数据'}), 400

  try:
    updated = update_function_keys(model_type, model_id, data['keys'])
    return jsonify({
      'success': True,
      'keys': [k.to_dict() for k in updated]
    })
  except Exception as e:
    db.session.rollback()
    logger.error(f"更新功能键失败: {e}")
    return jsonify({'success': False, 'error': '操作失败，请稍后重试'}), 500


@files_bp.route('/reparse-function-table/<model_type>/<int:model_id>', methods=['POST'])
def reparse_function_table(model_type, model_id):
  """
  重新解析数码功能表

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    {"success": true, "keys": [...]} 或错误信息
  """
  if model_type not in ['locomotive', 'trainset']:
    return jsonify({'success': False, 'error': '该模型类型不支持功能键'}), 400

  # 查找功能表文件
  func_file = ModelFile.query.filter_by(
    model_type=model_type,
    model_id=model_id,
    file_type='function_table'
  ).first()

  if not func_file:
    return jsonify({'success': False, 'error': '未找到数码功能表文件'}), 404

  # 构建绝对路径（校验未越出 DATA_DIR）
  try:
    abs_path = get_absolute_file_path(func_file.file_path)
  except ValueError:
    return jsonify({'success': False, 'error': '非法文件路径'}), 400

  if not os.path.exists(abs_path):
    return jsonify({'success': False, 'error': '功能表文件不存在'}), 404

  try:
    parsed = parse_function_table(abs_path, func_file.mime_type)
    if parsed:
      saved = save_function_keys(
        model_type, model_id, parsed,
        source_file_id=func_file.id
      )
      return jsonify({
        'success': True,
        'keys': [k.to_dict() for k in saved],
        'count': len(saved)
      })
    else:
      return jsonify({
        'success': False,
        'error': '解析未提取到数据，请检查功能表图片是否清晰'
      }), 422
  except Exception as e:
    logger.error(f"重新解析失败: {e}")
    return jsonify({'success': False, 'error': '操作失败，请稍后重试'}), 500


@files_bp.route('/function-keys/<model_type>/<int:model_id>/export', methods=['GET'])
def export_keys(model_type, model_id):
  """
  导出功能键为 Excel

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    Excel 文件下载
  """
  if model_type not in ['locomotive', 'trainset']:
    return jsonify({'success': False, 'error': '该模型类型不支持功能键'}), 400

  # 获取品牌和货号信息用于文件名
  model_info = get_model_info(model_type, model_id)
  brand_abbr = model_info['brand_abbreviation'] if model_info else ''
  item_number = model_info['item_number'] if model_info else ''

  buf = export_function_keys_excel(model_type, model_id, brand_abbr, item_number)
  return send_file(
    buf,
    as_attachment=True,
    download_name=buf.filename,
    mimetype=buf.content_type
  )
