from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Float, Boolean, Date, ForeignKey, JSON, DateTime, UniqueConstraint, Table, Column
from sqlalchemy.orm import relationship
from datetime import date, datetime, timezone
import os

db = SQLAlchemy()

# 芯片型号-接口多对多关联表
chip_model_interface = Table(
  'chip_model_interface', db.metadata,
  Column('chip_model_id', Integer, ForeignKey('chip_model.id', ondelete='CASCADE'), primary_key=True),
  Column('chip_interface_id', Integer, ForeignKey('chip_interface.id', ondelete='CASCADE'), primary_key=True)
)

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
  abbreviation = db.Column(String(10), nullable=False, unique=True, comment='品牌缩写')
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
  interfaces = relationship('ChipInterface', secondary=chip_model_interface, backref='chip_models', lazy='joined')

  def __repr__(self):
    return f'<ChipModel {self.id}: {self.name}>'

class Merchant(db.Model):
  """购买商家（所有模型共享）"""
  __tablename__ = 'merchant'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='商家名称')
  website = db.Column(String(255), comment='网店地址')

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

  __table_args__ = (
    db.UniqueConstraint('scale', 'locomotive_number', name='uq_loco_scale_number'),
    db.UniqueConstraint('scale', 'decoder_number', name='uq_loco_scale_decoder'),
  )

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
  light_model_id = db.Column(Integer, ForeignKey('light_model.id'), comment='关联室内灯型号ID')

  __table_args__ = (
    db.UniqueConstraint('set_id', 'car_number', name='uq_carriage_item_car_number'),
  )

  # 关系
  model = relationship('CarriageModel', backref='items')
  light_model = relationship('LightModel', backref='carriage_items')

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
  light_model_id = db.Column(Integer, ForeignKey('light_model.id'), comment='关联室内灯型号ID')
  chip_interface_id = db.Column(Integer, ForeignKey('chip_interface.id'), comment='关联芯片接口ID')
  chip_model_id = db.Column(Integer, ForeignKey('chip_model.id'), comment='关联芯片型号ID')
  price = db.Column(String(50), comment='价格表达式（如288+538）')
  total_price = db.Column(Float, comment='总价（自动计算）')
  item_number = db.Column(String(50), comment='货号')
  product_url = db.Column(String(1024), comment='产品地址')
  purchase_date = db.Column(Date, default=date.today, comment='购买日期')
  merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

  __table_args__ = (
    db.UniqueConstraint('scale', 'trainset_number', name='uq_trainset_scale_number'),
  )

  # 关系
  series = relationship('TrainsetSeries', backref='trainsets')
  power_type = relationship('PowerType', backref='trainsets')
  model = relationship('TrainsetModel', backref='trainsets')
  brand = relationship('Brand', backref='trainsets')
  depot = relationship('Depot', backref='trainsets')
  chip_interface = relationship('ChipInterface', backref='trainsets')
  chip_model = relationship('ChipModel', backref='trainsets')
  merchant = relationship('Merchant', backref='trainsets')
  light_model = relationship('LightModel', backref='trainsets')

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
  light_model_id = db.Column(Integer, ForeignKey('light_model.id'), comment='关联室内灯型号ID')
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
  light_model = relationship('LightModel', backref='locomotive_heads')

  def __repr__(self):
    return f'<LocomotiveHead {self.id}: {self.model.name} {self.scale}>'

class ImportTemplate(db.Model):
  """自定义导入模板"""
  __tablename__ = 'import_template'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, comment='模板名称')
  config = db.Column(JSON, nullable=False, comment='映射配置')
  created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), comment='创建时间')
  updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='更新时间')

  def __repr__(self):
    return f'<ImportTemplate {self.id}: {self.name}>'


class ModelFile(db.Model):
  """模型文件跟踪表"""
  __tablename__ = 'model_file'

  id = db.Column(Integer, primary_key=True, comment='主键')
  model_type = db.Column(String(20), nullable=False, comment='模型类型：locomotive/carriage/trainset/locomotive_head')
  model_id = db.Column(Integer, nullable=False, comment='关联模型ID')
  file_type = db.Column(String(20), nullable=False, comment='文件类型：image/manual/function_table')
  file_path = db.Column(String(255), nullable=False, comment='相对路径（相对于 DATA_DIR）')
  original_filename = db.Column(String(255), nullable=False, comment='原始文件名')
  file_size = db.Column(Integer, comment='文件大小（字节）')
  mime_type = db.Column(String(100), comment='MIME 类型')
  uploaded_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), comment='上传时间')

  def __repr__(self):
    return f'<ModelFile {self.id}: {self.model_type}/{self.model_id} - {self.file_type}>'

  def to_dict(self):
    """转换为字典"""
    # 从 file_path 中提取实际存储的文件名
    stored_filename = os.path.basename(self.file_path) if self.file_path else self.original_filename
    return {
      'id': self.id,
      'model_type': self.model_type,
      'model_id': self.model_id,
      'file_type': self.file_type,
      'file_path': self.file_path,
      'original_filename': self.original_filename,
      'stored_filename': stored_filename,
      'file_size': self.file_size,
      'mime_type': self.mime_type,
      'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
    }


