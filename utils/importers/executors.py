"""
自定义导入执行函数（从 routes/custom_import.py 拆出）

包含 7 个执行函数和模型类映射：
  - execute_system_table_import:       系统表导入
  - execute_locomotive_import:         机车模型导入
  - execute_trainset_import:           动车组模型导入
  - execute_locomotive_head_import:    先头车模型导入
  - execute_carriage_import:           车厢套装导入
  - execute_model_series_import:       系列（机车/车厢/动车组）导入
  - execute_model_model_import:        车型（机车/车厢/动车组）导入
  - MODEL_CLASS_MAP:                   表名到模型类的映射
"""
import logging

from models import (
  db, LocomotiveModel, CarriageModel, TrainsetModel,
  Locomotive, CarriageSet, Trainset, LocomotiveHead,
  Brand, Depot, Merchant, ChipInterface, ChipModel,
  LocomotiveSeries, CarriageSeries, TrainsetSeries, PowerType,
  CarriageItem, LightBrand, LightModel,
)
from utils.helpers import parse_purchase_date, safe_int, safe_float, parse_boolean
from utils.price_calculator import calculate_price
from utils.importers.helpers import (
  resolve_foreign_key, find_id_by_name, _update_chip_model_interfaces,
)
from utils.importers.merged_cells import (
  get_cell_value_with_merge, detect_merged_cell_sets, validate_merged_cells_consistency,
)

logger = logging.getLogger(__name__)


# 模型类映射
MODEL_CLASS_MAP = {
  'brand': Brand,
  'depot': Depot,
  'merchant': Merchant,
  'power_type': PowerType,
  'chip_interface': ChipInterface,
  'chip_model': ChipModel,
  'locomotive_series': LocomotiveSeries,
  'carriage_series': CarriageSeries,
  'trainset_series': TrainsetSeries,
  'locomotive': Locomotive,
  'carriage': CarriageSet,
  'trainset': Trainset,
  'locomotive_head': LocomotiveHead,
  'carriage_model': CarriageModel,
  'locomotive_model': LocomotiveModel,
  'trainset_model': TrainsetModel,
  'light_brand': LightBrand,
  'light_model': LightModel
}


def execute_system_table_import(table_name, table_config, rows, source_to_target, conflict_mode):
  """
  执行系统表数据导入

  Args:
    table_name: 表名
    table_config: 表配置
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    conflict_mode: 冲突处理模式 ('skip' 或 'overwrite')

  Returns:
    int: 导入的记录数
  """
  from utils.helpers import generate_brand_abbreviation

  model_class = MODEL_CLASS_MAP.get(table_name)
  if not model_class:
    return 0

  count = 0
  for row in rows:
    # 映射行数据到目标字段
    mapped_row = {}
    for source_col, target_field in source_to_target.items():
      value = row.get(source_col)
      mapped_row[target_field] = value

    # 获取名称字段值（用于唯一性检查）
    name = mapped_row.get('name')
    if not name:
      continue

    # 品牌特殊处理：abbreviation 为空时自动生成
    if table_name == 'brand' and not mapped_row.get('abbreviation'):
      mapped_row['abbreviation'] = generate_brand_abbreviation(name)

    # 芯片型号特殊处理：提取接口名称（逗号分隔），不直接写入 mapped_row
    interface_names_raw = mapped_row.pop('interface_ids', None) if table_name == 'chip_model' else None

    # 检查是否存在
    existing = model_class.query.filter_by(name=name).first()

    if existing:
      if conflict_mode == 'skip':
        continue
      elif conflict_mode == 'overwrite':
        # 更新现有记录
        for field, value in mapped_row.items():
          if field != 'name' and value is not None:
            setattr(existing, field, value)
        # 芯片型号特殊处理：更新接口关联
        if table_name == 'chip_model' and interface_names_raw:
          _update_chip_model_interfaces(existing, interface_names_raw)
        count += 1
        continue

    # 创建新记录（不含 interface_ids 字段）
    mapped_row.pop('interface_ids', None)
    instance = model_class(**mapped_row)
    db.session.add(instance)
    db.session.flush()  # 确保 instance.id 可用
    # 芯片型号特殊处理：建立接口关联
    if table_name == 'chip_model' and interface_names_raw:
      _update_chip_model_interfaces(instance, interface_names_raw)
    count += 1

  db.session.commit()
  return count


