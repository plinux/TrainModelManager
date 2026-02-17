"""
信息维护路由 Blueprint
使用工厂函数简化 CRUD 操作
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models import db
from models import (
  PowerType, Brand, Merchant, Depot, ChipInterface, ChipModel,
  LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel,
  TrainsetSeries, TrainsetModel
)
from utils.helpers import safe_int, api_success, api_error
import subprocess
import logging

logger = logging.getLogger(__name__)
options_bp = Blueprint('options', __name__, url_prefix='')


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
    'fields': ['name', 'website', 'search_url'],
    'optional_fields': ['website', 'search_url']
  },
  'merchant': {
    'model': Merchant,
    'cascade_check': None,
    'fields': ['name']
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
    'fields': ['name']
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
    trainset_models=TrainsetModel.query.all()
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

      item = model_class(**kwargs)
      db.session.add(item)
      db.session.commit()
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
      item = model_class.query.get_or_404(id)

      # 检查是否被使用
      if config['cascade_check']:
        for relation in config['cascade_check']:
          if hasattr(item, relation) and getattr(item, relation):
            return f"该{option_type}正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"

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
    item = model_class.query.get_or_404(id)

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

        db.session.commit()
        return redirect(url_for('options.options'))
      except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing {option_type}: {e}")

    # 获取模板和额外数据
    template = config.get('template', 'option_edit_simple.html')
    context = {'item': item, 'title': f'编辑{option_type}', 'action_url': url_for(f'options.edit_{option_type}', id=id)}

    if 'extra_data' in config:
      context.update(config['extra_data']())

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
    item = model_class.query.get_or_404(id)

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

    db.session.commit()
    return jsonify(api_success('保存成功'))
  except Exception as e:
    db.session.rollback()
    logger.error(f"Error editing {type}: {e}")
    return jsonify(api_error(str(e))), 500
