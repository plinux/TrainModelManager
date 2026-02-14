from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import LocomotiveModel, LocomotiveSeries, PowerType, Brand, Depot, ChipInterface, ChipModel, Merchant
from models import CarriageModel, CarriageSeries, TrainsetModel, TrainsetSeries
from models import CarriageItem
from datetime import date
import re
import ast
import operator
import logging

# 配置日志
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s %(name)s %(levelname)s %(message)s',
  handlers=[
    logging.FileHandler('app.log'),
    logging.StreamHandler()
  ]
)
logger = logging.getLogger(__name__)

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
  chip_interfaces = ChipInterface.query.all()
  chip_models = ChipModel.query.all()
  locomotive_series = LocomotiveSeries.query.all()
  locomotive_models = LocomotiveModel.query.all()
  carriage_series = CarriageSeries.query.all()
  carriage_models = CarriageModel.query.all()
  trainset_series = TrainsetSeries.query.all()
  trainset_models = TrainsetModel.query.all()
  return render_template('options.html',
    power_types=power_types,
    brands=brands,
    merchants=merchants,
    depots=depots,
    chip_interfaces=chip_interfaces,
    chip_models=chip_models,
    locomotive_series=locomotive_series,
    locomotive_models=locomotive_models,
    carriage_series=carriage_series,
    carriage_models=carriage_models,
    trainset_series=trainset_series,
    trainset_models=trainset_models
  )

@app.route('/api/statistics')
def statistics():
  """获取汇总统计数据"""
  locomotives = Locomotive.query.all()
  carriage_sets = CarriageSet.query.all()
  trainsets = Trainset.query.all()
  locomotive_heads = LocomotiveHead.query.all()

  # 按比例分组
  locomotives_by_scale = {l.scale: len([x for x in locomotives if x.scale == l.scale]) for l in locomotives}
  carriage_sets_by_scale = {c.scale: len([x for x in carriage_sets if x.scale == c.scale]) for c in carriage_sets}
  trainsets_by_scale = {t.scale: len([x for x in trainsets if x.scale == t.scale]) for t in trainsets}
  locomotive_heads_by_scale = {l.scale: len([x for x in locomotive_heads if x.scale == l.scale]) for l in locomotive_heads}

  # 按品牌分组
  locomotives_by_brand = {}
  for l in locomotives:
    brand = l.brand.name if l.brand else '未知'
    locomotives_by_brand[brand] = locomotives_by_brand.get(brand, 0) + 1

  carriage_sets_by_brand = {}
  for c in carriage_sets:
    brand = c.brand.name if c.brand else '未知'
    carriage_sets_by_brand[brand] = carriage_sets_by_brand.get(brand, 0) + 1

  trainsets_by_brand = {}
  for t in trainsets:
    brand = t.brand.name if t.brand else '未知'
    trainsets_by_brand[brand] = trainsets_by_brand.get(brand, 0) + 1

  locomotive_heads_by_brand = {}
  for h in locomotive_heads:
    brand = h.brand.name if h.brand else '未知'
    locomotive_heads_by_brand[brand] = locomotive_heads_by_brand.get(brand, 0) + 1

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

def validate_locomotive_number(number):
  """验证机车号格式：4-12位数字，允许前导0"""
  return bool(re.match(r'^\d{4,12}$', number))

def validate_decoder_number(number):
  """验证编号格式：1-4位数字，无前导0"""
  return bool(re.match(r'^[1-9]\d{0,3}$', number))

def validate_trainset_number(number):
  """验证动车号格式：3-12位数字，允许前导0"""
  return bool(re.match(r'^\d{3,12}$', number))

def validate_car_number(number):
  """验证车辆号格式：3-10位数字，无前导0"""
  return bool(re.match(r'^[1-9]\d{2,9}$', number))