def execute_locomotive_import(rows, source_to_target, field_configs, conflict_mode):
  """
  执行机车模型导入

  Args:
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    field_configs: 字段配置字典
    conflict_mode: 冲突处理模式

  Returns:
    int: 导入的记录数
  """
  count = 0
  for row in rows:
    # 映射行数据并解析外键
    mapped_data = {}
    for source_col, target_field in source_to_target.items():
      value = row.get(source_col)
      field_config = field_configs.get(target_field, {})
      ref_table = field_config.get('ref')

      if ref_table:
        # 解析外键
        resolved_id = resolve_foreign_key(ref_table, value)
        if field_config.get('required') and resolved_id is None and value:
          logger.warning(f"跳过机车行：找不到 {ref_table} '{value}'")
          mapped_data = None
          break
        mapped_data[target_field] = resolved_id
      else:
        mapped_data[target_field] = value

    if not mapped_data:
      continue

    # 检查必填字段
    brand_id = mapped_data.get('brand_id')
    scale = mapped_data.get('scale')
    if not brand_id or not scale:
      logger.warning(f"跳过机车行：缺少必填字段 brand_id={brand_id}, scale={scale}")
      continue

    # 检查冲突（locomotive_number 或 decoder_number 在比例内唯一）
    existing = None
    locomotive_number = mapped_data.get('locomotive_number')
    decoder_number = mapped_data.get('decoder_number')

    if scale and locomotive_number:
      existing = Locomotive.query.filter_by(scale=scale, locomotive_number=locomotive_number).first()
    if not existing and scale and decoder_number:
      existing = Locomotive.query.filter_by(scale=scale, decoder_number=decoder_number).first()

    if existing:
      if conflict_mode == 'skip':
        logger.info(f"跳过机车：冲突数据 比例={scale}, 机车号={locomotive_number}, 编号={decoder_number}")
        continue
      elif conflict_mode == 'overwrite':
        # 更新现有记录
        for field, value in mapped_data.items():
          if value is not None:
            if field == 'price':
              existing.price = value
              existing.total_price = calculate_price(value) if value else 0
            elif field == 'purchase_date':
              existing.purchase_date = parse_purchase_date(value)
            else:
              setattr(existing, field, value)
        count += 1
        continue

    # 创建新记录
    price = mapped_data.get('price')
    locomotive = Locomotive(
      series_id=mapped_data.get('series_id'),
      power_type_id=mapped_data.get('power_type_id'),
      model_id=mapped_data.get('model_id'),
      brand_id=brand_id,
      depot_id=mapped_data.get('depot_id'),
      plaque=mapped_data.get('plaque') or None,
      color=mapped_data.get('color') or None,
      scale=scale,
      locomotive_number=locomotive_number or None,
      decoder_number=mapped_data.get('decoder_number') or None,
      chip_interface_id=mapped_data.get('chip_interface_id'),
      chip_model_id=mapped_data.get('chip_model_id'),
      price=price or None,
      total_price=calculate_price(price) if price else 0,
      item_number=mapped_data.get('item_number') or None,
      purchase_date=parse_purchase_date(mapped_data.get('purchase_date')),
      merchant_id=mapped_data.get('merchant_id')
    )
    db.session.add(locomotive)
    count += 1

  db.session.commit()
  return count


