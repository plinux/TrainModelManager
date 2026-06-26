"""
信息维护路由 Blueprint
使用工厂函数简化 CRUD 操作
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db
from models import (
  PowerType, Brand, Merchant, Depot, ChipInterface, ChipModel,
  LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel,
  TrainsetSeries, TrainsetModel,
  LightBrand, LightModel, LightModelCarriage, LightModelTrainset,
  LightModelBrandApplicability,
  CarriageItem, Trainset, LocomotiveHead
)
from utils.helpers import safe_int, api_success, api_error, generate_brand_abbreviation
import html
import logging

logger = logging.getLogger(__name__)
options_bp = Blueprint('options', __name__, url_prefix='')


def check_light_model_cascade(item):
  """检查灯型号是否被实际模型引用"""
  if CarriageItem.query.filter_by(light_model_id=item.id).first():
    return "该灯型号正在被车厢模型使用，无法删除！"
  if Trainset.query.filter_by(light_model_id=item.id).first():
    return "该灯型号正在被动车组模型使用，无法删除！"
  if LocomotiveHead.query.filter_by(light_model_id=item.id).first():
    return "该灯型号正在被先头车模型使用，无法删除！"
  return None


def _save_chip_model_interfaces(item, form):
  """保存芯片型号与接口的多对多关联"""
  interface_ids = [v for x in form.getlist('interface_ids') if (v := safe_int(x)) is not None]
  # 清除旧关联，重新设置
  item.interfaces = []
  for iface_id in interface_ids:
    iface = db.session.get(ChipInterface, iface_id)
    if iface:
      item.interfaces.append(iface)


def save_light_model_applicabilities(item, form):
  """保存灯型号的适用车型关联

  两种模式：
  - 品牌级：只勾选品牌，不勾选车型 → 存入 LightModelBrandApplicability（适用该品牌所有车型，含未来新增）
  - 车型级：同时勾选品牌和具体车型 → 存入 LightModelCarriage/Trainset（笛卡尔积）
  """
  brand_ids = [v for x in form.getlist('applicable_brands') if (v := safe_int(x)) is not None]
  carriage_model_ids = [v for x in form.getlist('carriage_models') if (v := safe_int(x)) is not None]
  trainset_model_ids = [v for x in form.getlist('trainset_models') if (v := safe_int(x)) is not None]

  # 清除旧数据（三种表都清）
  LightModelCarriage.query.filter_by(light_model_id=item.id).delete()
  LightModelTrainset.query.filter_by(light_model_id=item.id).delete()
  LightModelBrandApplicability.query.filter_by(light_model_id=item.id).delete()

  if not brand_ids:
    return

  has_carriage = len(carriage_model_ids) > 0
  has_trainset = len(trainset_model_ids) > 0

  if not has_carriage and not has_trainset:
    # 纯品牌级：适用于该品牌所有车型
    for brand_id in brand_ids:
      db.session.add(LightModelBrandApplicability(
        light_model_id=item.id,
        brand_id=brand_id,
        vehicle_type='all'
      ))
  else:
    # 车型级：品牌 × 具体车型的笛卡尔积
    if has_carriage:
      for brand_id in brand_ids:
        for model_id in carriage_model_ids:
          db.session.add(LightModelCarriage(
            light_model_id=item.id,
            carriage_model_id=model_id,
            brand_id=brand_id
          ))
    if has_trainset:
      for brand_id in brand_ids:
        for model_id in trainset_model_ids:
          db.session.add(LightModelTrainset(
            light_model_id=item.id,
            trainset_model_id=model_id,
            brand_id=brand_id
          ))


# 选项类型配置：模型类、是否需要级联检查、级联检查字段
OPTION_CONFIG = {
  # 简单选项（只有 name 字段）
  'power_type': {
    'model': PowerType,
    'cascade_check': None,
    'fields': ['name']
  },
  'brand': {
    'model': Brand,
    'cascade_check': None,
    'fields': ['name', 'website', 'search_url', 'abbreviation'],
    'optional_fields': ['website', 'search_url', 'abbreviation']
  },
  'merchant': {
    'model': Merchant,
    'cascade_check': None,
    'fields': ['name', 'website'],
    'optional_fields': ['website']
  },
  'depot': {
    'model': Depot,
    'cascade_check': None,
    'fields': ['name']
  },
  'chip_interface': {
    'model': ChipInterface,
    'cascade_check': None,
    'fields': ['name']
  },
  'chip_model': {
    'model': ChipModel,
    'cascade_check': None,
    'fields': ['name'],
    'post_save': _save_chip_model_interfaces
  },
  'locomotive_series': {
    'model': LocomotiveSeries,
    'cascade_check': ['locomotives', 'models'],
    'fields': ['name']
  },
  'carriage_series': {
    'model': CarriageSeries,
    'cascade_check': ['carriage_sets', 'models'],
    'fields': ['name']
  },
  'trainset_series': {
    'model': TrainsetSeries,
    'cascade_check': ['trainsets', 'models'],
    'fields': ['name']
  },
  # 复杂选项（有额外关联字段）
  'locomotive_model': {
    'model': LocomotiveModel,
    'cascade_check': ['locomotives'],
    'fields': ['name', 'series_id', 'power_type_id'],
    'template': 'option_edit_locomotive_model.html',
    'extra_data': lambda: {
      'locomotive_series': LocomotiveSeries.query.all(),
      'power_types': PowerType.query.all()
    }
  },
  'carriage_model': {
    'model': CarriageModel,
    'cascade_check': ['items'],
    'fields': ['name', 'series_id', 'type'],
    'template': 'option_edit_carriage_model.html',
    'extra_data': lambda: {
      'carriage_series': CarriageSeries.query.all()
    }
  },
  'trainset_model': {
    'model': TrainsetModel,
    'cascade_check': ['trainsets', 'locomotive_heads'],
    'fields': ['name', 'series_id', 'power_type_id'],
    'template': 'option_edit_trainset_model.html',
    'extra_data': lambda: {
      'trainset_series': TrainsetSeries.query.all(),
      'power_types': PowerType.query.all()
    }
  },
  'light_brand': {
    'model': LightBrand,
    'cascade_check': ['light_models'],
    'fields': ['name']
  },
  'light_model': {
    'model': LightModel,
    'cascade_check': None,
    'custom_cascade_check': check_light_model_cascade,
    'post_save': save_light_model_applicabilities,
    'fields': ['name', 'color_temperature', 'light_brand_id', 'scale'],
    'template': 'option_edit_light_model.html',
    'extra_data': lambda: {
      'light_brands': LightBrand.query.all(),
      'brands': Brand.query.all(),
      'carriage_models': CarriageModel.query.all(),
      'trainset_models': TrainsetModel.query.all()
    }
  }
}


@options_bp.route('/options')
def options():
  """信息维护页面"""
  return render_template('options.html',
    power_types=PowerType.query.all(),
    brands=Brand.query.all(),
    merchants=Merchant.query.all(),
    depots=Depot.query.all(),
    chip_interfaces=ChipInterface.query.all(),
    chip_models=ChipModel.query.all(),
    locomotive_series=LocomotiveSeries.query.all(),
    locomotive_models=LocomotiveModel.query.all(),
    carriage_series=CarriageSeries.query.all(),
    carriage_models=CarriageModel.query.all(),
    trainset_series=TrainsetSeries.query.all(),
    trainset_models=TrainsetModel.query.all(),
    light_brands=LightBrand.query.all(),
    light_models=LightModel.query.all()
  )


# 使用工厂函数生成路由
def create_option_add_route(option_type):
  """创建添加选项的路由"""
  def add():
    try:
      config = OPTION_CONFIG[option_type]
      model_class = config['model']

      # 构建字段字典
      kwargs = {}
      for field in config['fields']:
        value = request.form.get(field)
        if field.endswith('_id') and value:
          kwargs[field] = int(value)
        elif field == 'type':
          kwargs[field] = value
        elif value:
          kwargs[field] = value

      # 品牌特殊处理：abbreviation 为空时自动生成
      if option_type == 'brand':
        if not kwargs.get('abbreviation'):
          name = kwargs.get('name', '')
          kwargs['abbreviation'] = generate_brand_abbreviation(name)

      item = model_class(**kwargs)
      db.session.add(item)
      db.session.commit()

      # 灯型号特殊处理：保存适用车型关联
      post_save = config.get('post_save')
      if post_save:
        post_save(item, request.form)

      logger.info(f"{option_type} added: ID={item.id}")
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error adding {option_type}: {e}")
    return redirect(url_for('options.options'))
  return add


def create_option_delete_route(option_type):
  """创建删除选项的路由"""
  def delete(id):
    try:
      config = OPTION_CONFIG[option_type]
      model_class = config['model']
      item = db.get_or_404(model_class, id)
      # 自定义级联检查（如灯型号被 CarriageItem/Trainset/LocomotiveHead 引用）
      custom_cascade_check = config.get('custom_cascade_check')
      if custom_cascade_check:
        msg = custom_cascade_check(item)
        if msg:
          return f"{html.escape(msg)}<script>setTimeout(()=>location.href='/options', 2000);</script>"
      # 检查是否被使用
      if config['cascade_check']:
        for relation in config['cascade_check']:
          if hasattr(item, relation) and getattr(item, relation):
            return f"该{html.escape(option_type)}正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
      db.session.delete(item)
      db.session.commit()
      logger.info(f"{option_type} deleted: ID={id}")
    except Exception as e:
      db.session.rollback()
      logger.error(f"Error deleting {option_type}: {e}")
    return redirect(url_for('options.options'))
  return delete
def create_option_edit_route(option_type):
  """创建编辑选项的路由"""
  def edit(id):
    config = OPTION_CONFIG[option_type]
    model_class = config['model']
    optional_fields = config.get('optional_fields', [])
    item = db.get_or_404(model_class, id)
    if request.method == 'POST':
      try:
        for field in config['fields']:
          value = request.form.get(field)
          # _id 字段需要非空才能转换为 int
          if field.endswith('_id'):
            if value:
              setattr(item, field, int(value))
          # type 字段特殊处理
          elif field == 'type':
            setattr(item, field, value)
          # 可选字段允许设置为空
          elif field in optional_fields:
            setattr(item, field, value or None)
          # 其他字段需要非空
          elif value:
            setattr(item, field, value)
        # 品牌特殊处理:验证 abbreviation 唯一性
        if option_type == 'brand' and item.abbreviation:
          new_abbr = item.abbreviation  # rollback 前捕获，避免响应用回滚后的原值
          with db.session.no_autoflush:
            existing = Brand.query.filter(
              Brand.abbreviation == new_abbr,
              Brand.id != item.id
            ).first()
          if existing:
            db.session.rollback()
            return f"缩写 '{html.escape(new_abbr)}' 已被其他品牌使用！<script>setTimeout(()=>history.back(), 2000);</script>"
        # 灯型号特殊处理:保存适用车型关联
        post_save = config.get('post_save')
        if post_save:
          post_save(item, request.form)
        db.session.commit()
        return redirect(url_for('options.options'))
      except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing {option_type}: {e}")
    # 添加 light_model 的 applicability 模板上下文
    context = {'item': item, 'title': f'编辑{option_type}', 'action_url': url_for(f'options.edit_{option_type}', id=id)}
    if option_type == 'light_model':
      # 构建已选中的品牌和车型 ID 集合（用于模板 checkbox 的 checked 状态）
      selected_brand_ids = set()
      selected_carriage_model_ids = set()
      selected_trainset_model_ids = set()
      # 车型级规则
      for app in item.carriage_applicabilities:
        selected_brand_ids.add(app.brand_id)
        selected_carriage_model_ids.add(app.carriage_model_id)
      for app in item.trainset_applicabilities:
        selected_brand_ids.add(app.brand_id)
        selected_trainset_model_ids.add(app.trainset_model_id)
      # 品牌级规则
      brand_level_brand_ids = set()
      for app in item.brand_applicabilities:
        selected_brand_ids.add(app.brand_id)
        brand_level_brand_ids.add(app.brand_id)
      context['selected_brand_ids'] = selected_brand_ids
      context['selected_carriage_model_ids'] = selected_carriage_model_ids
      context['selected_trainset_model_ids'] = selected_trainset_model_ids
      context['brand_level_brand_ids'] = brand_level_brand_ids
    if 'extra_data' in config:
      context.update(config['extra_data']())
    # 获取模板
    template = config.get('template', 'option_edit_simple.html')
    return render_template(template, **context)
  return edit
# 动态注册路由
for option_type in OPTION_CONFIG:
  # 添加路由
  add_func = create_option_add_route(option_type)
  add_func.__name__ = f'add_{option_type}'
  options_bp.add_url_rule(f'/options/{option_type}', endpoint=f'add_{option_type}', methods=['POST'], view_func=add_func)
  # 删除路由
  delete_func = create_option_delete_route(option_type)
  delete_func.__name__ = f'delete_{option_type}'
  options_bp.add_url_rule(f'/options/{option_type}/delete/<int:id>', endpoint=f'delete_{option_type}', methods=['POST'], view_func=delete_func)
  # 编辑路由
  edit_func = create_option_edit_route(option_type)
  edit_func.__name__ = f'edit_{option_type}'
  options_bp.add_url_rule(f'/options/{option_type}/edit/<int:id>', endpoint=f'edit_{option_type}', methods=['GET', 'POST'], view_func=edit_func)
@options_bp.route('/api/options/<string:type>/edit', methods=['POST'])
def edit_option_api(type):
  """选项行内编辑 API"""
  if type not in OPTION_CONFIG:
    return jsonify(api_error('未知类型')), 400
  try:
    config = OPTION_CONFIG[type]
    model_class = config['model']
    optional_fields = config.get('optional_fields', [])
    id = request.form.get('id')
    item = db.get_or_404(model_class, id)
    for field in config['fields']:
      value = request.form.get(field)
      # _id 字段需要非空才能转换为 int
      if field.endswith('_id'):
        if value:
          setattr(item, field, int(value))
      # 可选字段允许设置为空
      elif field in optional_fields:
        setattr(item, field, value or None)
      # 其他字段需要非空
      elif value:
        setattr(item, field, value)
    # 品牌特殊处理:验证 abbreviation 唯一性
    if type == 'brand' and item.abbreviation:
      with db.session.no_autoflush:
        existing = Brand.query.filter(
          Brand.abbreviation == item.abbreviation,
          Brand.id != item.id
        ).first()
      if existing:
        return jsonify(api_error(f"缩写 '{item.abbreviation}' 已被其他品牌使用")), 400
    # 调用 post_save 钩子（如芯片型号-接口关联）
    post_save = config.get('post_save')
    if post_save:
      post_save(item, request.form)
    db.session.commit()
    return jsonify(api_success('保存成功'))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error editing {type}: {e}")
    return jsonify(api_error(str(e))), 500
