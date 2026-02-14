"""
主路由 Blueprint
包含首页和统计 API
"""
from flask import Blueprint, render_template, jsonify
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead
from utils.helpers import group_by_field

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
  """汇总统计页面"""
  return render_template('index.html')


@main_bp.route('/api/statistics')
def statistics():
  """获取汇总统计数据"""
  locomotives = Locomotive.query.all()
  carriage_sets = CarriageSet.query.all()
  trainsets = Trainset.query.all()
  locomotive_heads = LocomotiveHead.query.all()

  # 使用通用分组函数按比例分组
  locomotives_by_scale = group_by_field(locomotives, lambda l: l.scale)
  carriage_sets_by_scale = group_by_field(carriage_sets, lambda c: c.scale)
  trainsets_by_scale = group_by_field(trainsets, lambda t: t.scale)
  locomotive_heads_by_scale = group_by_field(locomotive_heads, lambda l: l.scale)

  # 按品牌分组
  locomotives_by_brand = group_by_field(locomotives, lambda l: l.brand.name if l.brand else '未知')
  carriage_sets_by_brand = group_by_field(carriage_sets, lambda c: c.brand.name if c.brand else '未知')
  trainsets_by_brand = group_by_field(trainsets, lambda t: t.brand.name if t.brand else '未知')
  locomotive_heads_by_brand = group_by_field(locomotive_heads, lambda h: h.brand.name if h.brand else '未知')

  return jsonify({
    'locomotive': {
      'count': len(locomotives),
      'total': sum(l.total_price or 0 for l in locomotives),
      'by_scale': locomotives_by_scale,
      'by_brand': locomotives_by_brand
    },
    'carriage': {
      'count': len(carriage_sets),
      'total': sum(c.total_price or 0 for c in carriage_sets),
      'by_scale': carriage_sets_by_scale,
      'by_brand': carriage_sets_by_brand
    },
    'trainset': {
      'count': len(trainsets),
      'total': sum(t.total_price or 0 for t in trainsets),
      'by_scale': trainsets_by_scale,
      'by_brand': trainsets_by_brand
    },
    'locomotive_head': {
      'count': len(locomotive_heads),
      'total': sum(l.total_price or 0 for l in locomotive_heads),
      'by_scale': locomotive_heads_by_scale,
      'by_brand': locomotive_heads_by_brand
    }
  })
