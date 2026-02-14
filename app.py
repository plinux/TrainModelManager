from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import LocomotiveModel, LocomotiveSeries, PowerType, Brand, Depot, ChipInterface, ChipModel, Merchant
from models import CarriageModel, CarriageSeries, TrainsetModel
from models import CarriageItem
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
  power_types = PowerType.query.all()
  brands = Brand.query.all()
  merchants = Merchant.query.all()
  depots = Depot.query.all()
  return render_template('options.html',
    power_types=power_types,
    brands=brands,
    merchants=merchants,
    depots=depots
  )

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
  elif table == 'trainset':
    if field == 'trainset_number':
      return Trainset.query.filter_by(trainset_number=value, scale=scale).first()
    elif field == 'decoder_number':
      return Trainset.query.filter_by(decoder_number=value, scale=scale).first()
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

@app.route('/carriage', methods=['GET', 'POST'])
def carriage():
  """车厢模型列表和添加"""
  carriage_sets = CarriageSet.query.all()
  carriage_models = CarriageModel.query.all()
  carriage_series = CarriageSeries.query.all()
  brands = Brand.query.all()
  depots = Depot.query.all()
  merchants = Merchant.query.all()

  if request.method == 'POST':
    carriage_set = CarriageSet(
      brand_id=int(request.form.get('brand_id')),
      series_id=request.form.get('series_id'),
      depot_id=request.form.get('depot_id'),
      train_number=request.form.get('train_number'),
      plaque=request.form.get('plaque'),
      item_number=request.form.get('item_number'),
      scale=request.form.get('scale'),
      total_price=float(request.form.get('total_price') or 0),
      purchase_date=request.form.get('purchase_date') or date.today(),
      merchant_id=request.form.get('merchant_id')
    )
    db.session.add(carriage_set)
    db.session.commit()
    db.session.refresh(carriage_set)

    # 添加车厢项
    for i in range(10):
      model_key = f'model_{i}'
      car_number_key = f'car_number_{i}'
      color_key = f'color_{i}'
      lighting_key = f'lighting_{i}'

      if model_key in request.form and request.form.get(model_key):
        carriage_item = CarriageItem(
          set_id=carriage_set.id,
          model_id=int(request.form.get(model_key)),
          car_number=request.form.get(car_number_key),
          color=request.form.get(color_key),
          lighting=request.form.get(lighting_key)
        )
        db.session.add(carriage_item)

    db.session.commit()
    return redirect(url_for('carriage'))

  return render_template('carriage.html',
    carriage_sets=carriage_sets,
    carriage_models=carriage_models,
    carriage_series=carriage_series,
    brands=brands,
    depots=depots,
    merchants=merchants
  )

@app.route('/carriage/delete/<int:id>', methods=['POST'])
def delete_carriage(id):
  """删除车厢套装"""
  carriage_set = CarriageSet.query.get_or_404(id)
  db.session.delete(carriage_set)
  db.session.commit()
  return redirect(url_for('carriage'))

@app.route('/trainset', methods=['GET', 'POST'])
def trainset():
  """动车组模型列表和添加"""
  trainsets = Trainset.query.all()
  trainset_models = TrainsetModel.query.all()
  trainset_series = TrainsetSeries.query.all()
  power_types = PowerType.query.all()
  brands = Brand.query.all()
  depots = Depot.query.all()
  chip_interfaces = ChipInterface.query.all()
  chip_models = ChipModel.query.all()
  merchants = Merchant.query.all()

  errors = []

  if request.method == 'POST':
    scale = request.form.get('scale')
    trainset_number = request.form.get('trainset_number')
    decoder_number = request.form.get('decoder_number')

    # 唯一性验证
    if trainset_number and check_duplicate('trainset', 'trainset_number', trainset_number, scale):
      errors.append(f"动车号 {trainset_number} 在 {scale} 比例下已存在")
    if decoder_number and check_duplicate('trainset', 'decoder_number', decoder_number, scale):
      errors.append(f"编号 {decoder_number} 在 {scale} 比例下已存在")

    if not errors:
      trainset = Trainset(
        model_id=int(request.form.get('model_id')),
        series_id=request.form.get('series_id'),
        power_type_id=request.form.get('power_type_id'),
        brand_id=int(request.form.get('brand_id')),
        depot_id=request.form.get('depot_id'),
        plaque=request.form.get('plaque'),
        color=request.form.get('color'),
        scale=scale,
        formation=int(request.form.get('formation')) if request.form.get('formation') else None,
        trainset_number=trainset_number,
        decoder_number=decoder_number,
        head_light=True if request.form.get('head_light') == 'true' else False,
        interior_light=request.form.get('interior_light'),
        chip_interface_id=request.form.get('chip_interface_id'),
        chip_model_id=request.form.get('chip_model_id'),
        price=request.form.get('price'),
        total_price=calculate_price(request.form.get('price')),
        item_number=request.form.get('item_number'),
        purchase_date=request.form.get('purchase_date') or date.today(),
        merchant_id=request.form.get('merchant_id')
      )
      db.session.add(trainset)
      db.session.commit()
      return redirect(url_for('trainset'))

  return render_template('trainset.html',
    trainsets=trainsets,
    trainset_models=trainset_models,
    trainset_series=trainset_series,
    power_types=power_types,
    brands=brands,
    depots=depots,
    chip_interfaces=chip_interfaces,
    chip_models=chip_models,
    merchants=merchants,
    errors=errors
  )

