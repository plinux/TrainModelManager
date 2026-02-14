"""
机车模型路由 Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, Locomotive, LocomotiveModel, LocomotiveSeries, PowerType, Brand, Depot, ChipInterface, ChipModel, Merchant
from utils.helpers import parse_purchase_date, safe_int, validate_unique, api_success, api_error
from utils.validators import validate_locomotive_number, validate_decoder_number
from utils.price_calculator import calculate_price
import logging

logger = logging.getLogger(__name__)
locomotive_bp = Blueprint('locomotive', __name__, url_prefix='')


def get_locomotive_form_data():
  """获取机车表单所需的下拉框数据"""
  return {
    'locomotive_models': LocomotiveModel.query.all(),
    'locomotive_series': LocomotiveSeries.query.all(),
    'power_types': PowerType.query.all(),
    'brands': Brand.query.all(),
    'depots': Depot.query.all(),
    'chip_interfaces': ChipInterface.query.all(),
    'chip_models': ChipModel.query.all(),
    'merchants': Merchant.query.all()
  }


def validate_locomotive_data(locomotive_number, decoder_number, scale, exclude_id=None):
  """验证机车数据，返回错误列表"""
  errors = []

  # 格式验证
  if locomotive_number and not validate_locomotive_number(locomotive_number):
    errors.append({'field': 'locomotive_number', 'message': '机车号格式错误：应为4-12位数字，允许前导0'})
  if decoder_number and not validate_decoder_number(decoder_number):
    errors.append({'field': 'decoder_number', 'message': '编号格式错误：应为1-4位数字，无前导0'})

  # 唯一性验证
  if locomotive_number and not validate_unique(Locomotive, 'locomotive_number', locomotive_number, scale, exclude_id):
    errors.append({'field': 'locomotive_number', 'message': f'机车号 {locomotive_number} 在 {scale} 比例下已存在'})
  if decoder_number and not validate_unique(Locomotive, 'decoder_number', decoder_number, scale, exclude_id):
    errors.append({'field': 'decoder_number', 'message': f'编号 {decoder_number} 在 {scale} 比例下已存在'})

  return errors


def create_locomotive_from_form(form_data, is_json=False):
  """从表单数据创建机车对象"""
  get_value = lambda key: form_data.get(key) if is_json else form_data.get(key)

  return Locomotive(
    model_id=safe_int(get_value('model_id')),
    series_id=safe_int(get_value('series_id')),
    power_type_id=safe_int(get_value('power_type_id')),
    brand_id=safe_int(get_value('brand_id')),
    depot_id=safe_int(get_value('depot_id')),
    plaque=get_value('plaque'),
    color=get_value('color'),
    scale=get_value('scale'),
    locomotive_number=get_value('locomotive_number'),
    decoder_number=get_value('decoder_number'),
    chip_interface_id=safe_int(get_value('chip_interface_id')),
    chip_model_id=safe_int(get_value('chip_model_id')),
    price=get_value('price'),
    total_price=calculate_price(get_value('price')),
    item_number=get_value('item_number'),
    purchase_date=parse_purchase_date(get_value('purchase_date')),
    merchant_id=safe_int(get_value('merchant_id'))
  )


def update_locomotive_from_form(locomotive, form_data):
  """从表单数据更新机车对象"""
  locomotive.model_id = safe_int(form_data.get('model_id'))
  locomotive.series_id = safe_int(form_data.get('series_id'))
  locomotive.power_type_id = safe_int(form_data.get('power_type_id'))
  locomotive.brand_id = safe_int(form_data.get('brand_id'))
  locomotive.depot_id = safe_int(form_data.get('depot_id'))
  locomotive.plaque = form_data.get('plaque')
  locomotive.color = form_data.get('color')
  locomotive.scale = form_data.get('scale')
  locomotive.locomotive_number = form_data.get('locomotive_number')
  locomotive.decoder_number = form_data.get('decoder_number')
  locomotive.chip_interface_id = safe_int(form_data.get('chip_interface_id'))
  locomotive.chip_model_id = safe_int(form_data.get('chip_model_id'))
  locomotive.price = form_data.get('price')
  locomotive.total_price = calculate_price(form_data.get('price'))
  locomotive.item_number = form_data.get('item_number')
  locomotive.purchase_date = parse_purchase_date(form_data.get('purchase_date'))
  locomotive.merchant_id = safe_int(form_data.get('merchant_id'))


# API 路由
@locomotive_bp.route('/api/locomotive/add', methods=['POST'])
def api_add_locomotive():
  """AJAX 添加机车模型"""
  try:
    data = request.get_json()
    scale = data.get('scale')
    locomotive_number = data.get('locomotive_number')
    decoder_number = data.get('decoder_number')

    errors = validate_locomotive_data(locomotive_number, decoder_number, scale)
    if errors:
      return jsonify(api_error('验证失败', errors=errors)), 400

    locomotive = create_locomotive_from_form(data, is_json=True)

    db.session.add(locomotive)
    db.session.commit()
    logger.info(f"Locomotive added: ID={locomotive.id}")

    return jsonify(api_success('机车模型添加成功'))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error adding locomotive: {e}")
    return jsonify(api_error(str(e))), 500


# 页面路由
@locomotive_bp.route('/locomotive', methods=['GET', 'POST'])
def locomotive():
  """机车模型列表和添加"""
  if request.method == 'POST':
    scale = request.form.get('scale')
    locomotive_number = request.form.get('locomotive_number')
    decoder_number = request.form.get('decoder_number')

    errors = validate_locomotive_data(locomotive_number, decoder_number, scale)
    if errors:
      form_data = get_locomotive_form_data()
      form_data['locomotives'] = Locomotive.query.all()
      form_data['errors'] = [e['message'] for e in errors]
      return render_template('locomotive.html', **form_data)

    try:
      locomotive = create_locomotive_from_form(request.form)
      db.session.add(locomotive)
      db.session.commit()
      logger.info(f"Locomotive added: ID={locomotive.id}")
      return redirect(url_for('locomotive.locomotive'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error adding locomotive: {e}")
      form_data = get_locomotive_form_data()
      form_data['locomotives'] = Locomotive.query.all()
      form_data['errors'] = [str(e)]
      return render_template('locomotive.html', **form_data)

  form_data = get_locomotive_form_data()
  form_data['locomotives'] = Locomotive.query.all()
  form_data['errors'] = []
  return render_template('locomotive.html', **form_data)


@locomotive_bp.route('/locomotive/delete/<int:id>', methods=['POST'])
def delete_locomotive(id):
  """删除机车模型"""
  try:
    locomotive = Locomotive.query.get_or_404(id)
    logger.info(f"Deleting locomotive: {locomotive}")
    db.session.delete(locomotive)
    db.session.commit()
    logger.info(f"Locomotive deleted: ID={id}")
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error deleting locomotive: {e}")

  return redirect(url_for('locomotive.locomotive'))


@locomotive_bp.route('/locomotive/edit/<int:id>', methods=['GET', 'POST'])
def edit_locomotive(id):
  """编辑机车模型"""
  locomotive = Locomotive.query.get_or_404(id)
  form_data = get_locomotive_form_data()

  if request.method == 'POST':
    scale = request.form.get('scale')
    locomotive_number = request.form.get('locomotive_number')
    decoder_number = request.form.get('decoder_number')

    errors = validate_locomotive_data(locomotive_number, decoder_number, scale, exclude_id=id)
    if errors:
      form_data['locomotive'] = locomotive
      form_data['errors'] = [e['message'] for e in errors]
      return render_template('locomotive_edit.html', **form_data)

    try:
      update_locomotive_from_form(locomotive, request.form)
      db.session.commit()
      logger.info(f"Locomotive updated: ID={id}")
      return redirect(url_for('locomotive.locomotive'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error updating locomotive: {e}")
      form_data['locomotive'] = locomotive
      form_data['errors'] = [str(e)]
      return render_template('locomotive_edit.html', **form_data)

  form_data['locomotive'] = locomotive
  form_data['errors'] = []
  return render_template('locomotive_edit.html', **form_data)
