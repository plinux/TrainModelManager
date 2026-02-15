"""
车厢模型路由 Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, CarriageSet, CarriageItem, CarriageModel, CarriageSeries, Brand, Depot, Merchant
from utils.helpers import parse_purchase_date, safe_int, safe_float, api_success, api_error
from utils.validators import validate_car_number
import logging

logger = logging.getLogger(__name__)
carriage_bp = Blueprint('carriage', __name__, url_prefix='')


def get_carriage_form_data():
  """获取车厢表单所需的下拉框数据"""
  return {
    'carriage_models': CarriageModel.query.all(),
    'carriage_series': CarriageSeries.query.all(),
    'brands': Brand.query.all(),
    'depots': Depot.query.all(),
    'merchants': Merchant.query.all()
  }


def validate_carriage_items(form_data, is_json=False):
  """验证车厢项数据，返回错误列表"""
  errors = []
  get_value = lambda key: form_data.get(key) if is_json else form_data.get(key)

  for i in range(10):
    model_key = f'model_{i}'
    car_number_key = f'car_number_{i}'

    if get_value(model_key):
      car_number = get_value(car_number_key)
      if car_number and not validate_car_number(car_number):
        errors.append({'field': car_number_key, 'message': f'车辆号 {car_number} 格式错误：应为1-20位字母、数字或连字符'})

  return errors


def create_carriage_set_from_form(form_data, is_json=False):
  """从表单数据创建车厢套装对象"""
  get_value = lambda key: form_data.get(key) if is_json else form_data.get(key)

  return CarriageSet(
    brand_id=safe_int(get_value('brand_id')),
    series_id=safe_int(get_value('series_id')),
    depot_id=safe_int(get_value('depot_id')),
    train_number=get_value('train_number'),
    plaque=get_value('plaque'),
    item_number=get_value('item_number'),
    scale=get_value('scale'),
    total_price=safe_float(get_value('total_price')),
    purchase_date=parse_purchase_date(get_value('purchase_date')),
    merchant_id=safe_int(get_value('merchant_id'))
  )


def create_carriage_items(carriage_set_id, form_data, is_json=False):
  """从表单数据创建车厢项列表"""
  get_value = lambda key: form_data.get(key) if is_json else form_data.get(key)
  items = []

  for i in range(10):
    model_key = f'model_{i}'
    if get_value(model_key):
      item = CarriageItem(
        set_id=carriage_set_id,
        model_id=safe_int(get_value(model_key)),
        car_number=get_value(f'car_number_{i}'),
        color=get_value(f'color_{i}'),
        lighting=get_value(f'lighting_{i}')
      )
      items.append(item)

  return items


# API 路由
@carriage_bp.route('/api/carriage/add', methods=['POST'])
def api_add_carriage():
  """AJAX 添加车厢模型"""
  try:
    data = request.get_json()

    errors = validate_carriage_items(data, is_json=True)
    if errors:
      return jsonify(api_error('验证失败', errors=errors)), 400

    carriage_set = create_carriage_set_from_form(data, is_json=True)
    db.session.add(carriage_set)
    db.session.flush()  # 获取 ID

    items = create_carriage_items(carriage_set.id, data, is_json=True)
    for item in items:
      db.session.add(item)

    db.session.commit()
    logger.info(f"Carriage set added: ID={carriage_set.id}")

    return jsonify(api_success('车厢套装添加成功'))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error adding carriage: {e}")
    return jsonify(api_error(str(e))), 500


# 页面路由
@carriage_bp.route('/carriage', methods=['GET', 'POST'])
def carriage():
  """车厢模型列表和添加"""
  if request.method == 'POST':
    errors = validate_carriage_items(request.form)
    if errors:
      form_data = get_carriage_form_data()
      form_data['carriage_sets'] = CarriageSet.query.all()
      form_data['errors'] = [e['message'] for e in errors]
      return render_template('carriage.html', **form_data)

    try:
      carriage_set = create_carriage_set_from_form(request.form)
      db.session.add(carriage_set)
      db.session.commit()
      db.session.refresh(carriage_set)

      items = create_carriage_items(carriage_set.id, request.form)
      for item in items:
        db.session.add(item)

      db.session.commit()
      return redirect(url_for('carriage.carriage'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error adding carriage: {e}")
      form_data = get_carriage_form_data()
      form_data['carriage_sets'] = CarriageSet.query.all()
      form_data['errors'] = [str(e)]
      return render_template('carriage.html', **form_data)

  form_data = get_carriage_form_data()
  form_data['carriage_sets'] = CarriageSet.query.all()
  form_data['errors'] = []
  return render_template('carriage.html', **form_data)


@carriage_bp.route('/carriage/delete/<int:id>', methods=['POST'])
def delete_carriage(id):
  """删除车厢套装"""
  try:
    carriage_set = CarriageSet.query.get_or_404(id)
    logger.info(f"Deleting carriage set: {carriage_set}")
    db.session.delete(carriage_set)
    db.session.commit()
    logger.info(f"Carriage set deleted: ID={id}")
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error deleting carriage: {e}")

  return redirect(url_for('carriage.carriage'))


@carriage_bp.route('/carriage/edit/<int:id>', methods=['GET', 'POST'])
def edit_carriage(id):
  """编辑车厢套装"""
  carriage_set = CarriageSet.query.get_or_404(id)
  form_data = get_carriage_form_data()

  if request.method == 'POST':
    errors = validate_carriage_items(request.form)
    if errors:
      form_data['carriage_set'] = carriage_set
      form_data['errors'] = [e['message'] for e in errors]
      return render_template('carriage_edit.html', **form_data)

    try:
      # 更新套装信息
      carriage_set.brand_id = safe_int(request.form.get('brand_id'))
      carriage_set.series_id = safe_int(request.form.get('series_id'))
      carriage_set.depot_id = safe_int(request.form.get('depot_id'))
      carriage_set.train_number = request.form.get('train_number')
      carriage_set.plaque = request.form.get('plaque')
      carriage_set.item_number = request.form.get('item_number')
      carriage_set.scale = request.form.get('scale')
      carriage_set.total_price = safe_float(request.form.get('total_price'))
      carriage_set.purchase_date = parse_purchase_date(request.form.get('purchase_date'))
      carriage_set.merchant_id = safe_int(request.form.get('merchant_id'))

      # 删除旧的车厢项并添加新的
      CarriageItem.query.filter_by(set_id=id).delete()
      items = create_carriage_items(carriage_set.id, request.form)
      for item in items:
        db.session.add(item)

      db.session.commit()
      logger.info(f"Carriage set updated: ID={id}")
      return redirect(url_for('carriage.carriage'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error updating carriage: {e}")
      form_data['carriage_set'] = carriage_set
      form_data['errors'] = [str(e)]
      return render_template('carriage_edit.html', **form_data)

  form_data['carriage_set'] = carriage_set
  form_data['errors'] = []
  return render_template('carriage_edit.html', **form_data)
