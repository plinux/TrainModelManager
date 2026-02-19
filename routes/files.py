"""
文件管理 API 路由 Blueprint

提供模型文件的上传、下载、预览、删除等功能
"""

import os
import zipfile
import tempfile
import logging
import random
from datetime import datetime, date
from flask import Blueprint, request, jsonify, send_file, send_from_directory, current_app
from werkzeug.utils import secure_filename
from models import db, ModelFile
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead, Brand
from utils.file_sync import (
  get_model_folder_path, ensure_folder_exists,
  get_model_files, get_mime_type
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
    包含 brand_name 和 item_number 的字典
  """
  model_class = MODEL_CLASS_MAP.get(model_type)
  if not model_class:
    return None

  model = model_class.query.get(model_id)
  if not model:
    return None

  brand = Brand.query.get(model.brand_id)
  if not brand:
    return None

  return {
    'brand_name': brand.name,
    'item_number': model.item_number or ''
  }


def generate_filename(file_type: str, brand_name: str, item_number: str,
                      original_filename: str = None) -> str:
  """
  生成存储文件名

  Args:
    file_type: 文件类型
    brand_name: 品牌名称
    item_number: 货号
    original_filename: 原始文件名（用于说明书）

  Returns:
    生成的文件名
  """
  # 安全处理品牌名称和货号
  safe_brand = secure_filename(brand_name)
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

    brand_name = model_info['brand_name']
    item_number = model_info['item_number']
    if not item_number:
      return jsonify({'success': False, 'error': '模型缺少货号信息'}), 400

    # 生成存储文件名
    new_filename = generate_filename(file_type, brand_name, item_number, file.filename)

    # 获取存储路径
    folder_path = get_model_folder_path(model_type, brand_name, item_number)
    if not ensure_folder_exists(folder_path):
      return jsonify({'success': False, 'error': '创建存储目录失败'}), 500

    file_path = os.path.join(folder_path, new_filename)

    # 图片和数码功能表是唯一的，先删除旧文件
    if file_type in ['image', 'function_table']:
      old_file = ModelFile.query.filter_by(
        model_type=model_type,
        model_id=model_id,
        file_type=file_type
      ).first()

      if old_file:
        # 删除旧文件
        old_full_path = os.path.join(current_app.config['DATA_DIR'], old_file.file_path)
        if os.path.exists(old_full_path):
          os.remove(old_full_path)
        db.session.delete(old_file)

    # 说明书检查同名文件
    if file_type == 'manual':
      existing = ModelFile.query.filter_by(
        model_type=model_type,
        model_id=model_id,
        file_type=file_type,
        original_filename=file.filename
      ).first()

      if existing:
        # 删除旧文件
        old_full_path = os.path.join(current_app.config['DATA_DIR'], existing.file_path)
        if os.path.exists(old_full_path):
          os.remove(old_full_path)
        db.session.delete(existing)

    # 保存文件
    file.save(file_path)

    # 获取文件信息
    file_size = os.path.getsize(file_path)
    relative_path = os.path.join(model_type, f"{brand_name}_{item_number}", new_filename)

    # 创建数据库记录
    new_record = ModelFile(
      model_type=model_type,
      model_id=model_id,
      file_type=file_type,
      file_path=relative_path,
      original_filename=file.filename,
      file_size=file_size,
      mime_type=get_mime_type(new_filename),
      uploaded_at=datetime.utcnow()
    )
    db.session.add(new_record)
    db.session.commit()

    logger.info(f"文件上传成功: {relative_path}")

    return jsonify({
      'success': True,
      'file': new_record.to_dict()
    })

  except Exception as e:
    db.session.rollback()
    logger.error(f"文件上传失败: {str(e)}")
    return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500


@files_bp.route('/download/<int:file_id>')
def download_file(file_id):
  """
  下载文件

  Args:
    file_id: 文件记录ID
  """
  file_record = ModelFile.query.get_or_404(file_id)

  data_dir = current_app.config.get('DATA_DIR', 'data')
  file_path = os.path.join(data_dir, file_record.file_path)

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
  file_record = ModelFile.query.get_or_404(file_id)

  data_dir = current_app.config.get('DATA_DIR', 'data')
  file_path = os.path.join(data_dir, file_record.file_path)

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
    file_record = ModelFile.query.get_or_404(file_id)

    # 删除物理文件
    data_dir = current_app.config.get('DATA_DIR', 'data')
    file_path = os.path.join(data_dir, file_record.file_path)

    if os.path.exists(file_path):
      os.remove(file_path)

    # 删除数据库记录
    db.session.delete(file_record)
    db.session.commit()

    logger.info(f"文件删除成功: {file_record.file_path}")

    return jsonify({'success': True})

  except Exception as e:
    db.session.rollback()
    logger.error(f"文件删除失败: {str(e)}")
    return jsonify({'success': False, 'error': f'删除失败: {str(e)}'}), 500


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

    return send_file(
      temp_path,
      as_attachment=True,
      download_name=zip_filename,
      mimetype='application/zip'
    )

  except Exception as e:
    logger.error(f"文件导出失败: {str(e)}")
    return jsonify({'success': False, 'error': f'导出失败: {str(e)}'}), 500


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

  model = model_class.query.get_or_404(model_id)

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

  # 获取基本属性
  for column in model.__table__.columns:
    col_name = column.name
    if col_name not in ['id', 'brand_id', 'series_id', 'model_id', 'power_type_id',
                        'depot_id', 'merchant_id', 'chip_interface_id', 'chip_model_id']:
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
