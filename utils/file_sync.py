"""
文件同步工具

启动时扫描 data 目录，同步数据库中的文件记录。
处理手动删除/添加文件的情况。
"""

import os
from datetime import datetime
from flask import current_app
from models import db, ModelFile


# 支持的模型类型
MODEL_TYPES = ['locomotive', 'carriage', 'trainset', 'locomotive_head']

# 文件类型映射（基于文件名特征）
FILE_TYPE_PATTERNS = {
  'image': '',  # 基础文件名，如 百万城_HXD3D001.jpg
  'function_table': '_FunctionKey',  # 数码功能表
  'manual': '_Manual_'  # 说明书
}


def get_file_type(filename: str, base_name: str) -> str:
  """
  根据文件名判断文件类型

  Args:
    filename: 文件名
    base_name: 基础名称（品牌_货号）

  Returns:
    文件类型：image/manual/function_table
  """
  name_without_ext = os.path.splitext(filename)[0]

  # 检查是否为数码功能表
  if name_without_ext == f"{base_name}_FunctionKey":
    return 'function_table'

  # 检查是否为说明书
  if '_Manual_' in name_without_ext and name_without_ext.startswith(base_name):
    return 'manual'

  # 检查是否为图片（基础文件名）
  if name_without_ext == base_name:
    return 'image'

  return None


def get_mime_type(filename: str) -> str:
  """
  根据扩展名获取 MIME 类型

  Args:
    filename: 文件名

  Returns:
    MIME 类型字符串
  """
  ext = os.path.splitext(filename)[1].lower()
  mime_map = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.zip': 'application/zip'
  }
  return mime_map.get(ext, 'application/octet-stream')


def parse_folder_name(folder_name: str) -> tuple:
  """
  解析文件夹名称，提取品牌和货号

  Args:
    folder_name: 文件夹名称（如 "百万城_HXD3D001"）

  Returns:
    (brand, item_number) 元组
  """
  parts = folder_name.split('_', 1)
  if len(parts) == 2:
    return parts[0], parts[1]
  return None, None


def find_model_id(model_type: str, brand_name: str, item_number: str) -> int:
  """
  根据品牌和货号查找模型ID

  Args:
    model_type: 模型类型
    brand_name: 品牌名称
    item_number: 货号

  Returns:
    模型ID，未找到返回 None
  """
  # 延迟导入避免循环依赖
  from models import Brand, Locomotive, CarriageSet, Trainset, LocomotiveHead

  # 先查找品牌ID
  brand = Brand.query.filter_by(name=brand_name).first()
  if not brand:
    return None

  # 根据模型类型查找
  if model_type == 'locomotive':
    model = Locomotive.query.filter_by(brand_id=brand.id, item_number=item_number).first()
  elif model_type == 'carriage':
    model = CarriageSet.query.filter_by(brand_id=brand.id, item_number=item_number).first()
  elif model_type == 'trainset':
    model = Trainset.query.filter_by(brand_id=brand.id, item_number=item_number).first()
  elif model_type == 'locomotive_head':
    model = LocomotiveHead.query.filter_by(brand_id=brand.id, item_number=item_number).first()
  else:
    return None

  return model.id if model else None