def execute_trainset_import(rows, source_to_target, field_configs, conflict_mode):
  """
  执行动车组模型导入

  Args:
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    field_configs: 字段配置字典
    conflict_mode: 冲突处理模式

  Returns:
    int: 导入的记录数
  """
  count = 0
  for row in rows:
    # 映射行数据并解析外键
    mapped_data = {}
    for source_col, target_field in source_to_target.items():
      value = row.get(source_col)
      field_config = field_configs.get(target_field, {})
      ref_table = field_config.get('ref')

      if ref_table:
        resolved_id = resolve_foreign_key(ref_table, value)
        if field_config.get('required') and resolved_id is None and value:
          logger.warning(f"跳过动车组行：找不到 {ref_table} '{value}'")
          mapped_data = None
          break
        mapped_data[target_field] = resolved_id
      else:
        mapped_data[target_field] = value

    if not mapped_data:
      continue

    # 检查必填字段
    brand_id = mapped_data.get('brand_id')
    scale = mapped_data.get('scale')
    if not brand_id or not scale:
      logger.warning(f"跳过动车组行：缺少必填字段 brand_id={brand_id}, scale={scale}")
      continue

    # 检查冲突（trainset_number 在比例内唯一）
    existing = None
    trainset_number = mapped_data.get('trainset_number')

    if scale and trainset_number:
      existing = Trainset.query.filter_by(scale=scale, trainset_number=trainset_number).first()

    if existing:
      if conflict_mode == 'skip':
        logger.info(f"跳过动车组：冲突数据 比例={scale}, 动车号={trainset_number}")
        continue
      elif conflict_mode == 'overwrite':
        # 更新现有记录
        for field, value in mapped_data.items():
          if value is not None:
            if field == 'price':
              existing.price = value
              existing.total_price = calculate_price(value) if value else 0
            elif field == 'purchase_date':
              existing.purchase_date = parse_purchase_date(value)
            elif field == 'head_light':
              existing.head_light = parse_boolean(value) or False
            elif field == 'formation':
              existing.formation = safe_int(value)
            else:
              setattr(existing, field, value)
        count += 1
        continue

    # 创建新记录
    price = mapped_data.get('price')
    trainset = Trainset(
      series_id=mapped_data.get('series_id'),
      power_type_id=mapped_data.get('power_type_id'),
      model_id=mapped_data.get('model_id'),
      brand_id=brand_id,
      depot_id=mapped_data.get('depot_id'),
      plaque=mapped_data.get('plaque') or None,
      color=mapped_data.get('color') or None,
      scale=scale,
      formation=safe_int(mapped_data.get('formation')),
      trainset_number=trainset_number or None,
      decoder_number=mapped_data.get('decoder_number') or None,
      head_light=parse_boolean(mapped_data.get('head_light')) or False,
      light_model_id=mapped_data.get('light_model_id'),
      chip_interface_id=mapped_data.get('chip_interface_id'),
      chip_model_id=mapped_data.get('chip_model_id'),
      price=price or None,
      total_price=calculate_price(price) if price else 0,
      item_number=mapped_data.get('item_number') or None,
      purchase_date=parse_purchase_date(mapped_data.get('purchase_date')),
      merchant_id=mapped_data.get('merchant_id')
    )
    db.session.add(trainset)
    count += 1

  db.session.commit()
  return count


