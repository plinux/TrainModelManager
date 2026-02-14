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


@api_bp.route('/api/import/excel', methods=['POST'])
def import_from_excel():
  """从 Excel 文件导入数据"""
  try:
    if 'file' not in request.files:
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
      return jsonify({'success': False, 'error': '未选择文件'}), 400

    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
      return jsonify({'success': False, 'error': '文件格式错误，请上传Excel文件'}), 400

    workbook = openpyxl.load_workbook(file)
    summary = {}
    errors = []

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

      if not data:
        continue

      try:
        if sheet_name == '机车':
          count = import_locomotive_data(data)
          summary['机车模型'] = count
        elif sheet_name == '车厢':
          count = import_carriage_data(data)
          summary['车厢模型'] = count
        elif sheet_name == '动车组':
          count = import_trainset_data(data)
          summary['动车组模型'] = count
        elif sheet_name == '先头车':
          count = import_locomotive_head_data(data)
          summary['先头车模型'] = count
        else:
          logger.warning(f"Unknown sheet name: {sheet_name}")
      except Exception as e:
        errors.append(f"{sheet_name}: {str(e)}")
        logger.error(f"Error importing sheet {sheet_name}: {str(e)}", exc_info=True)

    if errors:
      return jsonify({'success': False, 'error': '部分导入失败: ' + '; '.join(errors)}), 400

    logger.info(f"Excel import completed: {summary}")
    return jsonify({'success': True, 'summary': summary})

  except Exception as e:
    db.session.rollback()
    logger.error(f"Excel import failed: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': str(e)}), 500


def import_locomotive_data(data):
  """导入机车模型数据"""
  count = 0
  for row in data:
    series_id = find_id_by_name(LocomotiveSeries, row.get('系列'))
    power_type_id = find_id_by_name(PowerType, row.get('动力类型'))
    model_id = find_id_by_name(LocomotiveModel, row.get('车型'),
      lambda q: q.filter_by(name=row.get('车型'), series_id=series_id, power_type_id=power_type_id).first())

    locomotive = Locomotive(
      series_id=series_id,
      power_type_id=power_type_id,
      model_id=model_id,
      brand_id=find_id_by_name(Brand, row.get('品牌')),
      depot_id=find_id_by_name(Depot, row.get('机务段')),
      plaque=row.get('挂牌'),
      color=row.get('颜色'),
      scale=row.get('比例'),
      locomotive_number=row.get('机车号'),
      decoder_number=row.get('编号'),
      chip_interface_id=find_id_by_name(ChipInterface, row.get('芯片接口')),
      chip_model_id=find_id_by_name(ChipModel, row.get('芯片型号')),
      price=row.get('价格'),
      total_price=calculate_price(row.get('价格')),
      item_number=row.get('货号'),
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(locomotive)
    count += 1

  db.session.commit()
  return count


def import_carriage_data(data):
  """导入车厢模型数据"""
  count = 0
  for row in data:
    carriage_set = CarriageSet(
      brand_id=find_id_by_name(Brand, row.get('品牌')),
      series_id=find_id_by_name(CarriageSeries, row.get('系列')),
      depot_id=find_id_by_name(Depot, row.get('车辆段')),
      train_number=row.get('车次'),
      plaque=row.get('挂牌'),
      item_number=row.get('货号'),
      scale=row.get('比例'),
      total_price=safe_float(row.get('总价')),
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(carriage_set)
    count += 1

  db.session.commit()
  return count


def import_trainset_data(data):
  """导入动车组模型数据"""
  count = 0
  for row in data:
    series_id = find_id_by_name(TrainsetSeries, row.get('系列'))
    power_type_id = find_id_by_name(PowerType, row.get('动力类型'))
    model_id = find_id_by_name(TrainsetModel, row.get('车型'),
      lambda q: q.filter_by(name=row.get('车型'), series_id=series_id, power_type_id=power_type_id).first())

    trainset = Trainset(
      series_id=series_id,
      power_type_id=power_type_id,
      model_id=model_id,
      brand_id=find_id_by_name(Brand, row.get('品牌')),
      depot_id=find_id_by_name(Depot, row.get('动车段')),
      plaque=row.get('挂牌'),
      color=row.get('颜色'),
      scale=row.get('比例'),
      formation=safe_int(row.get('编组')),
      trainset_number=row.get('动车号'),
      decoder_number=row.get('编号'),
      head_light=parse_boolean(row.get('头车灯')) or False,
      interior_light=row.get('室内灯'),
      chip_interface_id=find_id_by_name(ChipInterface, row.get('芯片接口')),
      chip_model_id=find_id_by_name(ChipModel, row.get('芯片型号')),
      price=row.get('价格'),
      total_price=calculate_price(row.get('价格')),
      item_number=row.get('货号'),
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(trainset)
    count += 1

  db.session.commit()
  return count


def import_locomotive_head_data(data):
  """导入先头车模型数据"""
  count = 0
  for row in data:
    locomotive_head = LocomotiveHead(
      model_id=find_id_by_name(TrainsetModel, row.get('车型')),
      brand_id=find_id_by_name(Brand, row.get('品牌')),
      depot_id=find_id_by_name(Depot, row.get('动车段')),
      special_color=row.get('特涂'),
      scale=row.get('比例'),
      head_light=parse_boolean(row.get('头车灯')) or False,
      interior_light=row.get('室内灯'),
      price=row.get('价格'),
      total_price=calculate_price(row.get('价格')),
      item_number=row.get('货号'),
      purchase_date=parse_purchase_date(row.get('购买日期')),
      merchant_id=find_id_by_name(Merchant, row.get('购买商家'))
    )
    db.session.add(locomotive_head)
    count += 1

  db.session.commit()
  return count


@api_bp.route('/api/export/excel')
def export_to_excel():
  """导出数据到Excel"""
  try:
    has_data = (
      Locomotive.query.count() > 0 or
      CarriageSet.query.count() > 0 or
      Trainset.query.count() > 0 or
      LocomotiveHead.query.count() > 0
    )

    if not has_data:
      return jsonify({'success': False, 'error': '当前没有可导出的数据，请先添加模型后再导出'}), 400

    workbook = openpyxl.Workbook()

    if 'Sheet' in workbook.sheetnames:
      workbook.remove(workbook['Sheet'])

    # 导出机车模型
    if Locomotive.query.count() > 0:
      sheet = workbook.create_sheet('机车')
      headers = ['系列', '动力类型', '车型', '品牌', '机务段', '挂牌', '颜色', '比例', '机车号', '编号',
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

    # 导出车厢模型
    if CarriageSet.query.count() > 0:
      sheet = workbook.create_sheet('车厢')
      headers = ['品牌', '系列', '车辆段', '车次', '挂牌', '货号', '比例', '车型', '车辆号', '颜色', '灯光', '总价', '购买日期', '购买商家']
      sheet.append(headers)

      row_offset = 2
      for carriage_set in CarriageSet.query.all():
        items = carriage_set.items
        if not items:
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
        else:
          set_row_start = row_offset
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
            row_offset += 1

          set_row_end = row_offset - 1
          merge_columns = [1, 2, 3, 4, 5, 6, 7, 12, 13, 14]
          for col in merge_columns:
            if set_row_start != set_row_end:
              sheet.merge_cells(start_row=set_row_start, start_column=col,
                          end_row=set_row_end, end_column=col)

    # 导出动车组模型
    if Trainset.query.count() > 0:
      sheet = workbook.create_sheet('动车组')
      headers = ['系列', '动力类型', '车型', '品牌', '动车段', '挂牌', '颜色', '比例', '编组', '动车号', '编号',
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
      headers = ['车型', '品牌', '动车段', '特涂', '比例', '头车灯', '室内灯', '价格', '总价', '货号', '购买日期', '购买商家']
      sheet.append(headers)

      for head in LocomotiveHead.query.all():
        sheet.append([
          head.model.name if head.model else '',
          head.brand.name if head.brand else '',
          head.depot.name if head.depot else '',
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

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    filename = f'火车模型数据导出_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    logger.info("Excel export completed successfully")
    return send_file(
      output,
      as_attachment=True,
      download_name=filename,
      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

  except Exception as e:
    logger.error(f"Excel export failed: {str(e)}", exc_info=True)
    return f"导出失败: {str(e)}", 500
