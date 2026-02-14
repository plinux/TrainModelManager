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
