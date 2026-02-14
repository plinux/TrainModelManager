from app import app
from models import db, PowerType, Brand, ChipInterface, ChipModel, Merchant, Depot
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel

def init_db():
  """初始化数据库并插入预置数据"""
  with app.app_context():
    db.create_all()
    insert_reference_data()
    print("数据库初始化完成！")

def insert_reference_data():
  """插入参考数据"""

  # 1. 动力类型
  power_types = ['蒸汽', '电力', '内燃', '双源']
  for name in power_types:
    if not PowerType.query.filter_by(name=name).first():
      db.session.add(PowerType(name=name))

  # 2. 机车系列
  locomotive_series = ['内电', '内集', '东风', '韶山', '和谐电', '和谐内', '复兴电', '复兴内', 'Vossloh', 'Vectron', 'EMD', 'TRAXX']
  for name in locomotive_series:
    if not LocomotiveSeries.query.filter_by(name=name).first():
      db.session.add(LocomotiveSeries(name=name))

  # 3. 车厢系列
  carriage_series = ['22', '25B', '25G', '25T', '25Z', '19T', '棚车', '敞车', '平车', '罐车']
  for name in carriage_series:
    if not CarriageSeries.query.filter_by(name=name).first():
      db.session.add(CarriageSeries(name=name))

  # 4. 动车组系列
  trainset_series = ['ICE', 'TGV', 'CRH', 'CRH380', 'CR400', 'CR450', 'DESIRO', 'RailJet', '新干线', '特急', '旅游列车']
  for name in trainset_series:
    if not TrainsetSeries.query.filter_by(name=name).first():
      db.session.add(TrainsetSeries(name=name))

  # 5. 芯片接口
  chip_interfaces = ['NEM651(6pin)', 'NEM652(8pin)', 'MTC21', 'MKL21', 'NEXT18', 'PluX16', 'PluX22', 'E24']
  for name in chip_interfaces:
    if not ChipInterface.query.filter_by(name=name).first():
      db.session.add(ChipInterface(name=name))

  # 6. 芯片型号
  chip_models = ['动芯5323', '动芯8004', '动芯8003', 'ESU5.0', 'MS450P22', 'XP5.1', 'Pragon4', 'Tsunami2']
  for name in chip_models:
    if not ChipModel.query.filter_by(name=name).first():
      db.session.add(ChipModel(name=name))

  # 7. 品牌
  brands = ['1435', 'ATHEARN', 'BLI', 'CMR', 'PIKO', 'ROCO', 'TRIX', '百万城', '浩瀚', '深东', '猩猩', '长鸣', '跨越', 'Kunter', '茂杉', 'KATO', 'HCMX', 'HTMX', 'KukePig', 'N27', '毫米制造', '火车花园', '曙光', 'WALTHERS', 'Tomix', '微景', 'ARNOLD', 'Fleischmann', 'MicroAce']
  for name in brands:
    if not Brand.query.filter_by(name=name).first():
      db.session.add(Brand(name=name))

  # 8. 商家
  merchants = ['星期五火车模型', 'SRE铁路模型店', '火车女侠店', '长鸣淘宝', '长鸣京东', '中车文创', 'Kunter飘局的模型店', '南京攀登者模型', '铸造模型', '天易模型', '日本N比例火车模型店', '百万城百克曼', '魔都铁路模型社', '火车模型之家', '百万城旗舰店', '1435火车模型', '浩瀚火车模型', '宁东火车模型', '百酷火车模型', '阿易火车模型', '闲鱼']
  for name in merchants:
    if not Merchant.query.filter_by(name=name).first():
      db.session.add(Merchant(name=name))

  # 9. 车辆段/机务段
  depots = ['京局京段', '京局丰段', '上局沪段', '上局杭段']
  for name in depots:
    if not Depot.query.filter_by(name=name).first():
      db.session.add(Depot(name=name))

  db.session.commit()

if __name__ == '__main__':
  init_db()
