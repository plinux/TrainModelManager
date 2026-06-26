"""
导入辅助函数（P3-1：从 routes/api.py 抽出）

外键解析、唯一性冲突检查、芯片接口关联、按名查 ID 等导入辅助逻辑。
"""
from models import (
  db, Brand, Depot, Merchant, PowerType,
  ChipInterface, ChipModel,
  LocomotiveSeries, CarriageSeries, TrainsetSeries,
  LocomotiveModel, CarriageModel, TrainsetModel,
  LightBrand, LightModel,
)

# 外键引用模型映射
FK_REFERENCE_MAP = {
  'brand': Brand,
  'depot': Depot,
  'merchant': Merchant,
  'power_type': PowerType,
  'chip_interface': ChipInterface,
  'chip_model': ChipModel,
  'locomotive_series': LocomotiveSeries,
  'carriage_series': CarriageSeries,
  'trainset_series': TrainsetSeries,
  'locomotive_model': LocomotiveModel,
  'carriage_model': CarriageModel,
  'trainset_model': TrainsetModel,
  'light_brand': LightBrand,
  'light_model': LightModel,
}


def find_id_by_name(model, name, custom_query=None):
  """根据名称查找模型的ID（大小写不敏感）"""
  if not name:
    return None
  if custom_query:
    result = custom_query(model.query)
    return result.id if result else None
  obj = model.query.filter(db.func.lower(model.name) == db.func.lower(name)).first()
  return obj.id if obj else None


def resolve_foreign_key(ref_table, value):
  """解析外键引用，将名称转换为 ID（大小写不敏感）"""
  if not value:
    return None
  model_class = FK_REFERENCE_MAP.get(ref_table)
  if not model_class:
    return None
  obj = model_class.query.filter(
    db.func.lower(model_class.name) == db.func.lower(value)
  ).first()
  return obj.id if obj else None


def check_unique_conflict(model_class, field_name, value, scale=None):
  """检查唯一约束冲突（大小写不敏感）"""
  if not value:
    return None
  field_attr = getattr(model_class, field_name)
  if scale:
    return model_class.query.filter(
      model_class.scale == scale,
      db.func.lower(field_attr) == db.func.lower(value)
    ).first()
  return model_class.query.filter(
    db.func.lower(field_attr) == db.func.lower(value)
  ).first()


def _update_chip_model_interfaces(chip_model_instance, interface_names_raw):
  """更新芯片型号与接口的关联（逗号分隔的接口名）"""
  chip_model_instance.interfaces = []
  if not interface_names_raw:
    return
  names = [n.strip() for n in str(interface_names_raw).split(',') if n.strip()]
  for iface_name in names:
    iface = ChipInterface.query.filter(
      db.func.lower(ChipInterface.name) == iface_name.lower()
    ).first()
    if iface:
      chip_model_instance.interfaces.append(iface)