def execute_locomotive_head_import(rows, source_to_target, field_configs, conflict_mode):
  """
  执行先头车模型导入（无唯一约束，直接导入）

  Args:
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    field_configs: 字段配置字典
    conflict_mode: 冲突处理模式（先头车无唯一约束，此参数被忽略）

  Returns:
    int: 导入的记录数
  """
  count = 0
  for row in rows:
    # 映射行数据并解析外键
    mapped_data = {}
    for source_col, target_field in source_to_target.items():
      value = row.get(source_col)
      field_config = field_configs.get(target_field, {})
      ref_table = field_config.get('ref')

      if ref_table:
        resolved_id = resolve_foreign_key(ref_table, value)
        if field_config.get('required') and resolved_id is None and value:
          logger.warning(f"跳过先头车行：找不到 {ref_table} '{value}'")
          mapped_data = None
          break
        mapped_data[target_field] = resolved_id
      else:
        mapped_data[target_field] = value

    if not mapped_data:
      continue

    # 检查必填字段
    brand_id = mapped_data.get('brand_id')
    scale = mapped_data.get('scale')
    if not brand_id or not scale:
      logger.warning(f"跳过先头车行：缺少必填字段 brand_id={brand_id}, scale={scale}")
      continue

    # 创建新记录（先头车无唯一约束）
    price = mapped_data.get('price')
    locomotive_head = LocomotiveHead(
      model_id=mapped_data.get('model_id'),
      brand_id=brand_id,
      special_color=mapped_data.get('special_color') or None,
      scale=scale,
      head_light=parse_boolean(mapped_data.get('head_light')) or False,
      light_model_id=mapped_data.get('light_model_id'),
      price=price or None,
      total_price=calculate_price(price) if price else 0,
      item_number=mapped_data.get('item_number') or None,
      purchase_date=parse_purchase_date(mapped_data.get('purchase_date')),
      merchant_id=mapped_data.get('merchant_id')
    )
    db.session.add(locomotive_head)
    count += 1

  db.session.commit()
  return count


