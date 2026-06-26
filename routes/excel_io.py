"""
传统 Excel 导入导出 Blueprint（从 routes/api.py 拆分）

包含:
  - /api/import/excel: 智能 Excel 导入（preview / skip / overwrite 三模式）
  - /api/export/excel: 数据导出（models / system / all 三模式）

注意: 自定义导入向导（/api/custom-import/*）已拆分到 routes/custom_import.py。
"""
from flask import Blueprint, request, jsonify, send_file
from models import db, LocomotiveModel, CarriageModel, TrainsetModel
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, CarriageSeries, TrainsetSeries, PowerType
from models import CarriageItem, LightModel
from utils.helpers import parse_purchase_date, safe_int, safe_float, parse_boolean
from utils.price_calculator import calculate_price
from utils.excel_safety import validate_excel_upload
from utils.importers.helpers import find_id_by_name
from utils.excel_exporter import export_to_excel_core, build_export_filename
import logging

logger = logging.getLogger(__name__)
excel_io_bp = Blueprint('excel_io', __name__, url_prefix='')


@excel_io_bp.route('/api/import/excel', methods=['POST'])
def import_from_excel():
  """从 Excel 文件导入数据 - 支持 preview、skip、overwrite 模式"""
  try:
    if 'file' not in request.files:
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not file.filename.lower().endswith('.xlsx'):
      return jsonify({'success': False, 'error': '文件格式错误，请上传Excel文件'}), 400

    # 获取模式参数：preview（只检查）、skip（跳过冲突）、overwrite（覆盖冲突）
    # 默认为 skip（向后兼容），前端显式传 preview 进行预检查
    mode = request.form.get('mode', 'skip')

    try:
      workbook = validate_excel_upload(file)
    except ValueError as e:
      return jsonify({'success': False, 'error': str(e)}), 400
    all_data = {}  # 存储 all sheet 数据

    # 读取所有 sheet 数据
    for sheet_name in workbook.sheetnames:
      sheet = workbook[sheet_name]
      data = []
      headers = None
      for row_idx, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if row_idx == 1:
          headers = [cell for cell in row if cell is not None]
        else:
          if any(cell is not None for cell in row):
            data.append(dict(zip(headers, row)))
      if data:
        all_data[sheet_name] = data

    if not all_data:
      return jsonify({'success': True, 'summary': {}, 'message': '没有找到可导入的数据'})

    # 预检查冲突
    conflicts = check_import_conflicts(all_data)

    if mode == 'preview':
      # 只返回预检查结果
      return jsonify({
        'success': True,
        'preview': True,
        'conflicts': conflicts,
        'has_conflicts': len(conflicts) > 0,
        'sheets': list(all_data.keys())
      })

    # 执行导入
    summary = {}
    errors = []

    # 模型数据 sheet 名称映射
    model_sheets = {
      '机车': ('机车模型', import_locomotive_data_with_mode),
      '车厢': ('车厢模型', import_carriage_data_with_mode),
      '动车组': ('动车组模型', import_trainset_data_with_mode),
      '先头车': ('先头车模型', import_locomotive_head_data_with_mode)
    }

    # 系统信息 sheet 名称映射
    system_sheets = {
      '品牌': ('品牌', import_brand_data_with_mode),
      '机务段': ('机务段', import_depot_data_with_mode),
      '车辆段': ('机务段', import_depot_data_with_mode),
      '商家': ('商家', import_merchant_data_with_mode),
      '动力类型': ('动力类型', import_power_type_data_with_mode),
      '芯片接口': ('芯片接口', import_chip_interface_data_with_mode),
      '芯片型号': ('芯片型号', import_chip_model_data_with_mode),
      '机车系列': ('机车系列', import_locomotive_series_data_with_mode),
      '机关系列': ('机车系列', import_locomotive_series_data_with_mode),
      '车厢系列': ('车厢系列', import_carriage_series_data_with_mode),
      '动车组系列': ('动车组系列', import_trainset_series_data_with_mode),
      '机车车型': ('机车车型', import_locomotive_model_data_with_mode),
      '车厢车型': ('车厢车型', import_carriage_model_data_with_mode),
      '动车组车型': ('动车组车型', import_trainset_model_data_with_mode)
    }

    for sheet_name, data in all_data.items():
      try:
        if sheet_name in model_sheets:
          display_name, import_func = model_sheets[sheet_name]
          count = import_func(data, mode)
          summary[display_name] = count
        elif sheet_name in system_sheets:
          display_name, import_func = system_sheets[sheet_name]
          count = import_func(data, mode)
          summary[display_name] = count
        else:
          logger.warning(f"Unknown sheet name: {sheet_name}")
      except Exception as e:
        db.session.rollback()
        errors.append(f"{sheet_name}: {str(e)}")
        logger.error(f"Error importing sheet {sheet_name}: {str(e)}", exc_info=True)

    if errors:
      return jsonify({'success': False, 'error': '部分导入失败: ' + '; '.join(errors)}), 400

    logger.info(f"Excel import completed: {summary}, mode={mode}")
    return jsonify({'success': True, 'summary': summary})

  except Exception as e:
    db.session.rollback()
    logger.error(f"Excel import failed: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '导入失败，请稍后重试'}), 500


def check_import_conflicts(all_data):
  """检查导入数据中的冲突"""
  conflicts = []

  # 检查系统信息名称冲突
  system_name_checks = [
    ('品牌', '品牌', Brand, 'name'),
    ('商家', '商家', Merchant, 'name'),
    ('动力类型', '动力类型', PowerType, 'name'),
    ('机务段', '机务段', Depot, 'name'),
    ('车辆段', '机务段', Depot, 'name'),
    ('芯片接口', '芯片接口', ChipInterface, 'name'),
    ('芯片型号', '芯片型号', ChipModel, 'name'),
    ('机车系列', '机车系列', LocomotiveSeries, 'name'),
    ('车厢系列', '车厢系列', CarriageSeries, 'name'),
    ('动车组系列', '动车组系列', TrainsetSeries, 'name'),
  ]

  for sheet_name, display_name, model, field in system_name_checks:
    if sheet_name in all_data:
      for row in all_data[sheet_name]:
        name = row.get('名称') or row.get(field) or row.get(display_name)
        if name:
          existing = model.query.filter_by(name=name).first()
          if existing:
            conflicts.append({
              'type': display_name,
              'field': '名称',
              'value': name,
              'message': f"{display_name} '{name}' 已存在"
            })

  # 检查机车冲突：同一比例内机车号或编号唯一
  if '机车' in all_data:
    for row in all_data['机车']:
      scale = row.get('比例')
      locomotive_number = row.get('机车号')
      decoder_number = row.get('编号')

      if scale and locomotive_number:
        existing = Locomotive.query.filter_by(scale=scale, locomotive_number=locomotive_number).first()
        if existing:
          conflicts.append({
            'type': '机车模型',
            'field': '机车号',
            'value': f'{scale} 比例 - {locomotive_number}',
            'message': f"机车号 '{locomotive_number}' 在比例 '{scale}' 中已存在"
          })

      if scale and decoder_number:
        existing = Locomotive.query.filter_by(scale=scale, decoder_number=decoder_number).first()
        if existing:
          conflicts.append({
            'type': '机车模型',
            'field': '编号',
            'value': f'{scale} 比例 - {decoder_number}',
            'message': f"编号 '{decoder_number}' 在比例 '{scale}' 中已存在"
          })

  # 检查动车组冲突：同一比例内动车号唯一
  if '动车组' in all_data:
    for row in all_data['动车组']:
      scale = row.get('比例')
      trainset_number = row.get('动车号')

      if scale and trainset_number:
        existing = Trainset.query.filter_by(scale=scale, trainset_number=trainset_number).first()
        if existing:
          conflicts.append({
            'type': '动车组模型',
            'field': '动车号',
            'value': f'{scale} 比例 - {trainset_number}',
            'message': f"动车号 '{trainset_number}' 在比例 '{scale}' 中已存在"
          })

  return conflicts


def import_locomotive_data_with_mode(data, mode='skip'):
  """导入机车模型数据，支持 skip/overwrite 模式"""
  count = 0
  for row in data:
    brand_name = row.get('品牌')
    scale = row.get('比例')
    if not brand_name or not scale:
      logger.warning(f"跳过机车行：缺少必填字段 品牌={brand_name}, 比例={scale}")
      continue

    brand_id = find_id_by_name(Brand, brand_name)
    if not brand_id:
      logger.warning(f"跳过机车行：找不到品牌 '{brand_name}'")
      continue

    series_id = find_id_by_name(LocomotiveSeries, row.get('系列'))
    power_type_id = find_id_by_name(PowerType, row.get('动力'))
    model_id = find_id_by_name(LocomotiveModel, row.get('车型'),
      lambda q: q.filter_by(name=row.get('车型'), series_id=series_id, power_type_id=power_type_id).first())

    locomotive_number = row.get('机车号') or None
    decoder_number = row.get('编号') or None

    # 检查冲突
    existing = None
    if scale and locomotive_number:
      existing = Locomotive.query.filter_by(scale=scale, locomotive_number=locomotive_number).first()
    if not existing and scale and decoder_number:
      existing = Locomotive.query.filter_by(scale=scale, decoder_number=decoder_number).first()

    if existing:
      if mode == 'skip':
        logger.info(f"跳过机车：冲突数据 比例={scale}, 机车号={locomotive_number}, 编号={decoder_number}")
        continue
      elif mode == 'overwrite':
        # 更新现有记录
        existing.series_id = series_id
        existing.power_type_id = power_type_id
        existing.model_id = model_id
        existing.brand_id = brand_id
        existing.depot_id = find_id_by_name(Depot, row.get('机务段'))
        existing.plaque = row.get('挂牌') or None
        existing.color = row.get('颜色') or None
        existing.decoder_number = decoder_number
        existing.chip_interface_id = find_id_by_name(ChipInterface, row.get('芯片接口'))
        existing.chip_model_id = find_id_by_name(ChipModel, row.get('芯片型号'))
        existing.price = row.get('价格') or None
        existing.total_price = calculate_price(row.get('价格')) if row.get('价格') else 0
        existing.item_number = row.get('货号') or None
        existing.purchase_date = parse_purchase_date(row.get('购买日期'))
        existing.merchant_id = find_id_by_name(Merchant, row.get('购买商家'))
        count += 1
        continue

    locomotive = Locomotive(
      series_id=series_id,
      power_type_id=power_type_id,
      model_id=model_id,
      brand_id=brand_id,
      depot_id=find_id_by_name(Depot, row.get('机务段')),
      plaque=row.get('挂牌') or None,
      color=row.get('颜色') or None,
      scale=scale,
      locomotive_number=locomotive_number,
      decoder_number=decoder_number,
      chip_interface_id=find_id_by_name(ChipInterface, row.get('芯片接口')),
      chip_model_id=find_id_by_name(ChipModel, row.get('芯片型号')),
      price=row.get('价格') or None,
      total_price=calculate_price(row.get('价格')) if row.get('价格') else 0,
      item_number=row.get('货号') or None,
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(locomotive)
    count += 1

  db.session.commit()
  return count


def import_carriage_data_with_mode(data, mode='skip'):
  """导入车厢模型数据 - 按套装分组处理，车厢没有唯一性约束，直接导入"""
  count = 0
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

  for row in data:
    brand_name = row.get('品牌')
    scale = row.get('比例')
    is_new_set = brand_name and scale

    if is_new_set:
      save_carriage_set()
      brand_id = find_id_by_name(Brand, brand_name)
      current_set_data = {
        'brand_id': brand_id,
        'series_id': find_id_by_name(CarriageSeries, row.get('系列')),
        'depot_id': find_id_by_name(Depot, row.get('车辆段')),
        'train_number': row.get('车次') or None,
        'plaque': row.get('挂牌') or None,
        'item_number': row.get('货号') or None,
        'scale': scale,
        'total_price': safe_float(row.get('总价')),
        'purchase_date': parse_purchase_date(row.get('购买日期')),
        'merchant_id': find_id_by_name(Merchant, row.get('购买商家'))
      }
      current_items = []

    model_name = row.get('车型')
    if model_name and current_set_data:
      model_id = find_id_by_name(CarriageModel, model_name)
      current_items.append({
        'model_id': model_id,
        'car_number': row.get('车辆号') or None,
        'color': row.get('颜色') or None,
        'light_model': row.get('灯光') or None
      })

  save_carriage_set()
  db.session.commit()
  return count


def import_trainset_data_with_mode(data, mode='skip'):
  """导入动车组模型数据，支持 skip/overwrite 模式"""
  count = 0
  for row in data:
    brand_name = row.get('品牌')
    scale = row.get('比例')
    if not brand_name or not scale:
      logger.warning(f"跳过动车组行：缺少必填字段 品牌={brand_name}, 比例={scale}")
      continue

    brand_id = find_id_by_name(Brand, brand_name)
    if not brand_id:
      logger.warning(f"跳过动车组行：找不到品牌 '{brand_name}'")
      continue

    series_id = find_id_by_name(TrainsetSeries, row.get('系列'))
    power_type_id = find_id_by_name(PowerType, row.get('动力'))
    model_id = find_id_by_name(TrainsetModel, row.get('车型'),
      lambda q: q.filter_by(name=row.get('车型'), series_id=series_id, power_type_id=power_type_id).first())

    trainset_number = row.get('动车号') or None

    # 检查冲突
    existing = None
    if scale and trainset_number:
      existing = Trainset.query.filter_by(scale=scale, trainset_number=trainset_number).first()

    if existing:
      if mode == 'skip':
        logger.info(f"跳过动车组：冲突数据 比例={scale}, 动车号={trainset_number}")
        continue
      elif mode == 'overwrite':
        existing.series_id = series_id
        existing.power_type_id = power_type_id
        existing.model_id = model_id
        existing.brand_id = brand_id
        existing.depot_id = find_id_by_name(Depot, row.get('动车段'))
        existing.plaque = row.get('挂牌') or None
        existing.color = row.get('颜色') or None
        existing.formation = safe_int(row.get('编组'))
        existing.decoder_number = row.get('编号') or None
        existing.head_light = parse_boolean(row.get('头车灯')) or False
        existing.light_model_id = find_id_by_name(LightModel, row.get('室内灯'))
        existing.chip_interface_id = find_id_by_name(ChipInterface, row.get('芯片接口'))
        existing.chip_model_id = find_id_by_name(ChipModel, row.get('芯片型号'))
        existing.price = row.get('价格') or None
        existing.total_price = calculate_price(row.get('价格')) if row.get('价格') else 0
        existing.item_number = row.get('货号') or None
        existing.purchase_date = parse_purchase_date(row.get('购买日期'))
        existing.merchant_id = find_id_by_name(Merchant, row.get('购买商家'))
        count += 1
        continue

    trainset = Trainset(
      series_id=series_id,
      power_type_id=power_type_id,
      model_id=model_id,
      brand_id=brand_id,
      depot_id=find_id_by_name(Depot, row.get('动车段')),
      plaque=row.get('挂牌') or None,
      color=row.get('颜色') or None,
      scale=scale,
      formation=safe_int(row.get('编组')),
      trainset_number=trainset_number,
      decoder_number=row.get('编号') or None,
      head_light=parse_boolean(row.get('头车灯')) or False,
      light_model_id=find_id_by_name(LightModel, row.get('室内灯')),
      chip_interface_id=find_id_by_name(ChipInterface, row.get('芯片接口')),
      chip_model_id=find_id_by_name(ChipModel, row.get('芯片型号')),
      price=row.get('价格') or None,
      total_price=calculate_price(row.get('价格')) if row.get('价格') else 0,
      item_number=row.get('货号') or None,
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(trainset)
    count += 1

  db.session.commit()
  return count


def import_locomotive_head_data_with_mode(data, mode='skip'):
  """导入先头车模型数据，先头车没有唯一性约束，直接导入"""
  count = 0
  for row in data:
    brand_name = row.get('品牌')
    scale = row.get('比例')
    if not brand_name or not scale:
      logger.warning(f"跳过先头车行：缺少必填字段 品牌={brand_name}, 比例={scale}")
      continue

    brand_id = find_id_by_name(Brand, brand_name)
    if not brand_id:
      logger.warning(f"跳过先头车行：找不到品牌 '{brand_name}'")
      continue

    model_id = find_id_by_name(TrainsetModel, row.get('车型'))

    locomotive_head = LocomotiveHead(
      model_id=model_id,
      brand_id=brand_id,
      special_color=row.get('涂装') or None,
      scale=scale,
      head_light=parse_boolean(row.get('头车灯')) or False,
      light_model_id=find_id_by_name(LightModel, row.get('室内灯')),
      price=row.get('价格') or None,
      total_price=calculate_price(row.get('价格')) if row.get('价格') else 0,
      item_number=row.get('货号') or None,
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(locomotive_head)
    count += 1

  db.session.commit()
  return count


# 系统信息导入函数（支持 skip/overwrite 模式）
def import_brand_data_with_mode(data, mode='skip'):
  """导入品牌数据"""
  from utils.helpers import generate_brand_abbreviation
  count = 0
  for row in data:
    name = row.get('名称') or row.get('品牌')
    if not name:
      continue
    existing = Brand.query.filter_by(name=name).first()
    if existing:
      if mode == 'skip':
        continue
      elif mode == 'overwrite':
        existing.search_url = row.get('搜索地址') or row.get('search_url') or existing.search_url
        count += 1
        continue
    abbreviation = row.get('缩写') or row.get('abbreviation')
    if not abbreviation:
      abbreviation = generate_brand_abbreviation(name)
    brand = Brand(
      name=name,
      abbreviation=abbreviation,
      search_url=row.get('搜索地址') or row.get('search_url') or None
    )
    db.session.add(brand)
    count += 1
  db.session.commit()
  return count


def _import_simple_name_data(model_class, data, name_keys, mode='skip'):
  """导入单 name 字段系统表（depot/merchant/power_type/chip_interface/chip_model/各系列）的泛型实现。

  Args:
    model_class: SQLAlchemy 模型类
    data: 行数据列表
    name_keys: 名称列名候选（按优先级）
    mode: skip/overwrite

  Returns:
    int: 处理数量
  """
  count = 0
  for row in data:
    name = next((row.get(k) for k in name_keys if row.get(k)), None)
    if not name:
      continue
    if model_class.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue  # 单 name 字段 overwrite 无需更新
    db.session.add(model_class(name=name))
    count += 1
  db.session.commit()
  return count


def import_depot_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(Depot, data, ['名称', '机务段', '车辆段'], mode)


def import_merchant_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(Merchant, data, ['名称', '商家'], mode)


def import_power_type_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(PowerType, data, ['名称', '动力类型'], mode)


def import_chip_interface_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(ChipInterface, data, ['名称', '芯片接口'], mode)


def import_chip_model_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(ChipModel, data, ['名称', '芯片型号'], mode)


def import_locomotive_series_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(LocomotiveSeries, data, ['名称', '系列'], mode)


def import_carriage_series_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(CarriageSeries, data, ['名称', '系列'], mode)


def import_trainset_series_data_with_mode(data, mode='skip'):
  return _import_simple_name_data(TrainsetSeries, data, ['名称', '系列'], mode)


def import_locomotive_model_data_with_mode(data, mode='skip'):
  """导入机车车型数据，车型没有唯一名称约束，直接导入"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('车型')
    if not name:
      continue
    model = LocomotiveModel(
      name=name,
      series_id=find_id_by_name(LocomotiveSeries, row.get('系列')),
      power_type_id=find_id_by_name(PowerType, row.get('动力类型'))
    )
    db.session.add(model)
    count += 1
  db.session.commit()
  return count


def import_carriage_model_data_with_mode(data, mode='skip'):
  """导入车厢车型数据，车型没有唯一名称约束，直接导入"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('车型')
    if not name:
      continue
    model = CarriageModel(
      name=name,
      series_id=find_id_by_name(CarriageSeries, row.get('系列')),
      type=row.get('类型') or '客车'
    )
    db.session.add(model)
    count += 1
  db.session.commit()
  return count


def import_trainset_model_data_with_mode(data, mode='skip'):
  """导入动车组车型数据，车型没有唯一名称约束，直接导入"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('车型')
    if not name:
      continue
    model = TrainsetModel(
      name=name,
      series_id=find_id_by_name(TrainsetSeries, row.get('系列')),
      power_type_id=find_id_by_name(PowerType, row.get('动力类型'))
    )
    db.session.add(model)
    count += 1
  db.session.commit()
  return count


@excel_io_bp.route('/api/export/excel')
def export_to_excel():
  """导出数据到Excel - 支持 mode 参数: models(模型数据), system(系统信息), all(全部)"""
  try:
    mode = request.args.get('mode', 'models')
    output = export_to_excel_core(mode)
    filename = build_export_filename(mode)
    return send_file(
      output,
      as_attachment=True,
      download_name=filename,
      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
  except ValueError as e:
    # 数据不存在的业务错误，返回 400
    return jsonify({'success': False, 'error': str(e)}), 400
  except Exception as e:
    logger.error(f"Excel export failed: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '导出失败，请稍后重试'}), 500
