"""
数据库完整性测试：唯一约束兜底（P2-1）

验证应用层校验被绕过时（如并发、直接 ORM 插入），DB 层 UniqueConstraint 仍能拦截。
"""
import pytest
from sqlalchemy.exc import IntegrityError
from models import Locomotive, db


class TestUniqueConstraints:
  def test_locomotive_scale_number_duplicate_rejected(self, app):
    """同比例内重复机车号必须被 DB 约束拒绝"""
    with app.app_context():
      db.session.add(Locomotive(scale='HO', locomotive_number='1234'))
      db.session.add(Locomotive(scale='HO', locomotive_number='1234'))
      with pytest.raises(IntegrityError):
        db.session.commit()
      db.session.rollback()

  def test_locomotive_number_allowed_across_scales(self, app):
    """不同比例下相同机车号允许（约束是 scale + number 组合）"""
    with app.app_context():
      db.session.add(Locomotive(scale='HO', locomotive_number='1234'))
      db.session.add(Locomotive(scale='N', locomotive_number='1234'))
      db.session.commit()  # 不应抛错


class TestSeedLightData:
  """灯种子数据（P2-3 单一来源）"""

  def test_seed_creates_brands_and_models(self, app):
    from utils.seeders.light_seed import seed_light_data
    from models import (LightBrand, LightModel, Brand, CarriageSeries,
                        CarriageModel, db)
    with app.app_context():
      # 前置数据：seed_light_data 依赖 Brand 与 CarriageModel
      db.session.add(Brand(name='KATO', abbreviation='KATO'))
      db.session.add(Brand(name='PIKO', abbreviation='PIKO'))
      series = CarriageSeries(name='test')
      db.session.add(series)
      db.session.commit()
      db.session.add(CarriageModel(name='YZ22', series_id=series.id, type='客车'))
      db.session.commit()

      seed_light_data()
      db.session.commit()

      assert LightBrand.query.count() == 7
      assert LightModel.query.count() == 31
