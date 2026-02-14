from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import LocomotiveModel, LocomotiveSeries, PowerType, Brand, Depot, ChipInterface, ChipModel, Merchant
from models import CarriageModel, TrainsetModel
from datetime import date
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
  """汇总统计页面"""
  return render_template('index.html')

@app.route('/options')
def options():
  """选项维护页面"""
  return render_template('options.html')

@app.route('/api/statistics')
def statistics():
  """获取汇总统计数据"""
  locomotives = Locomotive.query.all()
  carriage_sets = CarriageSet.query.all()
  trainsets = Trainset.query.all()
  locomotive_heads = LocomotiveHead.query.all()

  return jsonify({
    'locomotive': {
      'count': len(locomotives),
      'total': sum(l.total_price or 0 for l in locomotives)
    },
    'carriage': {
      'count': len(carriage_sets),
      'total': sum(c.total_price or 0 for c in carriage_sets)
    },
    'trainset': {
      'count': len(trainsets),
      'total': sum(t.total_price or 0 for t in trainsets)
    },
    'locomotive_head': {
      'count': len(locomotive_heads),
      'total': sum(l.total_price or 0 for l in locomotive_heads)
    }
  })

def calculate_price(price_expr):
  """安全计算价格表达式"""
  if not price_expr:
    return 0
  # 只允许数字、+、-、*、/、()
  if not re.match(r'^[\d+\-*/().\s]+$', price_expr):
    return 0
  try:
    return eval(price_expr)
  except:
    return 0

def check_duplicate(table, field, value, scale=None):
  """检查同一比例内的唯一性"""
  if table == 'locomotive':
    if field == 'locomotive_number':
      return Locomotive.query.filter_by(locomotive_number=value, scale=scale).first()
    elif field == 'decoder_number':
      return Locomotive.query.filter_by(decoder_number=value, scale=scale).first()
  return None

@app.route('/locomotive', methods=['GET', 'POST'])
def locomotive():
  """机车模型列表和添加"""
  locomotives = Locomotive.query.all()
  locomotive_models = LocomotiveModel.query.all()
  locomotive_series = LocomotiveSeries.query.all()
  power_types = PowerType.query.all()
  brands = Brand.query.all()
  depots = Depot.query.all()
  chip_interfaces = ChipInterface.query.all()
  chip_models = ChipModel.query.all()
  merchants = Merchant.query.all()

  errors = []

  if request.method == 'POST':
    scale = request.form.get('scale')
    locomotive_number = request.form.get('locomotive_number')
    decoder_number = request.form.get('decoder_number')

    # 唯一性验证
    if locomotive_number and check_duplicate('locomotive', 'locomotive_number', locomotive_number, scale):
      errors.append(f"机车号 {locomotive_number} 在 {scale} 比例下已存在")
    if decoder_number and check_duplicate('locomotive', 'decoder_number', decoder_number, scale):
      errors.append(f"编号 {decoder_number} 在 {scale} 比例下已存在")

    if not errors:
      locomotive = Locomotive(
        model_id=int(request.form.get('model_id')),
        series_id=request.form.get('series_id'),
        power_type_id=request.form.get('power_type_id'),
        brand_id=int(request.form.get('brand_id')),
        depot_id=request.form.get('depot_id'),
        plaque=request.form.get('plaque'),
        color=request.form.get('color'),
        scale=scale,
        locomotive_number=locomotive_number,
        decoder_number=decoder_number,
        chip_interface_id=request.form.get('chip_interface_id'),
        chip_model_id=request.form.get('chip_model_id'),
        price=request.form.get('price'),
        total_price=calculate_price(request.form.get('price')),
        item_number=request.form.get('item_number'),
        purchase_date=request.form.get('purchase_date') or date.today(),
        merchant_id=request.form.get('merchant_id')
      )
      db.session.add(locomotive)
      db.session.commit()
      return redirect(url_for('locomotive'))

  return render_template('locomotive.html',
    locomotives=locomotives,
    locomotive_models=locomotive_models,
    locomotive_series=locomotive_series,
    power_types=power_types,
    brands=brands,
    depots=depots,
    chip_interfaces=chip_interfaces,
    chip_models=chip_models,
    merchants=merchants,
    errors=errors
  )

@app.route('/locomotive/delete/<int:id>', methods=['POST'])
def delete_locomotive(id):
  """删除机车模型"""
  locomotive = Locomotive.query.get_or_404(id)
  db.session.delete(locomotive)
  db.session.commit()
  return redirect(url_for('locomotive'))

@app.route('/api/auto-fill/locomotive/<int:model_id>')
def auto_fill_locomotive(model_id):
  """机车车型自动填充"""
  model = LocomotiveModel.query.get_or_404(model_id)
  return jsonify({
    'series_id': model.series_id,
    'power_type_id': model.power_type_id
  })

@app.route('/api/auto-fill/carriage/<int:model_id>')
def auto_fill_carriage(model_id):
  """车厢车型自动填充"""
  model = CarriageModel.query.get_or_404(model_id)
  return jsonify({
    'series_id': model.series_id,
    'type': model.type
  })

@app.route('/api/auto-fill/trainset/<int:model_id>')
def auto_fill_trainset(model_id):
  """动车组车型自动填充"""
  model = TrainsetModel.query.get_or_404(model_id)
  return jsonify({
    'series_id': model.series_id,
    'power_type_id': model.power_type_id
  })

if __name__ == '__main__':
  app.run(debug=True)
