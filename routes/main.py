"""
主路由 Blueprint
包含首页和统计 API
"""
from flask import Blueprint, render_template, jsonify
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead

main_bp = Blueprint('main', __name__)


def aggregate_stats(items, get_key_func, get_price_func):
  """
  聚合统计函数

  Args:
    items: 对象列表
    get_key_func: 获取分组键的函数
    get_price_func: 获取价格的函数

  Returns:
    dict: {key: {count: int, total: float}}
  """
  result = {}
  for item in items:
    key = get_key_func(item)
    if key not in result:
      result[key] = {'count': 0, 'total': 0}
    result[key]['count'] += 1
    result[key]['total'] += get_price_func(item) or 0
  return result


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

  # 各类型基础统计
  type_stats = {
    'locomotive': {
      'name': '机车模型',
      'count': len(locomotives),
      'total': sum(l.total_price or 0 for l in locomotives)
    },
    'carriage': {
      'name': '车厢模型',
      'count': len(carriage_sets),
      'total': sum(c.total_price or 0 for c in carriage_sets)
    },
    'trainset': {
      'name': '动车组模型',
      'count': len(trainsets),
      'total': sum(t.total_price or 0 for t in trainsets)
    },
    'locomotive_head': {
      'name': '先头车模型',
      'count': len(locomotive_heads),
      'total': sum(l.total_price or 0 for l in locomotive_heads)
    }
  }

  # 按比例分组统计
  scale_stats = {}
  for items, get_price in [
    (locomotives, lambda l: l.total_price),
    (carriage_sets, lambda c: c.total_price),
    (trainsets, lambda t: t.total_price),
    (locomotive_heads, lambda l: l.total_price)
  ]:
    for item in items:
      scale = item.scale
      if scale not in scale_stats:
        scale_stats[scale] = {'count': 0, 'total': 0}
      scale_stats[scale]['count'] += 1
      scale_stats[scale]['total'] += get_price(item) or 0

  # 按品牌分组统计
  brand_stats = {}
  for items, get_brand, get_price in [
    (locomotives, lambda l: l.brand.name if l.brand else '未知', lambda l: l.total_price),
    (carriage_sets, lambda c: c.brand.name if c.brand else '未知', lambda c: c.total_price),
    (trainsets, lambda t: t.brand.name if t.brand else '未知', lambda t: t.total_price),
    (locomotive_heads, lambda h: h.brand.name if h.brand else '未知', lambda h: h.total_price)
  ]:
    for item in items:
      brand = get_brand(item)
      if brand not in brand_stats:
        brand_stats[brand] = {'count': 0, 'total': 0}
      brand_stats[brand]['count'] += 1
      brand_stats[brand]['total'] += get_price(item) or 0

  # 按商家分组统计
  merchant_stats = {}
  for items, get_merchant, get_price in [
    (locomotives, lambda l: l.merchant.name if l.merchant else '未知', lambda l: l.total_price),
    (carriage_sets, lambda c: c.merchant.name if c.merchant else '未知', lambda c: c.total_price),
    (trainsets, lambda t: t.merchant.name if t.merchant else '未知', lambda t: t.total_price),
    (locomotive_heads, lambda h: h.merchant.name if h.merchant else '未知', lambda h: h.total_price)
  ]:
    for item in items:
      merchant = get_merchant(item)
      if merchant not in merchant_stats:
        merchant_stats[merchant] = {'count': 0, 'total': 0}
      merchant_stats[merchant]['count'] += 1
      merchant_stats[merchant]['total'] += get_price(item) or 0

  return jsonify({
    'type_stats': type_stats,
    'scale_stats': scale_stats,
    'brand_stats': brand_stats,
    'merchant_stats': merchant_stats
  })
