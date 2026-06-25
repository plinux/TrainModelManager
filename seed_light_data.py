"""
种子数据脚本：填充灯品牌、灯型号和适用车型关联

使用方法：
  python seed_light_data.py

灯数据逻辑抽取到 utils/seeders/light_seed.py（与 init_db.py 共用单一来源）。
本脚本额外负责清理旧灯数据后再重建。

注意：会先清空灯相关表。若灯型号被 CarriageItem/Trainset/LocomotiveHead 引用，
清空会让主表 light_model_id 悬空（SQLite 默认不强制 FK，MySQL 会报错）。
"""
from app import create_app
from models import (
  db, LightBrand, LightModel, LightModelCarriage,
  LightModelTrainset, LightModelBrandApplicability,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed():
  app = create_app()
  with app.app_context():
    print("清理旧灯数据...")
    LightModelBrandApplicability.query.delete()
    LightModelCarriage.query.delete()
    LightModelTrainset.query.delete()
    LightModel.query.delete()
    LightBrand.query.delete()
    db.session.commit()

    print("填充灯数据（来自 utils/seeders/light_seed.py）...")
    from utils.seeders.light_seed import seed_light_data
    seed_light_data()
    db.session.commit()

    print(f"\n种子数据完成!")
    print(f"  灯品牌: {LightBrand.query.count()} 个")
    print(f"  灯型号: {LightModel.query.count()} 个")
    print(f"  品牌级适用规则: {LightModelBrandApplicability.query.count()} 条")
    print(f"  车厢适用关联: {LightModelCarriage.query.count()} 条")


if __name__ == '__main__':
  seed()