class SafeEval(ast.NodeVisitor):
  """安全的表达式求值器，只允许数字和基本运算"""

  def __init__(self):
    self._operators = {
      ast.Add: operator.add,
      ast.Sub: operator.sub,
      ast.Mult: operator.mul,
      ast.Div: operator.truediv,
      ast.USub: operator.neg
    }

  def visit(self, node):
    if not isinstance(node, self._allowed_nodes):
      raise ValueError(f"不安全的表达式节点: {type(node).__name__}")
    return super().visit(node)

  def _allowed_nodes(self, node):
    return isinstance(node, (
      ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant
    ))

  def generic_visit(self, node):
    if isinstance(node, ast.BinOp):
      left = self.visit(node.left)
      right = self.visit(node.right)
      return self._operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
      operand = self.visit(node.operand)
      return self._operators[type(node.op)](operand)
    elif isinstance(node, ast.Num):
      return node.n
    elif isinstance(node, ast.Constant):
      if isinstance(node.value, (int, float)):
        return node.value
      raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
    return super().generic_visit(node)

def calculate_price(price_expr):
  """安全计算价格表达式"""
  if not price_expr or not price_expr.strip():
    return 0
  # 只允许数字、+、-、*、/、()
  if not re.match(r'^[\d+\-*/().\s]+$', price_expr):
    return 0
  try:
    # 使用 AST 解析表达式
    expr = ast.parse(price_expr, mode='eval')
    evaluator = SafeEval()
    result = evaluator.visit(expr.body)
    # 确保结果是数字
    if isinstance(result, (int, float)):
      return result
    return 0
  except (ValueError, SyntaxError, TypeError, ZeroDivisionError):
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

    # 格式验证
    if locomotive_number and not validate_locomotive_number(locomotive_number):
      errors.append("机车号格式错误：应为4-12位数字，允许前导0")
    if decoder_number and not validate_decoder_number(decoder_number):
      errors.append("编号格式错误：应为1-4位数字，无前导0")

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
  logger.info(f"Deleting locomotive: {locomotive}")
  db.session.delete(locomotive)
  db.session.commit()
  logger.info(f"Locomotive deleted: ID={id}")
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

  errors = []

  if request.method == 'POST':
    # 先验证车辆号格式
    for i in range(10):
      model_key = f'model_{i}'
      car_number_key = f'car_number_{i}'

      if model_key in request.form and request.form.get(model_key):
        car_number = request.form.get(car_number_key)
        # 格式验证
        if car_number and not validate_car_number(car_number):
          errors.append(f"车辆号 {car_number} 格式错误：应为3-10位数字，无前导0")

    if not errors:
      # 验证通过后添加数据
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
    merchants=merchants,
    errors=errors
  )

@app.route('/carriage/delete/<int:id>', methods=['POST'])
def delete_carriage(id):
  """删除车厢套装"""
  carriage_set = CarriageSet.query.get_or_404(id)
  logger.info(f"Deleting carriage set: {carriage_set}")
  db.session.delete(carriage_set)
  db.session.commit()
  logger.info(f"Carriage set deleted: ID={id}")
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

    # 格式验证
    if trainset_number and not validate_trainset_number(trainset_number):
      errors.append("动车号格式错误：应为3-12位数字，允许前导0")
    if decoder_number and not validate_decoder_number(decoder_number):
      errors.append("编号格式错误：应为1-4位数字，无前导0")

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
  logger.info(f"Deleting trainset: {trainset}")
  db.session.delete(trainset)
  db.session.commit()
  logger.info(f"Trainset deleted: ID={id}")
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
  logger.info(f"Deleting locomotive head: {locomotive_head}")
  db.session.delete(locomotive_head)
  db.session.commit()
  logger.info(f"Locomotive head deleted: ID={id}")
  return redirect(url_for('locomotive_head'))

# 选项维护路由
@app.route('/options/power_type', methods=['POST'])
def add_power_type():
  power_type = PowerType(name=request.form.get('name'))
  logger.info(f"Adding power type: {power_type.name}")
  db.session.add(power_type)
  db.session.commit()
  logger.info(f"Power type added: ID={power_type.id}")
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

