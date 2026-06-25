"""
Pytest 配置文件
提供测试用的 fixtures
"""
import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import TestConfig
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel, PowerType
from models import LightBrand, LightModel, LightModelCarriage, LightModelTrainset, LightModelBrandApplicability


@pytest.fixture
def app():
    """创建测试用的 Flask 应用"""
    # 使用 TestConfig 确保在 db.init_app() 之前设置正确的数据库 URI
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def sample_data(app):
    """创建示例数据"""
    with app.app_context():
        # 检查是否已有数据，避免重复创建
        brand = Brand.query.filter_by(name='测试品牌').first()
        if not brand:
            brand = Brand(name='测试品牌', abbreviation='CSP')
            db.session.add(brand)

            depot = Depot(name='测试机务段')
            db.session.add(depot)

            merchant = Merchant(name='测试商家')
            db.session.add(merchant)

            power_type = PowerType(name='电力')
            db.session.add(power_type)

            # 机车系列和型号
            loco_series = LocomotiveSeries(name='SS系列')
            db.session.add(loco_series)

            # 车厢系列和型号
            carriage_series = CarriageSeries(name='YZ系列')
            db.session.add(carriage_series)

            # 动车组系列和型号
            trainset_series = TrainsetSeries(name='CRH系列')
            db.session.add(trainset_series)

            # 芯片
            chip_interface = ChipInterface(name='Next18')
            db.session.add(chip_interface)
            chip_interface2 = ChipInterface(name='PluX22')
            db.session.add(chip_interface2)
            chip_model = ChipModel(name='ESU LokSound 5')
            chip_model.interfaces.append(chip_interface)
            chip_model.interfaces.append(chip_interface2)
            db.session.add(chip_model)

            db.session.commit()

            # 创建型号（需要系列和动力类型先提交）
            loco_model = LocomotiveModel(name='SS4', series_id=1, power_type_id=1)
            db.session.add(loco_model)
            carriage_model = CarriageModel(name='YZ22', series_id=1, type='客车')
            db.session.add(carriage_model)
            trainset_model = TrainsetModel(name='CRH380A', series_id=1, power_type_id=1)
            db.session.add(trainset_model)

            db.session.commit()

            # 灯品牌和灯型号
            light_brand = LightBrand(name='测试灯品牌')
            db.session.add(light_brand)

            db.session.commit()

            light_model1 = LightModel(
                name='TEST-LED-3000K',
                color_temperature='3000K',
                scale='HO',
                light_brand_id=light_brand.id
            )
            light_model2 = LightModel(
                name='TEST-LED-5000K',
                color_temperature='5000K',
                scale='N',
                light_brand_id=light_brand.id
            )
            db.session.add(light_model1)
            db.session.add(light_model2)

            db.session.commit()

            # 灯型号适用车型关联
            # 车厢车型(carriage_model id=1) + 品牌(brand id=1) → 灯型号1
            lmc = LightModelCarriage(
                light_model_id=light_model1.id,
                carriage_model_id=carriage_model.id,
                brand_id=brand.id
            )
            db.session.add(lmc)

            # 动车组车型(trainset_model id=1) + 品牌(brand id=1) → 灯型号2
            lmt = LightModelTrainset(
                light_model_id=light_model2.id,
                trainset_model_id=trainset_model.id,
                brand_id=brand.id
            )
            db.session.add(lmt)

            # 品牌级规则：灯型号2 适用于测试品牌所有车型
            brand_app = LightModelBrandApplicability(
                light_model_id=light_model2.id,
                brand_id=brand.id,
                vehicle_type='all'
            )
            db.session.add(brand_app)

            db.session.commit()

        return {
            'brand': brand
        }
