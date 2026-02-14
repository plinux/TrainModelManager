from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date

db = SQLAlchemy()

# 参考数据表 - 跨模型共享
class PowerType(db.Model):
  """动力类型（机车和动车组共享）"""
  __tablename__ = 'power_type'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='动力类型名称')

class Brand(db.Model):
  """品牌（所有模型共享）"""
  __tablename__ = 'brand'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='品牌名称')

class ChipInterface(db.Model):
  """芯片接口（机车和动车组共享）"""
  __tablename__ = 'chip_interface'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='芯片接口名称')

class ChipModel(db.Model):
  """芯片型号（机车和动车组共享）"""
  __tablename__ = 'chip_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='芯片型号名称')

class Merchant(db.Model):
  """购买商家（所有模型共享）"""
  __tablename__ = 'merchant'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='商家名称')

class Depot(db.Model):
  """车辆段/机务段（机车、车厢、动车组共享）"""
  __tablename__ = 'depot'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='车辆段/机务段名称')

# 机车专用表
class LocomotiveSeries(db.Model):
  """机车系列"""
  __tablename__ = 'locomotive_series'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='机车系列名称')

class LocomotiveModel(db.Model):
  """机车型号（关联系列和类型）"""
  __tablename__ = 'locomotive_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, comment='机车型号名称')
  series_id = db.Column(Integer, ForeignKey('locomotive_series.id'), nullable=False, comment='关联系列ID')
  power_type_id = db.Column(Integer, ForeignKey('power_type.id'), nullable=False, comment='关联动力类型ID')

  series = relationship('LocomotiveSeries', backref='models')
  power_type = relationship('PowerType', backref='locomotive_models')

# 车厢专用表
class CarriageSeries(db.Model):
  """车厢系列"""
  __tablename__ = 'carriage_series'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='车厢系列名称')

class CarriageModel(db.Model):
  """车厢型号（关联系列和类型）"""
  __tablename__ = 'carriage_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, comment='车厢型号名称')
  series_id = db.Column(Integer, ForeignKey('carriage_series.id'), nullable=False, comment='关联系列ID')
  type = db.Column(String(20), nullable=False, comment='类型：客车/货车/工程车')

  series = relationship('CarriageSeries', backref='models')

# 动车组专用表（与先头车共享）
class TrainsetSeries(db.Model):
  """动车组系列"""
  __tablename__ = 'trainset_series'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='动车组系列名称')

class TrainsetModel(db.Model):
  """动车组车型（关联系列和类型）"""
  __tablename__ = 'trainset_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, comment='动车组车型名称')
  series_id = db.Column(Integer, ForeignKey('trainset_series.id'), nullable=False, comment='关联系列ID')
  power_type_id = db.Column(Integer, ForeignKey('power_type.id'), nullable=False, comment='关联动力类型ID')

  series = relationship('TrainsetSeries', backref='models')
  power_type = relationship('PowerType', backref='trainset_models')

# 核心数据表
class Locomotive(db.Model):
  """机车模型"""
  __tablename__ = 'locomotive'

  id = db.Column(Integer, primary_key=True, comment='主键')
  series_id = db.Column(Integer, ForeignKey('locomotive_series.id'), comment='关联机车系列ID')
  power_type_id = db.Column(Integer, ForeignKey('power_type.id'), comment='关联动力类型ID')
  model_id = db.Column(Integer, ForeignKey('locomotive_model.id'), comment='关联机车型号ID')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
  depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联机务段ID')
  plaque = db.Column(String(50), comment='挂牌')
  color = db.Column(String(50), comment='颜色')
  scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
  locomotive_number = db.Column(String(12), comment='机车号（4-12位数字，前导0）')
  decoder_number = db.Column(String(4), comment='编号（1-4位数字，无前导0）')
  chip_interface_id = db.Column(Integer, ForeignKey('chip_interface.id'), comment='关联芯片接口ID')
  chip_model_id = db.Column(Integer, ForeignKey('chip_model.id'), comment='关联芯片型号ID')
  price = db.Column(String(50), comment='价格表达式（如288+538）')
  total_price = db.Column(Float, comment='总价（自动计算）')
  item_number = db.Column(String(50), comment='货号')
  purchase_date = db.Column(Date, default=date.today, comment='购买日期')
  merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

  # 关系
  series = relationship('LocomotiveSeries', backref='locomotives')
  power_type = relationship('PowerType', backref='locomotives')
  model = relationship('LocomotiveModel', backref='locomotives')
  brand = relationship('Brand', backref='locomotives')
  depot = relationship('Depot', backref='locomotives')
  chip_interface = relationship('ChipInterface', backref='locomotives')
  chip_model = relationship('ChipModel', backref='locomotives')
  merchant = relationship('Merchant', backref='locomotives')

class CarriageSet(db.Model):
  """车厢套装主表"""
  __tablename__ = 'carriage_set'

  id = db.Column(Integer, primary_key=True, comment='主键')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
  series_id = db.Column(Integer, ForeignKey('carriage_series.id'), comment='关联车厢系列ID')
  depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联车辆段ID')
  train_number = db.Column(String(20), comment='车次')
  plaque = db.Column(String(50), comment='挂牌')
  item_number = db.Column(String(50), comment='货号')
  scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
  total_price = db.Column(Float, comment='总价')
  purchase_date = db.Column(Date, default=date.today, comment='购买日期')
  merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

  # 关系
  brand = relationship('Brand', backref='carriage_sets')
  series = relationship('CarriageSeries', backref='carriage_sets')
  depot = relationship('Depot', backref='carriage_sets')
  merchant = relationship('Merchant', backref='carriage_sets')
  items = relationship('CarriageItem', backref='set', cascade='all, delete-orphan')

class CarriageItem(db.Model):
  """车厢套装子表（每辆车的详细信息）"""
  __tablename__ = 'carriage_item'

  id = db.Column(Integer, primary_key=True, comment='主键')
  set_id = db.Column(Integer, ForeignKey('carriage_set.id'), nullable=False, comment='关联套装ID')
  model_id = db.Column(Integer, ForeignKey('carriage_model.id'), comment='关联车厢型号ID')
  car_number = db.Column(String(10), comment='车辆号（3-10位数字，无前导0）')
  color = db.Column(String(50), comment='颜色')
  lighting = db.Column(String(50), comment='灯光')

  # 关系
  model = relationship('CarriageModel', backref='items')
