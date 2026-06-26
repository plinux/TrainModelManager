"""
自动填充 API（P3-1：从 routes/api.py 拆分）

按车型返回关联的系列/动力/类型，供前端表单联动。
"""
from flask import Blueprint, jsonify
from models import db, LocomotiveModel, CarriageModel, TrainsetModel

auto_fill_bp = Blueprint('auto_fill', __name__, url_prefix='')


@auto_fill_bp.route('/api/auto-fill/locomotive/<int:model_id>')
def auto_fill_locomotive(model_id):
  """机车车型自动填充"""
  model = db.get_or_404(LocomotiveModel, model_id)
  return jsonify({
    'series_id': model.series_id,
    'power_type_id': model.power_type_id
  })


@auto_fill_bp.route('/api/auto-fill/carriage/<int:model_id>')
def auto_fill_carriage(model_id):
  """车厢车型自动填充"""
  model = db.get_or_404(CarriageModel, model_id)
  return jsonify({
    'series_id': model.series_id,
    'type': model.type
  })


@auto_fill_bp.route('/api/auto-fill/trainset/<int:model_id>')
def auto_fill_trainset(model_id):
  """动车组车型自动填充"""
  model = db.get_or_404(TrainsetModel, model_id)
  return jsonify({
    'series_id': model.series_id,
    'power_type_id': model.power_type_id
  })
