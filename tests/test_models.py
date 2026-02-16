"""
模型测试
验证数据库模型的属性和关系
"""
import pytest
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, LocomotiveModel, TrainsetSeries, TrainsetModel, PowerType


class TestLocomotiveHeadModel:
    """先头车模型测试 - 确保 depot 字段已被移除"""

    def test_locomotive_head_has_no_depot(self, app, sample_data):
        """验证 LocomotiveHead 没有 depot 属性"""
        with app.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                special_color='测试涂装',
                scale='HO',
                head_light=True,
                interior_light='LED',
                price=100,
                total_price=100
            )
            db.session.add(head)
            db.session.commit()

            # 验证没有 depot 属性
            assert not hasattr(head, 'depot_id')
            assert not hasattr(head, 'depot')

            # 验证其他属性存在
            assert hasattr(head, 'special_color')
            assert hasattr(head, 'head_light')
            assert hasattr(head, 'interior_light')
            assert head.special_color == '测试涂装'

    def test_locomotive_head_crud(self, app, sample_data):
        """测试先头车 CRUD 操作"""
        with app.app_context():
            # Create
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                special_color='红色',
                scale='HO',
                head_light=True
            )
            db.session.add(head)
            db.session.commit()

            # Read
            saved = LocomotiveHead.query.first()
            assert saved is not None
            assert saved.special_color == '红色'

            # Update
            saved.special_color = '蓝色'
            db.session.commit()
            updated = LocomotiveHead.query.first()
            assert updated.special_color == '蓝色'

            # Delete
            db.session.delete(updated)
            db.session.commit()
            assert LocomotiveHead.query.count() == 0


class TestLocomotiveModel:
    """机车模型测试"""

    def test_locomotive_creation(self, app, sample_data):
        """测试机车创建"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='0001',
                decoder_number='1',
                price='100',
                total_price=100
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.first()
            assert saved.locomotive_number == '0001'
            assert saved.scale == 'HO'

    def test_locomotive_relationships(self, app, sample_data):
        """测试机车关系"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                depot_id=1,
                scale='HO'
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.first()
            assert saved.brand.name == '测试品牌'
            assert saved.series.name == 'SS系列'
            assert saved.depot.name == '测试机务段'


class TestTrainsetModel:
    """动车组模型测试"""

    def test_trainset_creation(self, app, sample_data):
        """测试动车组创建"""
        with app.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                trainset_number='0001',
                formation=8,
                head_light=True,
                color='白色'
            )
            db.session.add(trainset)
            db.session.commit()

            saved = Trainset.query.first()
            assert saved.trainset_number == '0001'
            assert saved.formation == 8


class TestBrandModel:
    """品牌模型测试"""

    def test_brand_creation(self, app):
        """测试品牌创建"""
        with app.app_context():
            brand = Brand(name='新品牌', search_url='http://example.com/{query}')
            db.session.add(brand)
            db.session.commit()

            saved = Brand.query.filter_by(name='新品牌').first()
            assert saved is not None
            assert saved.search_url == 'http://example.com/{query}'