def execute_carriage_import(rows, source_to_target, field_configs, conflict_mode,
                            sheet=None, headers=None, set_detection_mode='merged'):
  """
  执行车厢套装导入（套装无唯一约束，按套装分组处理）

  Args:
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    field_configs: 字段配置字典
    conflict_mode: 冲突处理模式（车厢无唯一约束，此参数被忽略）
    sheet: openpyxl worksheet 对象（用于合并单元格检测）
    headers: 列标题列表（用于合并单元格检测）
    set_detection_mode: 套装检测模式
      - 'merged': 按合并单元格识别套装（默认）
      - 'row': 每行作为一个独立套装

  Returns:
    dict: {'count': int, 'warnings': list}
  """
  from models import CarriageItem

  count = 0
  warnings = []
  current_set_data = None
  current_items = []

  def save_carriage_set():
    """保存当前套装及其车厢项"""
    nonlocal count
    if not current_set_data:
      return

    brand_id = current_set_data.get('brand_id')
    scale = current_set_data.get('scale')
    if not brand_id or not scale:
      logger.warning(f"跳过车厢套装：缺少必填字段 brand_id={brand_id}, scale={scale}")
      return

    carriage_set = CarriageSet(
      brand_id=brand_id,
      series_id=current_set_data.get('series_id'),
      depot_id=current_set_data.get('depot_id'),
      train_number=current_set_data.get('train_number'),
      plaque=current_set_data.get('plaque'),
      item_number=current_set_data.get('item_number'),
      scale=scale,
      total_price=current_set_data.get('total_price', 0),
      purchase_date=current_set_data.get('purchase_date'),
      merchant_id=current_set_data.get('merchant_id')
    )
    db.session.add(carriage_set)
    db.session.flush()

    for item_data in current_items:
      if item_data.get('model_id'):
        item = CarriageItem(
          set_id=carriage_set.id,
          model_id=item_data.get('model_id'),
          car_number=item_data.get('car_number'),
          color=item_data.get('color'),
          light_model_id=find_id_by_name(LightModel, item_data.get('light_model'))
        )
        db.session.add(item)

    count += 1

  # 区分套装字段和车厢项字段
  set_fields = set()
  item_fields = set()
  for field_name, config in field_configs.items():
    if config.get('is_set_field'):
      set_fields.add(field_name)
    elif config.get('is_item_field'):
      item_fields.add(field_name)

  # 获取套装字段在 headers 中的索引
  set_field_indices = []
  if headers and set_detection_mode == 'merged':
    for source_col, target_field in source_to_target.items():
      if target_field in set_fields:
        try:
          idx = headers.index(source_col)
          set_field_indices.append(idx)
        except ValueError:
          pass

  # 尝试检测合并单元格
  set_groups = None
  if sheet and headers and set_detection_mode == 'merged' and set_field_indices:
    set_groups = detect_merged_cell_sets(sheet, headers, set_field_indices)
    if set_groups:
      # 验证合并单元格一致性
      consistency_warnings = validate_merged_cells_consistency(
        sheet, headers, set_field_indices, set_groups
      )
      warnings.extend(consistency_warnings)

  # 如果检测到合并单元格，按分组处理
  if set_groups:
    logger.info(f"检测到 {len(set_groups)} 个合并单元格套装分组")

    for group in set_groups:
      start_row = group['start_row'] - 2  # 转换为 0-based 行索引（跳过标题行）
      end_row = group['end_row'] - 2

      if start_row < 0 or start_row >= len(rows):
        continue

      # 收集该套装的所有行
      group_rows = rows[start_row:end_row + 1]
      if not group_rows:
        continue

      # 从第一行获取套装字段值
      first_row = group_rows[0]
      mapped_first = {}
      for source_col, target_field in source_to_target.items():
        value = first_row.get(source_col)
        field_config = field_configs.get(target_field, {})
        ref_table = field_config.get('ref')

        if ref_table:
          resolved_id = resolve_foreign_key(ref_table, value)
          mapped_first[target_field] = resolved_id
        else:
          mapped_first[target_field] = value

      brand_id = mapped_first.get('brand_id')
      scale = mapped_first.get('scale')

      if not brand_id or not scale:
        logger.warning(f"跳过套装分组（行 {start_row + 2}-{end_row + 2}）：缺少必填字段")
        continue

      # 创建套装数据
      current_set_data = {
        'brand_id': brand_id,
        'series_id': mapped_first.get('series_id'),
        'depot_id': mapped_first.get('depot_id'),
        'train_number': mapped_first.get('train_number') or None,
        'plaque': mapped_first.get('plaque') or None,
        'item_number': mapped_first.get('item_number') or None,
        'scale': scale,
        'total_price': safe_float(mapped_first.get('total_price')),
        'purchase_date': parse_purchase_date(mapped_first.get('purchase_date')),
        'merchant_id': mapped_first.get('merchant_id')
      }
      current_items = []

      # 添加所有车厢项
      for row in group_rows:
        mapped_data = {}
        for source_col, target_field in source_to_target.items():
          value = row.get(source_col)
          field_config = field_configs.get(target_field, {})
          ref_table = field_config.get('ref')

          if ref_table:
            resolved_id = resolve_foreign_key(ref_table, value)
            mapped_data[target_field] = resolved_id
          else:
            mapped_data[target_field] = value

        model_id = mapped_data.get('model_id')
        if model_id:
          current_items.append({
            'model_id': model_id,
            'car_number': mapped_data.get('car_number') or None,
            'color': mapped_data.get('color') or None,
            'light_model': mapped_data.get('light_model') or None
          })

      save_carriage_set()

  else:
    # 默认行为：按品牌+比例识别新套装
    # 如果 set_detection_mode == 'row'，则每行都是一个独立套装
    for row_idx, row in enumerate(rows):
      # 映射行数据并解析外键
      mapped_data = {}
      excel_row = row_idx + 2  # Excel 行号（1-based，跳过标题行）

      for source_col, target_field in source_to_target.items():
        value = row.get(source_col)
        field_config = field_configs.get(target_field, {})

        # 对于套装字段，如果值为 None 且有 worksheet，尝试从合并单元格获取值
        if value is None and sheet and headers and target_field in set_fields:
          try:
            col_idx = headers.index(source_col) + 1  # 转换为 1-based 列索引
            value = get_cell_value_with_merge(sheet, excel_row, col_idx)
          except (ValueError, IndexError):
            pass

        ref_table = field_config.get('ref')

        if ref_table:
          resolved_id = resolve_foreign_key(ref_table, value)
          mapped_data[target_field] = resolved_id
        else:
          mapped_data[target_field] = value

      # 判断是否是新套装
      brand_id = mapped_data.get('brand_id')
      scale = mapped_data.get('scale')

      if set_detection_mode == 'row':
        # 每行都是独立套装：只要有 brand+scale 就是新套装
        is_new_set = brand_id and scale
      else:
        # 默认：brand_id 和 scale 同时存在时认为是新套装
        is_new_set = brand_id and scale

      if is_new_set:
        # 保存之前的套装
        save_carriage_set()
        # 开始新套装
        current_set_data = {
          'brand_id': brand_id,
          'series_id': mapped_data.get('series_id'),
          'depot_id': mapped_data.get('depot_id'),
          'train_number': mapped_data.get('train_number') or None,
          'plaque': mapped_data.get('plaque') or None,
          'item_number': mapped_data.get('item_number') or None,
          'scale': scale,
          'total_price': safe_float(mapped_data.get('total_price')),
          'purchase_date': parse_purchase_date(mapped_data.get('purchase_date')),
          'merchant_id': mapped_data.get('merchant_id')
        }
        current_items = []

      # 添加车厢项
      model_id = mapped_data.get('model_id')
      if model_id and current_set_data:
        current_items.append({
          'model_id': model_id,
          'car_number': mapped_data.get('car_number') or None,
          'color': mapped_data.get('color') or None,
          'light_model': mapped_data.get('light_model') or None
        })

      # 在 'row' 模式下，每行结束时保存套装
      if set_detection_mode == 'row' and current_set_data:
        save_carriage_set()
        current_set_data = None
        current_items = []

    # 保存最后一个套装（非 row 模式）
    if set_detection_mode != 'row':
      save_carriage_set()

  db.session.commit()
  return {'count': count, 'warnings': warnings}