@app.route('/options/chip_interface', methods=['POST'])
def add_chip_interface():
  chip_interface = ChipInterface(name=request.form.get('name'))
  db.session.add(chip_interface)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/chip_interface/delete/<int:id>', methods=['POST'])
def delete_chip_interface(id):
  chip_interface = ChipInterface.query.get_or_404(id)
  db.session.delete(chip_interface)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/chip_model', methods=['POST'])
def add_chip_model():
  chip_model = ChipModel(name=request.form.get('name'))
  db.session.add(chip_model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/chip_model/delete/<int:id>', methods=['POST'])
def delete_chip_model(id):
  chip_model = ChipModel.query.get_or_404(id)
  db.session.delete(chip_model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/locomotive_series', methods=['POST'])
def add_locomotive_series():
  series = LocomotiveSeries(name=request.form.get('name'))
  db.session.add(series)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/locomotive_series/delete/<int:id>', methods=['POST'])
def delete_locomotive_series(id):
  series = LocomotiveSeries.query.get_or_404(id)
  if series.locomotives or series.models:
    return f"该机车系列正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
  db.session.delete(series)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/locomotive_model', methods=['POST'])
def add_locomotive_model():
  model = LocomotiveModel(
    name=request.form.get('name'),
    series_id=int(request.form.get('series_id')),
    power_type_id=int(request.form.get('power_type_id'))
  )
  db.session.add(model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/locomotive_model/delete/<int:id>', methods=['POST'])
def delete_locomotive_model(id):
  model = LocomotiveModel.query.get_or_404(id)
  if model.locomotives:
    return f"该机车型号正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
  db.session.delete(model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/carriage_series', methods=['POST'])
def add_carriage_series():
  series = CarriageSeries(name=request.form.get('name'))
  db.session.add(series)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/carriage_series/delete/<int:id>', methods=['POST'])
def delete_carriage_series(id):
  series = CarriageSeries.query.get_or_404(id)
  if series.carriages or series.models:
    return f"该车厢系列正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
  db.session.delete(series)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/carriage_model', methods=['POST'])
def add_carriage_model():
  model = CarriageModel(
    name=request.form.get('name'),
    series_id=int(request.form.get('series_id')),
    type=request.form.get('type')
  )
  db.session.add(model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/carriage_model/delete/<int:id>', methods=['POST'])
def delete_carriage_model(id):
  model = CarriageModel.query.get_or_404(id)
  if model.items:
    return f"该车厢型号正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
  db.session.delete(model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/trainset_series', methods=['POST'])
def add_trainset_series():
  series = TrainsetSeries(name=request.form.get('name'))
  db.session.add(series)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/trainset_series/delete/<int:id>', methods=['POST'])
def delete_trainset_series(id):
  series = TrainsetSeries.query.get_or_404(id)
  if series.trainsets or series.models:
    return f"该动车组系列正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
  db.session.delete(series)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/trainset_model', methods=['POST'])
def add_trainset_model():
  model = TrainsetModel(
    name=request.form.get('name'),
    series_id=int(request.form.get('series_id')),
    power_type_id=int(request.form.get('power_type_id'))
  )
  db.session.add(model)
  db.session.commit()
  return redirect(url_for('options'))

@app.route('/options/trainset_model/delete/<int:id>', methods=['POST'])
def delete_trainset_model(id):
  model = TrainsetModel.query.get_or_404(id)
  if model.trainsets or model.locomotive_heads:
    return f"该动车组车型正在被使用，无法删除！<script>setTimeout(()=>location.href='/options', 2000);</script>"
  db.session.delete(model)
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

# 错误处理器
@app.errorhandler(404)
def not_found(error):
  """404 错误处理"""
  return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
  """500 错误处理"""
  return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
  """全局异常处理"""
  db.session.rollback()
  logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
  return f"服务器错误: {str(error)}<script>setTimeout(()=>location.href='/', 3000);</script>", 500

if __name__ == '__main__':
  app.run(debug=True)
