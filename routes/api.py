"""
API 路由 Blueprint
包含自动填充 API 和 Excel 导入导出
"""
from flask import Blueprint, request, jsonify, send_file
from models import db, LocomotiveModel, CarriageModel, TrainsetModel
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, CarriageSeries, TrainsetSeries, PowerType
from models import CarriageItem
from utils.helpers import parse_purchase_date, safe_int, safe_float, parse_boolean
from utils.price_calculator import calculate_price
from io import BytesIO
from datetime import datetime
import openpyxl
import logging
import random

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='')


# 自动填充 API
@api_bp.route('/api/auto-fill/locomotive/<int:model_id>')
def auto_fill_locomotive(model_id):
  """机车车型自动填充"""
  model = LocomotiveModel.query.get_or_404(model_id)
  return jsonify({
    'series_id': model.series_id,
    'power_type_id': model.power_type_id
  })


@api_bp.route('/api/auto-fill/carriage/<int:model_id>')
def auto_fill_carriage(model_id):
  """车厢车型自动填充"""
  model = CarriageModel.query.get_or_404(model_id)
  return jsonify({
    'series_id': model.series_id,
    'type': model.type
  })


@api_bp.route('/api/auto-fill/trainset/<int:model_id>')
def auto_fill_trainset(model_id):
  """动车组车型自动填充"""
  model = TrainsetModel.query.get_or_404(model_id)
  return jsonify({
    'series_id': model.series_id,
    'power_type_id': model.power_type_id
  })


# Excel 导入导出
def find_id_by_name(model, name, custom_query=None):
  """根据名称查找模型的ID"""
  if not name:
    return None

  if custom_query:
    result = custom_query(model.query)
    return result.id if result else None

  obj = model.query.filter_by(name=name).first()
  return obj.id if obj else None


def validate_required(value, field_name):
  """验证必填字段"""
  if not value:
    raise ValueError(f"必填字段 '{field_name}' 不能为空")
  return value


@api_bp.route('/api/import/excel', methods=['POST'])
def import_from_excel():
  """从 Excel 文件导入数据 - 支持 preview、skip、overwrite 模式"""
  try:
    if 'file' not in request.files:
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
      return jsonify({'success': False, 'error': '文件格式错误，请上传Excel文件'}), 400

    # 获取模式参数：preview（只检查）、skip（跳过冲突）、overwrite（覆盖冲突）
    # 默认为 skip（向后兼容），前端显式传 preview 进行预检查
    mode = request.form.get('mode', 'skip')

    workbook = openpyxl.load_workbook(file)
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
    return jsonify({'success': False, 'error': str(e)}), 500


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
          lighting=item_data.get('lighting')
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
        'lighting': row.get('灯光') or None
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
        existing.interior_light = row.get('室内灯') or None
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
      interior_light=row.get('室内灯') or None,
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
      interior_light=row.get('室内灯') or None,
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
    brand = Brand(
      name=name,
      search_url=row.get('搜索地址') or row.get('search_url') or None
    )
    db.session.add(brand)
    count += 1
  db.session.commit()
  return count


def import_depot_data_with_mode(data, mode='skip'):
  """导入机务段/车辆段数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('机务段') or row.get('车辆段')
    if not name:
      continue
    if Depot.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      # overwrite 模式下无需更新，因为只有 name 字段
      continue
    depot = Depot(name=name)
    db.session.add(depot)
    count += 1
  db.session.commit()
  return count


def import_merchant_data_with_mode(data, mode='skip'):
  """导入商家数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('商家')
    if not name:
      continue
    if Merchant.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    merchant = Merchant(name=name)
    db.session.add(merchant)
    count += 1
  db.session.commit()
  return count


def import_power_type_data_with_mode(data, mode='skip'):
  """导入动力类型数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('动力类型')
    if not name:
      continue
    if PowerType.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    power_type = PowerType(name=name)
    db.session.add(power_type)
    count += 1
  db.session.commit()
  return count


def import_chip_interface_data_with_mode(data, mode='skip'):
  """导入芯片接口数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('芯片接口')
    if not name:
      continue
    if ChipInterface.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    chip_interface = ChipInterface(name=name)
    db.session.add(chip_interface)
    count += 1
  db.session.commit()
  return count


