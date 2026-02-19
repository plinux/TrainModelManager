"""
动车组模型路由 Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, Trainset, TrainsetModel, TrainsetSeries, PowerType, Brand, Depot, ChipInterface, ChipModel, Merchant
from utils.helpers import parse_purchase_date, safe_int, validate_unique, parse_boolean, api_success, api_error
from utils.validators import validate_trainset_number, validate_decoder_number
from utils.price_calculator import calculate_price
from utils.file_sync import rename_model_folder, update_file_records_in_db
import logging

logger = logging.getLogger(__name__)
trainset_bp = Blueprint('trainset', __name__, url_prefix='')


def get_trainset_form_data():
  """获取动车组表单所需的下拉框数据"""
  return {
    'trainset_models': TrainsetModel.query.all(),
    'trainset_series': TrainsetSeries.query.all(),
    'power_types': PowerType.query.all(),
    'brands': Brand.query.all(),
    'depots': Depot.query.all(),
    'chip_interfaces': ChipInterface.query.all(),
    'chip_models': ChipModel.query.all(),
    'merchants': Merchant.query.all()
  }


def validate_trainset_data(trainset_number, decoder_number, scale, exclude_id=None):
  """验证动车组数据，返回错误列表"""
  errors = []

  # 格式验证
  if trainset_number and not validate_trainset_number(trainset_number):
    errors.append({'field': 'trainset_number', 'message': '动车号格式错误：应为3-12位数字，允许前导0'})
  if decoder_number and not validate_decoder_number(decoder_number):
    errors.append({'field': 'decoder_number', 'message': '编号格式错误：应为1-4位数字，无前导0'})

  # 唯一性验证
  if trainset_number and not validate_unique(Trainset, 'trainset_number', trainset_number, scale, exclude_id):
    errors.append({'field': 'trainset_number', 'message': f'动车号 {trainset_number} 在 {scale} 比例下已存在'})
  if decoder_number and not validate_unique(Trainset, 'decoder_number', decoder_number, scale, exclude_id):
    errors.append({'field': 'decoder_number', 'message': f'编号 {decoder_number} 在 {scale} 比例下已存在'})

  return errors


def create_trainset_from_form(form_data, is_json=False):
  """从表单数据创建动车组对象"""
  get_value = lambda key: form_data.get(key) if is_json else form_data.get(key)
  get_formation = lambda: safe_int(get_value('formation')) if get_value('formation') else None

  return Trainset(
    model_id=safe_int(get_value('model_id')),
    series_id=safe_int(get_value('series_id')),
    power_type_id=safe_int(get_value('power_type_id')),
    brand_id=safe_int(get_value('brand_id')),
    depot_id=safe_int(get_value('depot_id')),
    plaque=get_value('plaque'),
    color=get_value('color'),
    scale=get_value('scale'),
    formation=get_formation(),
    trainset_number=get_value('trainset_number'),
    decoder_number=get_value('decoder_number'),
    head_light=parse_boolean(get_value('head_light')) or False,
    interior_light=get_value('interior_light'),
    chip_interface_id=safe_int(get_value('chip_interface_id')),
    chip_model_id=safe_int(get_value('chip_model_id')),
    price=get_value('price'),
    total_price=calculate_price(get_value('price')),
    item_number=get_value('item_number'),
    product_url=get_value('product_url'),
    purchase_date=parse_purchase_date(get_value('purchase_date')),
    merchant_id=safe_int(get_value('merchant_id'))
  )


def update_trainset_from_form(trainset, form_data):
  """从表单数据更新动车组对象"""
  trainset.model_id = safe_int(form_data.get('model_id'))
  trainset.series_id = safe_int(form_data.get('series_id'))
  trainset.power_type_id = safe_int(form_data.get('power_type_id'))
  trainset.brand_id = safe_int(form_data.get('brand_id'))
  trainset.depot_id = safe_int(form_data.get('depot_id'))
  trainset.plaque = form_data.get('plaque')
  trainset.color = form_data.get('color')
  trainset.scale = form_data.get('scale')
  trainset.formation = safe_int(form_data.get('formation')) if form_data.get('formation') else None
  trainset.trainset_number = form_data.get('trainset_number')
  trainset.decoder_number = form_data.get('decoder_number')
  trainset.head_light = parse_boolean(form_data.get('head_light')) or False
  trainset.interior_light = form_data.get('interior_light')
  trainset.chip_interface_id = safe_int(form_data.get('chip_interface_id'))
  trainset.chip_model_id = safe_int(form_data.get('chip_model_id'))
  trainset.price = form_data.get('price')
  trainset.total_price = calculate_price(form_data.get('price'))
  trainset.item_number = form_data.get('item_number')
  trainset.product_url = form_data.get('product_url')
  trainset.purchase_date = parse_purchase_date(form_data.get('purchase_date'))
  trainset.merchant_id = safe_int(form_data.get('merchant_id'))


# API 路由
@trainset_bp.route('/api/trainset/edit/<int:id>', methods=['POST'])
def api_edit_trainset(id):
  """AJAX 编辑动车组模型"""
  try:
    trainset = Trainset.query.get_or_404(id)
    data = request.get_json()
    scale = data.get('scale')
    trainset_number = data.get('trainset_number')
    decoder_number = data.get('decoder_number')

    errors = validate_trainset_data(trainset_number, decoder_number, scale, exclude_id=id)
    if errors:
      return jsonify(api_error('验证失败', errors=errors)), 400

    # 保存旧的品牌和货号（用于重命名文件夹）
    old_brand = Brand.query.get(trainset.brand_id)
    old_brand_name = old_brand.name if old_brand else ''
    old_item_number = trainset.item_number or ''

    # 更新模型
    update_trainset_from_form(trainset, data)

    # 获取新的品牌和货号
    new_brand = Brand.query.get(trainset.brand_id)
    new_brand_name = new_brand.name if new_brand else ''
    new_item_number = trainset.item_number or ''

    # 如果品牌或货号变化，重命名文件夹
    if old_brand_name != new_brand_name or old_item_number != new_item_number:
      rename_model_folder('trainset', old_brand_name, old_item_number,
                          new_brand_name, new_item_number)
      update_file_records_in_db('trainset', id, old_brand_name, old_item_number,
                                new_brand_name, new_item_number)

    db.session.commit()
    logger.info(f"Trainset updated: ID={id}")

    return jsonify(api_success('动车组模型更新成功'))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error updating trainset: {e}")
    return jsonify(api_error(str(e))), 500


@trainset_bp.route('/api/trainset/add', methods=['POST'])
def api_add_trainset():
  """AJAX 添加动车组模型"""
  try:
    data = request.get_json()
    scale = data.get('scale')
    trainset_number = data.get('trainset_number')
    decoder_number = data.get('decoder_number')

    errors = validate_trainset_data(trainset_number, decoder_number, scale)
    if errors:
      return jsonify(api_error('验证失败', errors=errors)), 400

    trainset = create_trainset_from_form(data, is_json=True)

    db.session.add(trainset);
    db.session.commit()
    logger.info(f"Trainset added: ID={trainset.id}")

    return jsonify(api_success('动车组模型添加成功', data={'id': trainset.id}))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error adding trainset: {e}")
    return jsonify(api_error(str(e))), 500


# 页面路由
@trainset_bp.route('/trainset', methods=['GET', 'POST'])
def trainset():
  """动车组模型列表和添加"""
  if request.method == 'POST':
    scale = request.form.get('scale')
    trainset_number = request.form.get('trainset_number')
    decoder_number = request.form.get('decoder_number')

    errors = validate_trainset_data(trainset_number, decoder_number, scale)
    if errors:
      form_data = get_trainset_form_data()
      form_data['trainsets'] = Trainset.query.all()
      form_data['errors'] = [e['message'] for e in errors]
      return render_template('trainset.html', **form_data)

    try:
      trainset = create_trainset_from_form(request.form)
      db.session.add(trainset)
      db.session.commit()
      logger.info(f"Trainset added: ID={trainset.id}")
      return redirect(url_for('trainset.trainset'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error adding trainset: {e}")
      form_data = get_trainset_form_data()
      form_data['trainsets'] = Trainset.query.all()
      form_data['errors'] = [str(e)]
      return render_template('trainset.html', **form_data)

  form_data = get_trainset_form_data()
  form_data['trainsets'] = Trainset.query.all()
  form_data['errors'] = []
  return render_template('trainset.html', **form_data)


@trainset_bp.route('/trainset/delete/<int:id>', methods=['POST'])
def delete_trainset(id):
  """删除动车组模型"""
  try:
    trainset = Trainset.query.get_or_404(id)
    logger.info(f"Deleting trainset: {trainset}")
    db.session.delete(trainset)
    db.session.commit()
    logger.info(f"Trainset deleted: ID={id}")
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error deleting trainset: {e}")

  return redirect(url_for('trainset.trainset'))


@trainset_bp.route('/trainset/edit/<int:id>', methods=['GET', 'POST'])
def edit_trainset(id):
  """编辑动车组模型"""
  trainset = Trainset.query.get_or_404(id)
  form_data = get_trainset_form_data()

  if request.method == 'POST':
    scale = request.form.get('scale')
    trainset_number = request.form.get('trainset_number')
    decoder_number = request.form.get('decoder_number')

    errors = validate_trainset_data(trainset_number, decoder_number, scale, exclude_id=id)
    if errors:
      form_data['trainset'] = trainset
      form_data['errors'] = [e['message'] for e in errors]
      return render_template('trainset_edit.html', **form_data)

    try:
      update_trainset_from_form(trainset, request.form)
      db.session.commit()
      logger.info(f"Trainset updated: ID={id}")
      return redirect(url_for('trainset.trainset'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error updating trainset: {e}")
      form_data['trainset'] = trainset
      form_data['errors'] = [str(e)]
      return render_template('trainset_edit.html', **form_data)

  form_data['trainset'] = trainset
  form_data['errors'] = []
  return render_template('trainset_edit.html', **form_data)