def execute_model_series_import(table_name, rows, source_to_target, conflict_mode):
  """
  执行机车/车厢/动车组系列导入

  Args:
    table_name: 表名 (locomotive_series, carriage_series, trainset_series)
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    conflict_mode: 冲突处理模式

  Returns:
    int: 导入的记录数
  """
  model_class = MODEL_CLASS_MAP.get(table_name)
  if not model_class:
    return 0

  count = 0
  for row in rows:
    name = None
    for source_col, target_field in source_to_target.items():
      if target_field == 'name':
        name = row.get(source_col)
        break

    if not name:
      continue

    existing = model_class.query.filter_by(name=name).first()
    if existing:
      if conflict_mode == 'skip':
        continue
      # overwrite 模式下无需更新，因为只有 name 字段
      continue

    series = model_class(name=name)
    db.session.add(series)
    count += 1

  db.session.commit()
  return count


def execute_model_model_import(table_name, rows, source_to_target, field_configs, conflict_mode):
  """
  执行机车/车厢/动车组车型导入（车型没有唯一名称约束，直接导入）

  Args:
    table_name: 表名 (locomotive_model, carriage_model, trainset_model)
    rows: 数据行列表
    source_to_target: 源列到目标字段的映射
    field_configs: 字段配置字典
    conflict_mode: 冲突处理模式（车型无唯一约束，此参数被忽略）

  Returns:
    int: 导入的记录数
  """
  model_class = MODEL_CLASS_MAP.get(table_name)
  if not model_class:
    return 0

  count = 0
  for row in rows:
    mapped_data = {}
    for source_col, target_field in source_to_target.items():
      value = row.get(source_col)
      field_config = field_configs.get(target_field, {})
      ref_table = field_config.get('ref')

      if ref_table:
        resolved_id = resolve_foreign_key(ref_table, value)
        mapped_data[target_field] = resolved_id
      else:
        mapped_data[target_field] = value

    name = mapped_data.get('name')
    if not name:
      continue

    model_instance = model_class(**mapped_data)
    db.session.add(model_instance)
    count += 1

  db.session.commit()
  return count
