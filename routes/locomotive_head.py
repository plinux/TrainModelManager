"""
先头车模型路由 Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db, LocomotiveHead, TrainsetModel, Brand, Merchant
from utils.helpers import parse_purchase_date, safe_int, parse_boolean, api_success, api_error
from utils.price_calculator import calculate_price
from utils.file_sync import rename_model_folder, update_file_records_in_db
import logging

logger = logging.getLogger(__name__)
locomotive_head_bp = Blueprint('locomotive_head', __name__, url_prefix='')


def get_locomotive_head_form_data():
  """获取先头车表单所需的下拉框数据"""
  return {
    'trainset_models': TrainsetModel.query.all(),
    'brands': Brand.query.all(),
    'merchants': Merchant.query.all()
  }


def create_locomotive_head_from_form(form_data, is_json=False):
  """从表单数据创建先头车对象"""
  get_value = lambda key: form_data.get(key) if is_json else form_data.get(key)

  return LocomotiveHead(
    model_id=safe_int(get_value('model_id')),
    brand_id=safe_int(get_value('brand_id')),
    special_color=get_value('special_color'),
    scale=get_value('scale'),
    head_light=parse_boolean(get_value('head_light')) or False,
    interior_light=get_value('interior_light'),
    price=get_value('price'),
    total_price=calculate_price(get_value('price')),
    item_number=get_value('item_number'),
    product_url=get_value('product_url'),
    purchase_date=parse_purchase_date(get_value('purchase_date')),
    merchant_id=safe_int(get_value('merchant_id'))
  )


def update_locomotive_head_from_form(locomotive_head, form_data):
  """从表单数据更新先头车对象"""
  locomotive_head.model_id = safe_int(form_data.get('model_id'))
  locomotive_head.brand_id = safe_int(form_data.get('brand_id'))
  locomotive_head.special_color = form_data.get('special_color')
  locomotive_head.scale = form_data.get('scale')
  locomotive_head.head_light = parse_boolean(form_data.get('head_light')) or False
  locomotive_head.interior_light = form_data.get('interior_light')
  locomotive_head.price = form_data.get('price')
  locomotive_head.total_price = calculate_price(form_data.get('price'))
  locomotive_head.item_number = form_data.get('item_number')
  locomotive_head.product_url = form_data.get('product_url')
  locomotive_head.purchase_date = parse_purchase_date(form_data.get('purchase_date'))
  locomotive_head.merchant_id = safe_int(form_data.get('merchant_id'))


# API 路由
@locomotive_head_bp.route('/api/locomotive-head/edit/<int:id>', methods=['POST'])
def api_edit_locomotive_head(id):
  """AJAX 编辑先头车模型"""
  try:
    locomotive_head = db.get_or_404(LocomotiveHead, id)
    data = request.get_json()

    # 保存旧的品牌和货号（用于重命名文件夹）
    old_brand = db.session.get(Brand, locomotive_head.brand_id)
    old_brand_name = old_brand.name if old_brand else ''
    old_item_number = locomotive_head.item_number or ''

    # 更新模型
    update_locomotive_head_from_form(locomotive_head, data)

    # 获取新的品牌和货号
    new_brand = db.session.get(Brand, locomotive_head.brand_id)
    new_brand_name = new_brand.name if new_brand else ''
    new_item_number = locomotive_head.item_number or ''

    # 如果品牌或货号变化，重命名文件夹
    if old_brand_name != new_brand_name or old_item_number != new_item_number:
      rename_model_folder('locomotive_head', old_brand_name, old_item_number,
                          new_brand_name, new_item_number)
      update_file_records_in_db('locomotive_head', id, old_brand_name, old_item_number,
                                new_brand_name, new_item_number)

    db.session.commit()
    logger.info(f"Locomotive head updated: ID={id}")

    return jsonify(api_success('先头车模型更新成功'))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error updating locomotive head: {e}")
    return jsonify(api_error(str(e))), 500


@locomotive_head_bp.route('/api/locomotive-head/add', methods=['POST'])
def api_add_locomotive_head():
  """AJAX 添加先头车模型"""
  try:
    data = request.get_json()
    locomotive_head = create_locomotive_head_from_form(data, is_json=True)

    db.session.add(locomotive_head)
    db.session.commit()
    logger.info(f"Locomotive head added: ID={locomotive_head.id}")

    return jsonify(api_success('先头车模型添加成功', data={'id': locomotive_head.id}))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error adding locomotive head: {e}")
    return jsonify(api_error(str(e))), 500


# 页面路由
@locomotive_head_bp.route('/locomotive-head', methods=['GET', 'POST'])
def locomotive_head():
  """先头车模型列表和添加"""
  if request.method == 'POST':
    try:
      locomotive_head = create_locomotive_head_from_form(request.form)
      db.session.add(locomotive_head)
      db.session.commit()
      return redirect(url_for('locomotive_head.locomotive_head'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error adding locomotive head: {e}")
      form_data = get_locomotive_head_form_data()
      form_data['locomotive_heads'] = LocomotiveHead.query.all()
      return render_template('locomotive_head.html', **form_data)

  form_data = get_locomotive_head_form_data()
  form_data['locomotive_heads'] = LocomotiveHead.query.all()
  return render_template('locomotive_head.html', **form_data)


@locomotive_head_bp.route('/locomotive-head/delete/<int:id>', methods=['POST'])
def delete_locomotive_head(id):
  """删除先头车模型"""
  try:
    locomotive_head = db.get_or_404(LocomotiveHead, id)
    logger.info(f"Deleting locomotive head: {locomotive_head}")
    db.session.delete(locomotive_head)
    db.session.commit()
    logger.info(f"Locomotive head deleted: ID={id}")
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error deleting locomotive head: {e}")

  return redirect(url_for('locomotive_head.locomotive_head'))


@locomotive_head_bp.route('/locomotive-head/edit/<int:id>', methods=['GET', 'POST'])
def edit_locomotive_head(id):
  """编辑先头车模型"""
  locomotive_head = db.get_or_404(LocomotiveHead, id)
  form_data = get_locomotive_head_form_data()

  if request.method == 'POST':
    try:
      update_locomotive_head_from_form(locomotive_head, request.form)
      db.session.commit()
      logger.info(f"Locomotive head updated: ID={id}")
      return redirect(url_for('locomotive_head.locomotive_head'))
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error updating locomotive head: {e}")
      form_data['locomotive_head'] = locomotive_head
      return render_template('locomotive_head_edit.html', **form_data)

  form_data['locomotive_head'] = locomotive_head
  return render_template('locomotive_head_edit.html', **form_data)