def sync_data_directory():
  """
  同步 data 目录中的文件到数据库

  扫描 data 目录，更新数据库中的文件记录：
  1. 删除数据库中存在但文件系统中不存在的记录
  2. 添加文件系统中存在但数据库中不存在的记录
  """
  data_dir = current_app.config.get('DATA_DIR')
  if not data_dir or not os.path.exists(data_dir):
    current_app.logger.info(f"DATA_DIR 不存在，跳过文件同步: {data_dir}")
    return

  # 检查表是否存在
  try:
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    if 'model_file' not in inspector.get_table_names():
      current_app.logger.info("model_file 表不存在，跳过文件同步")
      return
  except Exception as e:
    current_app.logger.warning(f"检查表存在时出错: {e}")
    return

  synced_count = 0
  removed_count = 0

  # 获取所有现有文件记录的路径
  existing_paths = set()
  db_files = ModelFile.query.all()
  for f in db_files:
    existing_paths.add(f.file_path)

  # 扫描目录结构
  for model_type in MODEL_TYPES:
    type_dir = os.path.join(data_dir, model_type)
    if not os.path.exists(type_dir):
      continue

    for folder_name in os.listdir(type_dir):
      folder_path = os.path.join(type_dir, folder_name)
      if not os.path.isdir(folder_path):
        continue

      # 解析品牌和货号
      brand_name, item_number = parse_folder_name(folder_name)
      if not brand_name or not item_number:
        continue

      # 查找对应的模型ID
      model_id = find_model_id(model_type, brand_name, item_number)
      if not model_id:
        continue

      # 扫描文件夹中的文件
      for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
          continue

        # 判断文件类型
        base_name = folder_name
        file_type = get_file_type(filename, base_name)

        # 跳过无法识别的文件
        if not file_type:
          continue

        # 先头车不能有数码功能表
        if model_type == 'locomotive_head' and file_type == 'function_table':
          continue

        # 相对路径（相对于 DATA_DIR）
        relative_path = os.path.join(model_type, folder_name, filename)

        # 检查是否已存在记录
        existing = ModelFile.query.filter_by(
          model_type=model_type,
          model_id=model_id,
          file_type=file_type,
          file_path=relative_path
        ).first()

        if existing:
          # 从待删除集合中移除
          existing_paths.discard(relative_path)
          continue

        # 创建新记录
        file_size = os.path.getsize(file_path)
        mime_type = get_mime_type(filename)

        new_file = ModelFile(
          model_type=model_type,
          model_id=model_id,
          file_type=file_type,
          file_path=relative_path,
          original_filename=filename,
          file_size=file_size,
          mime_type=mime_type,
          uploaded_at=datetime.utcnow()
        )
        db.session.add(new_file)
        synced_count += 1

  # 删除文件系统中不存在的记录
  for f in db_files:
    if f.file_path in existing_paths:
      db.session.delete(f)
      removed_count += 1

  # 提交更改
  if synced_count > 0 or removed_count > 0:
    db.session.commit()
    current_app.logger.info(f"文件同步完成: 新增 {synced_count} 个，删除 {removed_count} 个")
  else:
    current_app.logger.info("文件同步完成: 无变化")


def get_model_files(model_type: str, model_id: int) -> dict:
  """
  获取模型的所有文件

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    按文件类型分组的文件字典
  """
  files = ModelFile.query.filter_by(model_type=model_type, model_id=model_id).all()

  result = {
    'image': None,
    'function_table': None,
    'manual': []
  }

  for f in files:
    if f.file_type == 'image':
      result['image'] = f.to_dict()
    elif f.file_type == 'function_table':
      result['function_table'] = f.to_dict()
    elif f.file_type == 'manual':
      result['manual'].append(f.to_dict())

  return result


def get_model_folder_path(model_type: str, brand_name: str, item_number: str) -> str:
  """
  获取模型文件存储路径

  Args:
    model_type: 模型类型
    brand_name: 品牌名称
    item_number: 货号

  Returns:
    文件夹绝对路径
  """
  data_dir = current_app.config.get('DATA_DIR', 'data')
  folder_name = f"{brand_name}_{item_number}"
  return os.path.join(data_dir, model_type, folder_name)


def ensure_folder_exists(folder_path: str) -> bool:
  """
  确保文件夹存在

  Args:
    folder_path: 文件夹路径

  Returns:
    是否成功创建
  """
  try:
    os.makedirs(folder_path, exist_ok=True)
    return True
  except OSError as e:
    current_app.logger.error(f"创建文件夹失败: {folder_path}, 错误: {e}")
    return False