def import_chip_model_data_with_mode(data, mode='skip'):
  """导入芯片型号数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('芯片型号')
    if not name:
      continue
    if ChipModel.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    chip_model = ChipModel(name=name)
    db.session.add(chip_model)
    count += 1
  db.session.commit()
  return count


def import_locomotive_series_data_with_mode(data, mode='skip'):
  """导入机车系列数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('系列')
    if not name:
      continue
    if LocomotiveSeries.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    series = LocomotiveSeries(name=name)
    db.session.add(series)
    count += 1
  db.session.commit()
  return count


def import_carriage_series_data_with_mode(data, mode='skip'):
  """导入车厢系列数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('系列')
    if not name:
      continue
    if CarriageSeries.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    series = CarriageSeries(name=name)
    db.session.add(series)
    count += 1
  db.session.commit()
  return count


def import_trainset_series_data_with_mode(data, mode='skip'):
  """导入动车组系列数据"""
  count = 0
  for row in data:
    name = row.get('名称') or row.get('系列')
    if not name:
      continue
    if TrainsetSeries.query.filter_by(name=name).first():
      if mode == 'skip':
        continue
      continue
    series = TrainsetSeries(name=name)
    db.session.add(series)
    count += 1
  db.session.commit()
  return count


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


@api_bp.route('/api/export/excel')
def export_to_excel():
  """导出数据到Excel - 支持 mode 参数: models(模型数据), system(系统信息), all(全部)"""
  try:
    mode = request.args.get('mode', 'models')

    # 检查是否有数据
    has_model_data = (
      Locomotive.query.count() > 0 or
      CarriageSet.query.count() > 0 or
      Trainset.query.count() > 0 or
      LocomotiveHead.query.count() > 0
    )
    has_system_data = (
      Brand.query.count() > 0 or
      Depot.query.count() > 0 or
      Merchant.query.count() > 0 or
      PowerType.query.count() > 0 or
      ChipInterface.query.count() > 0 or
      ChipModel.query.count() > 0
    )

    if mode == 'models' and not has_model_data:
      return jsonify({'success': False, 'error': '当前没有可导出的模型数据'}), 400
    if mode == 'system' and not has_system_data:
      return jsonify({'success': False, 'error': '当前没有可导出的系统信息'}), 400
    if mode == 'all' and not has_model_data and not has_system_data:
      return jsonify({'success': False, 'error': '当前没有可导出的数据'}), 400

    workbook = openpyxl.Workbook()

    if 'Sheet' in workbook.sheetnames:
      workbook.remove(workbook['Sheet'])

    # 导出模型数据（models 或 all 模式）
    if mode in ('models', 'all'):
      # 导出机车模型
      if Locomotive.query.count() > 0:
        sheet = workbook.create_sheet('机车')
        headers = ['系列', '动力', '车型', '品牌', '机务段', '挂牌', '颜色', '比例', '机车号', '编号',
               '芯片接口', '芯片型号', '价格', '总价', '货号', '购买日期', '购买商家']
        sheet.append(headers)

        for loco in Locomotive.query.all():
          sheet.append([
            loco.series.name if loco.series else '',
            loco.power_type.name if loco.power_type else '',
            loco.model.name if loco.model else '',
            loco.brand.name if loco.brand else '',
            loco.depot.name if loco.depot else '',
            loco.plaque or '',
            loco.color or '',
            loco.scale or '',
            loco.locomotive_number or '',
            loco.decoder_number or '',
            loco.chip_interface.name if loco.chip_interface else '',
            loco.chip_model.name if loco.chip_model else '',
            loco.price or '',
            loco.total_price or '',
            loco.item_number or '',
            loco.purchase_date.strftime('%Y-%m-%d') if loco.purchase_date else '',
            loco.merchant.name if loco.merchant else ''
          ])

      # 导出车厢模型（使用合并单元格标识套装）
      if CarriageSet.query.count() > 0:
        sheet = workbook.create_sheet('车厢')
        headers = ['品牌', '系列', '车辆段', '车次', '挂牌', '货号', '比例', '车型', '车辆号', '颜色', '灯光', '总价', '购买日期', '购买商家']
        sheet.append(headers)

        current_row = 2  # 从第2行开始（第1行是表头）
        for carriage_set in CarriageSet.query.all():
          items = carriage_set.items
          if not items:
            # 无车厢项的套装，单独一行
            sheet.append([
              carriage_set.brand.name if carriage_set.brand else '',
              carriage_set.series.name if carriage_set.series else '',
              carriage_set.depot.name if carriage_set.depot else '',
              carriage_set.train_number or '',
              carriage_set.plaque or '',
              carriage_set.item_number or '',
              carriage_set.scale or '',
              '', '', '', '',
              carriage_set.total_price or '',
              carriage_set.purchase_date.strftime('%Y-%m-%d') if carriage_set.purchase_date else '',
              carriage_set.merchant.name if carriage_set.merchant else ''
            ])
            current_row += 1
          else:
            # 有车厢项的套装，合并公共信息列
            start_row = current_row
            for item in items:
              sheet.append([
                carriage_set.brand.name if carriage_set.brand else '',
                carriage_set.series.name if carriage_set.series else '',
                carriage_set.depot.name if carriage_set.depot else '',
                carriage_set.train_number or '',
                carriage_set.plaque or '',
                carriage_set.item_number or '',
                carriage_set.scale or '',
                item.model.name if item.model else '',
                item.car_number or '',
                item.color or '',
                item.lighting or '',
                carriage_set.total_price or '',
                carriage_set.purchase_date.strftime('%Y-%m-%d') if carriage_set.purchase_date else '',
                carriage_set.merchant.name if carriage_set.merchant else ''
              ])
              current_row += 1

            # 合并公共信息列（前7列：A-G，即品牌到比例）
            # 合并总价、购买日期、购买商家列（L-N，即第12-14列）
            if len(items) > 1:
              end_row = current_row - 1
              # 合并前7列（品牌、系列、车辆段、车次、挂牌、货号、比例）
              for col in range(1, 8):  # A-G 列
                sheet.merge_cells(start_row=start_row, start_column=col, end_row=end_row, end_column=col)
              # 合并后3列（总价、购买日期、购买商家）
              for col in range(12, 15):  # L-N 列
                sheet.merge_cells(start_row=start_row, start_column=col, end_row=end_row, end_column=col)

      # 导出动车组模型
      if Trainset.query.count() > 0:
        sheet = workbook.create_sheet('动车组')
        headers = ['系列', '动力', '车型', '品牌', '动车段', '挂牌', '颜色', '比例', '编组', '动车号', '编号',
               '头车灯', '室内灯', '芯片接口', '芯片型号', '价格', '总价', '货号', '购买日期', '购买商家']
        sheet.append(headers)

        for ts in Trainset.query.all():
          sheet.append([
            ts.series.name if ts.series else '',
            ts.power_type.name if ts.power_type else '',
            ts.model.name if ts.model else '',
            ts.brand.name if ts.brand else '',
            ts.depot.name if ts.depot else '',
            ts.plaque or '',
            ts.color or '',
            ts.scale or '',
            ts.formation or '',
            ts.trainset_number or '',
            ts.decoder_number or '',
            '是' if ts.head_light else '否',
            ts.interior_light or '',
            ts.chip_interface.name if ts.chip_interface else '',
            ts.chip_model.name if ts.chip_model else '',
            ts.price or '',
            ts.total_price or '',
            ts.item_number or '',
            ts.purchase_date.strftime('%Y-%m-%d') if ts.purchase_date else '',
            ts.merchant.name if ts.merchant else ''
          ])

      # 导出先头车模型
      if LocomotiveHead.query.count() > 0:
        sheet = workbook.create_sheet('先头车')
        headers = ['车型', '品牌', '涂装', '比例', '头车灯', '室内灯', '价格', '总价', '货号', '购买日期', '购买商家']
        sheet.append(headers)

        for head in LocomotiveHead.query.all():
          sheet.append([
            head.model.name if head.model else '',
            head.brand.name if head.brand else '',
            head.special_color or '',
            head.scale or '',
            '是' if head.head_light else '否',
            head.interior_light or '',
            head.price or '',
            head.total_price or '',
            head.item_number or '',
            head.purchase_date.strftime('%Y-%m-%d') if head.purchase_date else '',
            head.merchant.name if head.merchant else ''
          ])

    # 导出系统信息（system 或 all 模式）
    if mode in ('system', 'all'):
      # 导出品牌
      if Brand.query.count() > 0:
        sheet = workbook.create_sheet('品牌')
        sheet.append(['名称', '搜索地址'])
        for brand in Brand.query.all():
          sheet.append([brand.name, brand.search_url or ''])

      # 导出机务段
      if Depot.query.count() > 0:
        sheet = workbook.create_sheet('机务段')
        sheet.append(['名称'])
        for depot in Depot.query.all():
          sheet.append([depot.name])

      # 导出商家
      if Merchant.query.count() > 0:
        sheet = workbook.create_sheet('商家')
        sheet.append(['名称'])
        for merchant in Merchant.query.all():
          sheet.append([merchant.name])

      # 导出动力类型
      if PowerType.query.count() > 0:
        sheet = workbook.create_sheet('动力类型')
        sheet.append(['名称'])
        for pt in PowerType.query.all():
          sheet.append([pt.name])

      # 导出芯片接口
      if ChipInterface.query.count() > 0:
        sheet = workbook.create_sheet('芯片接口')
        sheet.append(['名称'])
        for ci in ChipInterface.query.all():
          sheet.append([ci.name])

      # 导出芯片型号
      if ChipModel.query.count() > 0:
        sheet = workbook.create_sheet('芯片型号')
        sheet.append(['名称'])
        for cm in ChipModel.query.all():
          sheet.append([cm.name])

      # 导出机车系列
      if LocomotiveSeries.query.count() > 0:
        sheet = workbook.create_sheet('机车系列')
        sheet.append(['名称'])
        for series in LocomotiveSeries.query.all():
          sheet.append([series.name])

      # 导出车厢系列
      if CarriageSeries.query.count() > 0:
        sheet = workbook.create_sheet('车厢系列')
        sheet.append(['名称'])
        for series in CarriageSeries.query.all():
          sheet.append([series.name])

      # 导出动车组系列
      if TrainsetSeries.query.count() > 0:
        sheet = workbook.create_sheet('动车组系列')
        sheet.append(['名称'])
        for series in TrainsetSeries.query.all():
          sheet.append([series.name])

      # 导出机车车型
      if LocomotiveModel.query.count() > 0:
        sheet = workbook.create_sheet('机车车型')
        sheet.append(['名称', '系列', '动力类型'])
        for model in LocomotiveModel.query.all():
          sheet.append([
            model.name,
            model.series.name if model.series else '',
            model.power_type.name if model.power_type else ''
          ])

      # 导出车厢车型
      if CarriageModel.query.count() > 0:
        sheet = workbook.create_sheet('车厢车型')
        sheet.append(['名称', '系列', '类型'])
        for model in CarriageModel.query.all():
          sheet.append([
            model.name,
            model.series.name if model.series else '',
            model.type or ''
          ])

      # 导出动车组车型
      if TrainsetModel.query.count() > 0:
        sheet = workbook.create_sheet('动车组车型')
        sheet.append(['名称', '系列', '动力类型'])
        for model in TrainsetModel.query.all():
          sheet.append([
            model.name,
            model.series.name if model.series else '',
            model.power_type.name if model.power_type else ''
          ])

    # 加粗所有工作表的第一行（标题行）
    from openpyxl.styles import Font
    bold_font = Font(bold=True)
    for sheet_name in workbook.sheetnames:
      sheet = workbook[sheet_name]
      for cell in sheet[1]:
        cell.font = bold_font

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    # 根据模式设置文件名
    mode_names = {'models': 'Models', 'system': 'System', 'all': 'All'}
    filename = f'TMM_{mode_names.get(mode, "Export")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{random.randint(1000, 9999)}.xlsx'

    logger.info(f"Excel export completed successfully, mode={mode}")
    return send_file(
      output,
      as_attachment=True,
      download_name=filename,
      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

  except Exception as e:
    logger.error(f"Excel export failed: {str(e)}", exc_info=True)
    return f"导出失败: {str(e)}", 500
