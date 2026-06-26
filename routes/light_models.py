"""
灯型号 API（P3-1：从 routes/api.py 拆分）

按品牌/车型查询适用的室内灯型号，供前端表单下拉。
"""
from collections import OrderedDict
from flask import Blueprint, jsonify, request
from models import (
  LightModel, LightModelBrandApplicability, LightModelCarriage, LightModelTrainset
)
import logging

logger = logging.getLogger(__name__)
light_models_bp = Blueprint('light_models', __name__, url_prefix='')


@light_models_bp.route('/api/light-models/compatible')
def get_compatible_light_models():
  """查询适配指定车型+品牌组合的灯型号"""
  try:
    model_type = request.args.get('model_type')
    model_id = request.args.get('model_id', type=int)
    brand_id = request.args.get('brand_id', type=int)
    scale = request.args.get('scale')

    if model_type not in ('carriage', 'trainset', 'brand_only'):
      return jsonify({'success': False, 'error': 'model_type 必须为 carriage、trainset 或 brand_only'}), 400

    if not brand_id:
      return jsonify({'success': False, 'error': 'brand_id 不能为空'}), 400

    if model_type != 'brand_only' and not model_id:
      return jsonify({'success': False, 'error': 'model_id 不能为空'}), 400

    # 查询适用的灯型号ID（合并品牌级和车型级）
    light_model_ids = set()

    # 品牌级规则：适用于该品牌所有指定类型车型（含未来新增）
    vehicle_types = [model_type, 'all'] if model_type != 'brand_only' else ['all']
    brand_level_apps = LightModelBrandApplicability.query.filter(
      LightModelBrandApplicability.brand_id == brand_id,
      LightModelBrandApplicability.vehicle_type.in_(vehicle_types)
    ).all()
    for app in brand_level_apps:
      light_model_ids.add(app.light_model_id)

    # 车型级规则：精确匹配车型ID + 品牌ID（brand_only 模式跳过）
    if model_type != 'brand_only':
      if model_type == 'carriage':
        model_level_apps = LightModelCarriage.query.filter_by(
          carriage_model_id=model_id, brand_id=brand_id
        ).all()
      else:
        model_level_apps = LightModelTrainset.query.filter_by(
          trainset_model_id=model_id, brand_id=brand_id
        ).all()
      for app in model_level_apps:
        light_model_ids.add(app.light_model_id)

    # 查询灯型号
    if not light_model_ids:
      light_models = []
    else:
      query = LightModel.query.filter(LightModel.id.in_(light_model_ids))
      if scale:
        query = query.filter(LightModel.scale == scale)
      light_models = query.order_by(LightModel.light_brand_id, LightModel.name).all()

    # 按灯品牌分组
    groups_dict = OrderedDict()
    for lm in light_models:
      lb_id = lm.light_brand_id
      if lb_id not in groups_dict:
        groups_dict[lb_id] = {
          'light_brand_id': lb_id,
          'light_brand_name': lm.light_brand.name if lm.light_brand else '',
          'models': []
        }
      groups_dict[lb_id]['models'].append({
        'id': lm.id,
        'name': lm.name,
        'color_temperature': lm.color_temperature,
        'scale': lm.scale
      })

    return jsonify({
      'success': True,
      'groups': list(groups_dict.values()),
      'unfiltered': False
    })

  except Exception as e:
    logger.error(f"Failed to get compatible light models: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


@light_models_bp.route('/api/light-models/all')
def get_all_light_models():
  """获取所有灯品牌和灯型号（用于下拉菜单）"""
  try:
    light_models = LightModel.query.order_by(LightModel.light_brand_id, LightModel.name).all()

    groups_dict = OrderedDict()
    for lm in light_models:
      lb_id = lm.light_brand_id
      if lb_id not in groups_dict:
        groups_dict[lb_id] = {
          'light_brand_id': lb_id,
          'light_brand_name': lm.light_brand.name if lm.light_brand else '',
          'models': []
        }
      groups_dict[lb_id]['models'].append({
        'id': lm.id,
        'name': lm.name,
        'color_temperature': lm.color_temperature,
        'scale': lm.scale
      })

    return jsonify({
      'success': True,
      'groups': list(groups_dict.values())
    })

  except Exception as e:
    logger.error(f"Failed to get all light models: {str(e)}", exc_info=True)
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500