def rename_model_folder(model_type: str, old_brand_name: str, old_item_number: str,
                        new_brand_name: str, new_item_number: str) -> bool:
  """
  重命名模型文件夹（当品牌或货号变更时）

  Args:
    model_type: 模型类型
    old_brand_name: 旧品牌名称
    old_item_number: 旧货号
    new_brand_name: 新品牌名称
    new_item_number: 新货号

  Returns:
    是否成功重命名
  """
  from werkzeug.utils import secure_filename

  # 如果品牌和货号都没变，无需重命名
  if old_brand_name == new_brand_name and old_item_number == new_item_number:
    return True

  old_folder_path = get_model_folder_path(model_type, old_brand_name, old_item_number)

  # 如果旧目录不存在，无需重命名
  if not os.path.exists(old_folder_path):
    return True

  new_folder_path = get_model_folder_path(model_type, new_brand_name, new_item_number)

  # 如果新旧路径相同，无需重命名
  if old_folder_path == new_folder_path:
    return True

  try:
    # 确保父目录存在
    parent_dir = os.path.dirname(new_folder_path)
    os.makedirs(parent_dir, exist_ok=True)

    # 如果新目录已存在，先删除（这种情况不应该发生，但做保护）
    if os.path.exists(new_folder_path):
      import shutil
      shutil.rmtree(new_folder_path)

    # 重命名目录
    os.rename(old_folder_path, new_folder_path)

    # 重命名目录内的文件
    old_base = f"{secure_filename(old_brand_name)}_{secure_filename(old_item_number)}"
    new_base = f"{secure_filename(new_brand_name)}_{secure_filename(new_item_number)}"

    for filename in os.listdir(new_folder_path):
      old_file_path = os.path.join(new_folder_path, filename)
      if os.path.isfile(old_file_path):
        # 替换文件名中的基础部分
        new_filename = filename.replace(old_base, new_base, 1)
        if new_filename != filename:
          new_file_path = os.path.join(new_folder_path, new_filename)
          os.rename(old_file_path, new_file_path)

    current_app.logger.info(
      f"Renamed folder: {old_folder_path} -> {new_folder_path}"
    )
    return True

  except OSError as e:
    current_app.logger.error(
      f"重命名文件夹失败: {old_folder_path} -> {new_folder_path}, 错误: {e}"
    )
    return False


def update_file_records_in_db(model_type: str, model_id: int,
                              old_brand_name: str, old_item_number: str,
                              new_brand_name: str, new_item_number: str) -> bool:
  """
  更新数据库中的文件记录路径（当品牌或货号变更时）

  Args:
    model_type: 模型类型
    model_id: 模型ID
    old_brand_name: 旧品牌名称
    old_item_number: 旧货号
    new_brand_name: 新品牌名称
    new_item_number: 新货号

  Returns:
    是否成功更新
  """
  from werkzeug.utils import secure_filename

  # 如果品牌和货号都没变，无需更新
  if old_brand_name == new_brand_name and old_item_number == new_item_number:
    return True

  try:
    old_base = f"{secure_filename(old_brand_name)}_{secure_filename(old_item_number)}"
    new_base = f"{secure_filename(new_brand_name)}_{secure_filename(new_item_number)}"

    # 查找该模型的所有文件记录
    files = ModelFile.query.filter_by(model_type=model_type, model_id=model_id).all()

    for file_record in files:
      # 更新文件路径 - 路径中品牌_货号出现两次（目录名和文件名前缀）
      # 例如：locomotive/old_brand_old_item/old_brand_old_item.jpg
      # 需要替换所有出现的位置
      old_path = file_record.file_path
      new_path = old_path.replace(old_base, new_base)

      file_record.file_path = new_path
      # 注意：original_filename 保存的是用户上传时的原始文件名，不需要修改

    # 注意：这里不 commit，由调用者在适当时机统一提交
    return True

  except Exception as e:
    current_app.logger.error(f"更新文件记录失败: {e}")
    return False
