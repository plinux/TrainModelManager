from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Float, Boolean, Date, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import date, datetime

db = SQLAlchemy()

# 参考数据表 - 跨模型共享
class PowerType(db.Model):
  """动力类型（机车和动车组共享）"""
  __tablename__ = 'power_type'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='动力类型名称')

  def __repr__(self):
    return f'<PowerType {self.id}: {self.name}>'

class Brand(db.Model):
  """品牌（所有模型共享）"""
  __tablename__ = 'brand'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='品牌名称')
  website = db.Column(String(255), comment='官方网站')
  search_url = db.Column(String(255), comment='搜索URL模板，{query}为搜索词占位符')

  def __repr__(self):
    return f'<Brand {self.id}: {self.name}>'

class ChipInterface(db.Model):
  """芯片接口（机车和动车组共享）"""
  __tablename__ = 'chip_interface'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='芯片接口名称')

  def __repr__(self):
    return f'<ChipInterface {self.id}: {self.name}>'

class ChipModel(db.Model):
  """芯片型号（机车和动车组共享）"""
  __tablename__ = 'chip_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='芯片型号名称')

  def __repr__(self):
    return f'<ChipModel {self.id}: {self.name}>'

class Merchant(db.Model):
  """购买商家（所有模型共享）"""
  __tablename__ = 'merchant'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='商家名称')

  def __repr__(self):
    return f'<Merchant {self.id}: {self.name}>'

class Depot(db.Model):
  """车辆段/机务段（机车、车厢、动车组共享）"""
  __tablename__ = 'depot'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='车辆段/机务段名称')

  def __repr__(self):
    return f'<Depot {self.id}: {self.name}>'

# 机车专用表
class LocomotiveSeries(db.Model):
  """机车系列"""
  __tablename__ = 'locomotive_series'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='机车系列名称')

  def __repr__(self):
    return f'<LocomotiveSeries {self.id}: {self.name}>'

class LocomotiveModel(db.Model):
  """机车型号（关联系列和类型）"""
  __tablename__ = 'locomotive_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, comment='机车型号名称')
  series_id = db.Column(Integer, ForeignKey('locomotive_series.id'), nullable=False, comment='关联系列ID')
  power_type_id = db.Column(Integer, ForeignKey('power_type.id'), nullable=False, comment='关联动力类型ID')

  series = relationship('LocomotiveSeries', backref='models')
  power_type = relationship('PowerType', backref='locomotive_models')

  def __repr__(self):
    return f'<LocomotiveModel {self.id}: {self.name}>'

# 车厢专用表
class CarriageSeries(db.Model):
  """车厢系列"""
  __tablename__ = 'carriage_series'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='车厢系列名称')

  def __repr__(self):
    return f'<CarriageSeries {self.id}: {self.name}>'

class CarriageModel(db.Model):
  """车厢型号（关联系列和类型）"""
  __tablename__ = 'carriage_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, comment='车厢型号名称')
  series_id = db.Column(Integer, ForeignKey('carriage_series.id'), nullable=False, comment='关联系列ID')
  type = db.Column(String(20), nullable=False, comment='类型：客车/货车/工程车')

  series = relationship('CarriageSeries', backref='models')

  def __repr__(self):
    return f'<CarriageModel {self.id}: {self.name}>'

# 动车组专用表（与先头车共享）
class TrainsetSeries(db.Model):
  """动车组系列"""
  __tablename__ = 'trainset_series'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, unique=True, comment='动车组系列名称')

  def __repr__(self):
    return f'<TrainsetSeries {self.id}: {self.name}>'

class TrainsetModel(db.Model):
  """动车组车型（关联系列和类型）"""
  __tablename__ = 'trainset_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(50), nullable=False, comment='动车组车型名称')
  series_id = db.Column(Integer, ForeignKey('trainset_series.id'), nullable=False, comment='关联系列ID')
  power_type_id = db.Column(Integer, ForeignKey('power_type.id'), nullable=False, comment='关联动力类型ID')

  series = relationship('TrainsetSeries', backref='models')
  power_type = relationship('PowerType', backref='trainset_models')

  def __repr__(self):
    return f'<TrainsetModel {self.id}: {self.name}>'

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
  product_url = db.Column(String(1024), comment='产品地址')
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

  def __repr__(self):
    return f'<Locomotive {self.id}: {self.model.name} {self.scale}>'

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
  product_url = db.Column(String(1024), comment='产品地址')
  purchase_date = db.Column(Date, default=date.today, comment='购买日期')
  merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

  # 关系
  brand = relationship('Brand', backref='carriage_sets')
  series = relationship('CarriageSeries', backref='carriage_sets')
  depot = relationship('Depot', backref='carriage_sets')
  merchant = relationship('Merchant', backref='carriage_sets')
  items = relationship('CarriageItem', backref='set', cascade='all, delete-orphan')

  def __repr__(self):
    return f'<CarriageSet {self.id}: {self.train_number} {self.scale}>'