class FunctionKey(db.Model):
  """数码功能表解析结果 - 存储 F0~F31 功能键映射"""
  __tablename__ = 'function_key'

  id = db.Column(Integer, primary_key=True, comment='主键')
  model_type = db.Column(String(20), nullable=False, comment='模型类型: locomotive/trainset')
  model_id = db.Column(Integer, nullable=False, comment='关联模型ID')
  key_number = db.Column(Integer, nullable=False, comment='功能键号: 0-31')
  function_name = db.Column(String(200), comment='功能名称')
  description = db.Column(String(500), nullable=True, comment='功能说明(第三列,可选)')
  source_file_id = db.Column(Integer, nullable=True, comment='关联 ModelFile.id')
  created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
  updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

  __table_args__ = (
    db.UniqueConstraint('model_type', 'model_id', 'key_number', name='uq_function_key_model'),
  )

  def to_dict(self):
    """转换为字典"""
    return {
      'id': self.id,
      'model_type': self.model_type,
      'model_id': self.model_id,
      'key_number': self.key_number,
      'function_name': self.function_name or '',
      'description': self.description or '',
      'source_file_id': self.source_file_id,
    }

  def __repr__(self):
    return f'<FunctionKey {self.model_type}:{self.model_id} F{self.key_number}={self.function_name}>'


class LightBrand(db.Model):
  """室内灯品牌"""
  __tablename__ = 'light_brand'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(8), nullable=False, unique=True, comment='品牌名称(最多8字符)')

  # 关系
  light_models = relationship('LightModel', backref='light_brand', cascade='all, delete-orphan')

  def __repr__(self):
    return f'<LightBrand {self.id}: {self.name}>'


class LightModel(db.Model):
  """室内灯型号"""
  __tablename__ = 'light_model'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(32), nullable=False, comment='型号名称(最多32字符)')
  color_temperature = db.Column(String(10), nullable=False, comment='色温: 3000K/4000K/5000K')
  scale = db.Column(String(2), nullable=False, default='HO', comment='比例：HO/N')
  light_brand_id = db.Column(Integer, ForeignKey('light_brand.id'), nullable=False, comment='关联灯品牌ID')

  # 关系
  carriage_applicabilities = relationship('LightModelCarriage', backref='light_model', cascade='all, delete-orphan')
  trainset_applicabilities = relationship('LightModelTrainset', backref='light_model', cascade='all, delete-orphan')
  brand_applicabilities = relationship('LightModelBrandApplicability', backref='light_model', cascade='all, delete-orphan')

  def __repr__(self):
    return f'<LightModel {self.id}: {self.name} ({self.color_temperature})>'


class LightModelCarriage(db.Model):
  """灯光型号 ↔ 车厢车型 + 品牌（车型级规则）"""
  __tablename__ = 'light_model_carriage'

  light_model_id = db.Column(Integer, ForeignKey('light_model.id'), primary_key=True, comment='关联灯型号ID')
  carriage_model_id = db.Column(Integer, ForeignKey('carriage_model.id'), primary_key=True, comment='关联车厢车型ID')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), primary_key=True, comment='关联品牌ID')

  # 关系
  carriage_model = relationship('CarriageModel')
  brand = relationship('Brand')

  def __repr__(self):
    return f'<LightModelCarriage light_model={self.light_model_id} carriage={self.carriage_model_id} brand={self.brand_id}>'


class LightModelTrainset(db.Model):
  """灯光型号 ↔ 动车组车型 + 品牌（车型级规则）"""
  __tablename__ = 'light_model_trainset'

  light_model_id = db.Column(Integer, ForeignKey('light_model.id'), primary_key=True, comment='关联灯型号ID')
  trainset_model_id = db.Column(Integer, ForeignKey('trainset_model.id'), primary_key=True, comment='关联动车组车型ID')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), primary_key=True, comment='关联品牌ID')

  # 关系
  trainset_model = relationship('TrainsetModel')
  brand = relationship('Brand')

  def __repr__(self):
    return f'<LightModelTrainset light_model={self.light_model_id} trainset={self.trainset_model_id} brand={self.brand_id}>'


class LightModelBrandApplicability(db.Model):
  """灯型号品牌级适用规则：适用于该品牌所有指定类型车型（含未来新增）"""
  __tablename__ = 'light_model_brand_applicability'

  id = db.Column(Integer, primary_key=True, comment='主键')
  light_model_id = db.Column(Integer, ForeignKey('light_model.id'), nullable=False, comment='关联灯型号ID')
  brand_id = db.Column(Integer, ForeignKey('brand.id'), nullable=False, comment='关联品牌ID')
  vehicle_type = db.Column(String(10), nullable=False, default='all', comment='适用车型类型: carriage/trainset/all')

  # 唯一约束：同一灯型号对同一品牌+类型不应重复
  __table_args__ = (
    db.UniqueConstraint('light_model_id', 'brand_id', 'vehicle_type', name='uq_light_brand_app'),
  )

  # 关系
  brand = relationship('Brand')

  def __repr__(self):
    return f'<LightModelBrandApplicability light_model={self.light_model_id} brand={self.brand_id} type={self.vehicle_type}>'
