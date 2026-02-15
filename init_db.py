from app import app
from models import db, PowerType, Brand, ChipInterface, ChipModel, Merchant, Depot
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel


def init_db():
  """初始化数据库并插入预置数据"""
  with app.app_context():
    # 删除所有表并重新创建
    db.drop_all()
    db.create_all()
    print("数据库表结构已重建")

    insert_reference_data()
    print("数据库初始化完成！")
    # 验证数据
    power_types = PowerType.query.all()
    locomotive_models = LocomotiveModel.query.all()
    print(f"动力类型数量: {len(power_types)}")
    print(f"机车型号数量: {len(locomotive_models)}")

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
  carriage_series = ['22', '25B', '25G', '25K', '25T', '25Z', '19T', '棚车', '敞车', '平车', '罐车', '守车', '吊车']
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

  # 7. 品牌（带官网）
  brands = [
    ('1435', None),
    ('ATHEARN', 'https://www.athearn.com/'),
    ('BLI', 'https://broadway-limited.com/'),
    ('CMR', None),
    ('PIKO', 'https://www.piko-shop.de/en/'),
    ('ROCO', 'https://www.roco.cc/ren/'),
    ('TRIX', 'https://www.trix.de/en'),
    ('百万城', 'http://www.bachmannchina.com.cn/'),
    ('浩瀚', None),
    ('深东', None),
    ('猩猩', 'http://www.lyxxmx.com/'),
    ('长鸣', None),
    ('跨越', 'https://www.auroraminiature.com/'),
    ('Kunter', None),
    ('茂杉', None),
    ('KATO', 'https://www.katomodels.com/'),
    ('HCMX', None),
    ('HTMX', None),
    ('KukePig', None),
    ('N27', None),
    ('毫米制造', None),
    ('火车花园', None),
    ('曙光', None),
    ('WALTHERS', 'https://www.walthers.com/'),
    ('Tomix', 'https://www.tomytec.co.jp/tomix/'),
    ('微景', None),
    ('ARNOLD', 'https://www.arnoldmodel.com/'),
    ('Fleischmann', 'https://www.fleischmann.de/fen'),
    ('MicroAce', 'http://www.microace-arii.co.jp/')
  ]
  for name, website in brands:
    if not Brand.query.filter_by(name=name).first():
      db.session.add(Brand(name=name, website=website))

  # 8. 商家
  merchants = ['星期五火车模型', 'SRE铁路模型店', '火车女侠店', '长鸣淘宝', '长鸣京东', '中车文创', 'Kunter飘局的模型店', '南京攀登者模型', '铸造模型', '天易模型', '日本N比例火车模型店', '百万城百克曼', '魔都铁路模型社', '火车模型之家', '百万城旗舰店', '1435火车模型', '浩瀚火车模型', '宁东火车模型', '百酷火车模型', '阿易火车模型', '闲鱼']
  for name in merchants:
    if not Merchant.query.filter_by(name=name).first():
      db.session.add(Merchant(name=name))

  # 9. 车辆段/机务段
  depots = [
    # 中国铁路局段
    '铁总', '国铁',
    '上局', '上局沪段', '上局杭段', '上局翔段', '上局宁东段', '上局合段',
    '京局', '京局京段', '京局京西段', '京局丰段', '京局邯段', '京局怀段', '京局津段',
    '哈局哈段', '哈局齐段', '哈局三段', '哈局昂段', '齐局昂段',
    '青局格段',
    '沈局沈段', '沈局苏段', '沈局锦段',
    '广铁广段', '广铁长段', '广铁株段', '广铁肇段', '广铁汕段', '广铁沙段', '广铁深段',
    '西局西段', '西局新段',
    '南局南段', '南局福段', '南局昌段',
    '兰局兰段', '兰局兰西段', '兰局迎段',
    '郑局乡段', '郑局洛段',
    '武局江段', '武局',
    '成局贵段', '成局渝段', '成局',
    '宁局柳段', '宁局南宁段',
    '太局湖段',
    '乌局',
    '金温温段', '金温铁路',
    '福州分局',
    # 其他中国机构
    '石厂', '晋厂', '广北', '西兰', '京丰', '上海梅铁', '中粮生化', '西安地铁',
    # 日本铁路
    'JR东日本', 'JR东海道', 'JR西日本', 'JR九州', 'JR四国', '南海电铁', '东武铁道',
    # 境外铁路
    'UP', 'SP', 'DB', 'DR', 'SNCF', 'SNCB', 'SBB', 'OBB', 'PKP', 'CFL', 'JR',
    'PIKO', 'ROCO', 'ME', 'EGP', 'KPK',
    'Länderbahn', 'RailAdventure', 'RAIL Gondola', 'NL-VRR', 'RAOX',
    'ATSF', 'GrandUnion', 'CONRAIL', 'PBR',
    'OUIGO', 'Lokaltog', 'M&H',
    # 其他
    '国家能源', '神华集团'
  ]
  for name in depots:
    if not Depot.query.filter_by(name=name).first():
      db.session.add(Depot(name=name))

  db.session.commit()

  # 获取动力类型引用
  power_electric = PowerType.query.filter_by(name='电力').first()
  power_diesel = PowerType.query.filter_by(name='内燃').first()

  # 10. 机车型号
  # 东风系列 - 内燃
  dongfeng_series = LocomotiveSeries.query.filter_by(name='东风').first()
  dongfeng_models = ['DF4', 'DF4B', 'DF4C', 'DF4D', 'DF5', 'DF5G', 'DF7', 'DF7B', 'DF7C', 'DF7D', 'DF7G', 'DF8B', 'DF11', 'DF11G']
  for name in dongfeng_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=dongfeng_series.id if dongfeng_series else None, power_type_id=power_diesel.id if power_diesel else None))

  # 韶山系列 - 电力
  shaoshan_series = LocomotiveSeries.query.filter_by(name='韶山').first()
  shaoshan_models = ['SS1', 'SS3', 'SS3B', 'SS4G', 'SS6', 'SS6B', 'SS7', 'SS7C', 'SS7D', 'SS7E', 'SS8', 'SS9', 'SS9G']
  for name in shaoshan_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=shaoshan_series.id if shaoshan_series else None, power_type_id=power_electric.id if power_electric else None))

  # 和谐电系列 - 电力
  hexie_dian_series = LocomotiveSeries.query.filter_by(name='和谐电').first()
  hexie_dian_models = ['HXD1', 'HXD1B', 'HXD1C', 'HXD1D', 'HXD2', 'HXD3', 'HXD3B', 'HXD3C', 'HXD3D']
  for name in hexie_dian_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=hexie_dian_series.id if hexie_dian_series else None, power_type_id=power_electric.id if power_electric else None))

  # 和谐内系列 - 内燃
  hexie_nei_series = LocomotiveSeries.query.filter_by(name='和谐内').first()
  hexie_nei_models = ['HXN5', 'HXN3', 'HXN5B']
  for name in hexie_nei_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=hexie_nei_series.id if hexie_nei_series else None, power_type_id=power_diesel.id if power_diesel else None))

  # 复兴电系列 - 电力
  fuxing_dian_series = LocomotiveSeries.query.filter_by(name='复兴电').first()
  fuxing_dian_models = ['FXD1C', 'FXD3C']
  for name in fuxing_dian_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=fuxing_dian_series.id if fuxing_dian_series else None, power_type_id=power_electric.id if power_electric else None))

  # 复兴内系列 - 内燃
  fuxing_nei_series = LocomotiveSeries.query.filter_by(name='复兴内').first()
  fuxing_nei_models = ['FXN5C', 'FXN3C']
  for name in fuxing_nei_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=fuxing_nei_series.id if fuxing_nei_series else None, power_type_id=power_diesel.id if power_diesel else None))

  # 内集系列 - 内燃
  neiji_series = LocomotiveSeries.query.filter_by(name='内集').first()
  neiji_models = ['NJ1', 'NJ2']
  for name in neiji_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=neiji_series.id if neiji_series else None, power_type_id=power_diesel.id if power_diesel else None))

  # 内电系列 - 内燃
  neidian_series = LocomotiveSeries.query.filter_by(name='内电').first()
  neidian_models = ['ND1', 'ND2', 'ND3', 'ND5']
  for name in neidian_models:
    if not LocomotiveModel.query.filter_by(name=name).first():
      db.session.add(LocomotiveModel(name=name, series_id=neidian_series.id if neidian_series else None, power_type_id=power_diesel.id if power_diesel else None))

  db.session.commit()

  # 11. 动车组车型
  # ICE系列 - 电力
  ice_series = TrainsetSeries.query.filter_by(name='ICE').first()
  ice_models = ['BR411(ICE-T)', 'BR402(ICE2)', 'BR403(ICE3)', 'BR407(ICE3)', 'BR412(ICE4)']
  for name in ice_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=ice_series.id if ice_series else None, power_type_id=power_electric.id if power_electric else None))

  # TGV系列 - 电力
  tgv_series = TrainsetSeries.query.filter_by(name='TGV').first()
  tgv_models = ['TGV-2N2(TGV)']
  for name in tgv_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=tgv_series.id if tgv_series else None, power_type_id=power_electric.id if power_electric else None))

  # CRH系列 - 电力
  crh_series = TrainsetSeries.query.filter_by(name='CRH').first()
  crh_models = ['CRH2A', 'CRH2C', 'CRH3C', 'CRH6F-A']
  for name in crh_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=crh_series.id if crh_series else None, power_type_id=power_electric.id if power_electric else None))

  # CRH380系列 - 电力
  crh380_series = TrainsetSeries.query.filter_by(name='CRH380').first()
  crh380_models = ['CRH380A', 'CRH380B', 'CRH380C']
  for name in crh380_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=crh380_series.id if crh380_series else None, power_type_id=power_electric.id if power_electric else None))

  # CR400系列 - 电力
  cr400_series = TrainsetSeries.query.filter_by(name='CR400').first()
  cr400_models = ['CR400AF', 'CR400BF', 'CR400AF-S', 'CR400BF-C']
  for name in cr400_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=cr400_series.id if cr400_series else None, power_type_id=power_electric.id if power_electric else None))

  # DESIRO系列 - 内燃
  desiro_series = TrainsetSeries.query.filter_by(name='DESIRO').first()
  if not TrainsetModel.query.filter_by(name='DMU').first():
    db.session.add(TrainsetModel(name='DMU', series_id=desiro_series.id if desiro_series else None, power_type_id=power_diesel.id if power_diesel else None))

  # RailJet系列 - 电力
  railjet_series = TrainsetSeries.query.filter_by(name='RailJet').first()
  railjet_models = ['BR101', 'Taurus(金牛座)']
  for name in railjet_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=railjet_series.id if railjet_series else None, power_type_id=power_electric.id if power_electric else None))

  # 新干线系列 - 电力
  shinkansen_series = TrainsetSeries.query.filter_by(name='新干线').first()
  shinkansen_models = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', '0系', '100系', '200系', '300系', '400系', '500系', '600系', '700系', '800系']
  for name in shinkansen_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=shinkansen_series.id if shinkansen_series else None, power_type_id=power_electric.id if power_electric else None))

  # 旅游列车系列 - 内燃
  lvyou_series = TrainsetSeries.query.filter_by(name='旅游列车').first()
  lvyou_diesel_models = ['Kiha70/71', '87系', '787系', '77系']
  for name in lvyou_diesel_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=lvyou_series.id if lvyou_series else None, power_type_id=power_diesel.id if power_diesel else None))

  # 旅游列车系列 - 电力
  lvyou_electric_models = ['E001型', '冰河急特', '485型']
  for name in lvyou_electric_models:
    if not TrainsetModel.query.filter_by(name=name).first():
      db.session.add(TrainsetModel(name=name, series_id=lvyou_series.id if lvyou_series else None, power_type_id=power_electric.id if power_electric else None))

  db.session.commit()

  # 12. 车厢型号
  # 22系列
  series_22 = CarriageSeries.query.filter_by(name='22').first()
  if not CarriageModel.query.filter_by(name='XL22').first():
    db.session.add(CarriageModel(name='XL22', series_id=series_22.id if series_22 else None, type='客车'))

  # 25B系列
  series_25b = CarriageSeries.query.filter_by(name='25B').first()
  models_25b = ['XL25B', 'YZ25B', 'YW25B', 'RW25B', 'CA25B', 'KD25B', 'SYZ25B']
  for name in models_25b:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_25b.id if series_25b else None, type='客车'))

  # 25G系列
  series_25g = CarriageSeries.query.filter_by(name='25G').first()
  models_25g = ['XL25G', 'YZ25G', 'YW25G', 'RW25G', 'CA25G', 'KD25G', 'JY25G']
  for name in models_25g:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_25g.id if series_25g else None, type='客车'))

  # 25K系列
  series_25k = CarriageSeries.query.filter_by(name='25K').first()
  models_25k = ['XL25K', 'YZ25K', 'YW25K', 'RW25K', 'CA25K', 'KD25K', 'RZ125K', 'RZ225K', 'RZT25K']
  for name in models_25k:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_25k.id if series_25k else None, type='客车'))

  # 25Z系列
  series_25z = CarriageSeries.query.filter_by(name='25Z').first()
  models_25z = ['SRZ125Z', 'SCA25Z', 'KD25Z']
  for name in models_25z:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_25z.id if series_25z else None, type='客车'))

  # 25T系列
  series_25t = CarriageSeries.query.filter_by(name='25T').first()
  models_25t = ['XL25T', 'YZ25T', 'YW25T', 'RW25T', 'CA25T', 'KD25T']
  for name in models_25t:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_25t.id if series_25t else None, type='客车'))

  # 19T系列
  series_19t = CarriageSeries.query.filter_by(name='19T').first()
  if not CarriageModel.query.filter_by(name='RW19T').first():
    db.session.add(CarriageModel(name='RW19T', series_id=series_19t.id if series_19t else None, type='客车'))

  # 棚车系列
  series_peng = CarriageSeries.query.filter_by(name='棚车').first()
  models_peng = ['PB', 'P61', 'JSQ6']
  for name in models_peng:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_peng.id if series_peng else None, type='货车'))

  # 敞车系列
  series_chang = CarriageSeries.query.filter_by(name='敞车').first()
  models_chang = ['C80B', 'C70E', 'C70']
  for name in models_chang:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_chang.id if series_chang else None, type='货车'))

  # 平车系列
  series_ping = CarriageSeries.query.filter_by(name='平车').first()
  models_ping = ['NX17K', 'X70']
  for name in models_ping:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_ping.id if series_ping else None, type='货车'))

  # 罐车系列
  series_guan = CarriageSeries.query.filter_by(name='罐车').first()
  models_guan = ['GQ70', 'G70K']
  for name in models_guan:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_guan.id if series_guan else None, type='货车'))

  # 守车系列
  series_shou = CarriageSeries.query.filter_by(name='守车').first()
  models_shou = ['S12', 'CA']
  for name in models_shou:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_shou.id if series_shou else None, type='工程车'))

  # 吊车系列
  series_diao = CarriageSeries.query.filter_by(name='吊车').first()
  models_diao = ['EDK-570', 'So80']
  for name in models_diao:
    if not CarriageModel.query.filter_by(name=name).first():
      db.session.add(CarriageModel(name=name, series_id=series_diao.id if series_diao else None, type='工程车'))

  db.session.commit()

if __name__ == '__main__':
  init_db()