class CarriageItem(db.Model):
  """车厢套装子表（每辆车的详细信息）"""
  __tablename__ = 'carriage_item'

  id = db.Column(Integer, primary_key=True, comment='主键')
  set_id = db.Column(Integer, ForeignKey('carriage_set.id'), nullable=False, comment='关联套装ID')
  model_id = db.Column(Integer, ForeignKey('carriage_model.id'), comment='关联车厢型号ID')
  car_number = db.Column(String(20), comment='车辆号（1-20位字母、数字或连字符）')
  color = db.Column(String(50), comment='颜色')
  lighting = db.Column(String(50), comment='灯光')

  # 关系
  model = relationship('CarriageModel', backref='items')

  def __repr__(self):
    return f'<CarriageItem {self.id}: {self.model.name} {self.car_number}>'

class Trainset(db.Model):
  """动车组模型"""
  __tablename__ = 'trainset'

  id = db.Column(Integer, primary_key=True, comment='主键')
  series_id = db.Column(Integer, ForeignKey('trainset_series.id'), comment='关联动车组系列ID')
  power_type_id = db.Column(Integer, ForeignKey('power_type.id'), comment='关联动力类型ID')
  model_id = db.Column(Integer, ForeignKey('trainset_model.id'), comment='关联动车组车型ID')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
  depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联动车段ID')
  plaque = db.Column(String(50), comment='挂牌')
  color = db.Column(String(50), comment='颜色')
  scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
  formation = db.Column(Integer, comment='编组数')
  trainset_number = db.Column(String(12), comment='动车号（3-12位数字，前导0）')
  decoder_number = db.Column(String(4), comment='编号（1-4位数字，无前导0）')
  head_light = db.Column(Boolean, comment='头车灯（有/无）')
  interior_light = db.Column(String(50), comment='室内灯')
  chip_interface_id = db.Column(Integer, ForeignKey('chip_interface.id'), comment='关联芯片接口ID')
  chip_model_id = db.Column(Integer, ForeignKey('chip_model.id'), comment='关联芯片型号ID')
  price = db.Column(String(50), comment='价格表达式（如288+538）')
  total_price = db.Column(Float, comment='总价（自动计算）')
  item_number = db.Column(String(50), comment='货号')
  product_url = db.Column(String(1024), comment='产品地址')
  purchase_date = db.Column(Date, default=date.today, comment='购买日期')
  merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

  # 关系
  series = relationship('TrainsetSeries', backref='trainsets')
  power_type = relationship('PowerType', backref='trainsets')
  model = relationship('TrainsetModel', backref='trainsets')
  brand = relationship('Brand', backref='trainsets')
  depot = relationship('Depot', backref='trainsets')
  chip_interface = relationship('ChipInterface', backref='trainsets')
  chip_model = relationship('ChipModel', backref='trainsets')
  merchant = relationship('Merchant', backref='trainsets')

  def __repr__(self):
    return f'<Trainset {self.id}: {self.model.name} {self.scale}>'

class LocomotiveHead(db.Model):
  """先头车模型"""
  __tablename__ = 'locomotive_head'

  id = db.Column(Integer, primary_key=True, comment='主键')
  model_id = db.Column(Integer, ForeignKey('trainset_model.id'), comment='关联动车组车型ID')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
  special_color = db.Column(String(32), comment='特涂')
  scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
  head_light = db.Column(Boolean, comment='头车灯（有/无）')
  interior_light = db.Column(String(50), comment='室内灯')
  price = db.Column(String(50), comment='价格表达式（如288+538）')
  total_price = db.Column(Float, comment='总价（自动计算）')
  item_number = db.Column(String(50), comment='货号')
  product_url = db.Column(String(1024), comment='产品地址')
  purchase_date = db.Column(Date, default=date.today, comment='购买日期')
  merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

  # 关系
  model = relationship('TrainsetModel', backref='locomotive_heads')
  brand = relationship('Brand', backref='locomotive_heads')
  merchant = relationship('Merchant', backref='locomotive_heads')

  def __repr__(self):
    return f'<LocomotiveHead {self.id}: {self.model.name} {self.scale}>'

class ImportTemplate(db.Model):
  """自定义导入模板"""
  __tablename__ = 'import_template'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, comment='模板名称')
  config = db.Column(JSON, nullable=False, comment='映射配置')
  created_at = db.Column(DateTime, default=datetime.utcnow, comment='创建时间')
  updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

  def __repr__(self):
    return f'<ImportTemplate {self.id}: {self.name}>'
