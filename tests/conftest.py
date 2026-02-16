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
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel, PowerType


@pytest.fixture
def app():
    """创建测试用的 Flask 应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

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
            brand = Brand(name='测试品牌')
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
            chip_model = ChipModel(name='ESU LokSound 5')
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

        return {
            'brand': brand
        }