@app.route('/trainset/delete/<int:id>', methods=['POST'])
def delete_trainset(id):
  """删除动车组模型"""
  trainset = Trainset.query.get_or_404(id)
  db.session.delete(trainset)
  db.session.commit()
  return redirect(url_for('trainset'))

@app.route('/locomotive-head', methods=['GET', 'POST'])
def locomotive_head():
  """先头车模型列表和添加"""
  locomotive_heads = LocomotiveHead.query.all()
  trainset_models = TrainsetModel.query.all()
  brands = Brand.query.all()
  depots = Depot.query.all()
  merchants = Merchant.query.all()

  if request.method == 'POST':
    locomotive_head = LocomotiveHead(
      model_id=int(request.form.get('model_id')),
      brand_id=int(request.form.get('brand_id')),
      depot_id=request.form.get('depot_id'),
      special_color=request.form.get('special_color'),
      scale=request.form.get('scale'),
      head_light=True if request.form.get('head_light') == 'true' else False,
      interior_light=request.form.get('interior_light'),
      price=request.form.get('price'),
      total_price=calculate_price(request.form.get('price')),
      item_number=request.form.get('item_number'),
      purchase_date=request.form.get('purchase_date') or date.today(),
      merchant_id=request.form.get('merchant_id')
    )
    db.session.add(locomotive_head)
    db.session.commit()
    return redirect(url_for('locomotive_head'))

  return render_template('locomotive_head.html',
    locomotive_heads=locomotive_heads,
    trainset_models=trainset_models,
    brands=brands,
    depots=depots,
    merchants=merchants
  )

@app.route('/locomotive-head/delete/<int:id>', methods=['POST'])
def delete_locomotive_head(id):
  """删除先头车模型"""
  locomotive_head = LocomotiveHead.query.get_or_404(id)
  db.session.delete(locomotive_head)
  db.session.commit()
  return redirect(url_for('locomotive_head'))

# 选项维护路由
@app.route('/options/power_type', methods=['POST'])
def add_power_type():
  power_type = PowerType(name=request.form.get('name'))
  db.session.add(power_type)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/power_type/delete/<int:id>', methods=['POST'])
def delete_power_type(id):
  power_type = PowerType.query.get_or_404(id)
  db.session.delete(power_type)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/brand', methods=['POST'])
def add_brand():
  brand = Brand(name=request.form.get('name'))
  db.session.add(brand)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/brand/delete/<int:id>', methods=['POST'])
def delete_brand(id):
  brand = Brand.query.get_or_404(id)
  db.session.delete(brand)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/merchant', methods=['POST'])
def add_merchant():
  merchant = Merchant(name=request.form.get('name'))
  db.session.add(merchant)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/merchant/delete/<int:id>', methods=['POST'])
def delete_merchant(id):
  merchant = Merchant.query.get_or_404(id)
  db.session.delete(merchant)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/depot', methods=['POST'])
def add_depot():
  depot = Depot(name=request.form.get('name'))
  db.session.add(depot)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/depot/delete/<int:id>', methods=['POST'])
def delete_depot(id):
  depot = Depot.query.get_or_404(id)
  db.session.delete(depot)
  db.session.commit()
  return redirect(url_for('options'))

# Auto-fill API
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
