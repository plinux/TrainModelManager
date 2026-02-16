"""
数据验证测试
验证边界条件和异常数据处理
"""
import pytest
from models import db, Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel, PowerType


class TestLocomotiveValidation:
    """机车数据验证测试"""

    def test_locomotive_with_zero_price(self, app, sample_data):
        """测试价格为 0 的机车"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                price='0',
                total_price=0
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.first()
            assert saved.total_price == 0

    def test_locomotive_with_empty_string_fields(self, app, sample_data):
        """测试空字符串字段的机车"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='',  # 空字符串
                decoder_number='',     # 空字符串
                item_number=''         # 空字符串
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.first()
            assert saved.locomotive_number == ''
            assert saved.decoder_number == ''

    def test_locomotive_with_null_optional_fields(self, app, sample_data):
        """测试可选字段为 NULL"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                depot_id=None,
                chip_interface_id=None,
                chip_model_id=None,
                purchase_date=None,
                merchant_id=None
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.first()
            assert saved.depot_id is None
            assert saved.chip_interface_id is None

    def test_locomotive_price_expression(self, app, sample_data):
        """测试价格表达式计算"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                price='100+200',
                total_price=300
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.first()
            assert saved.price == '100+200'

    def test_locomotive_missing_required_field(self, app, sample_data):
        """测试缺少必填字段（scale 是必填的）"""
        with app.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1
                # 缺少 scale
            )
            db.session.add(loco)
            with pytest.raises(Exception):  # 应该抛出异常
                db.session.commit()
            db.session.rollback()


class TestTrainsetValidation:
    """动车组数据验证测试"""

    def test_trainset_with_zero_formation(self, app, sample_data):
        """测试编组为 0"""
        with app.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                formation=0
            )
            db.session.add(trainset)
            db.session.commit()

            saved = Trainset.query.first()
            assert saved.formation == 0

    def test_trainset_with_large_formation(self, app, sample_data):
        """测试大编组数"""
        with app.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                formation=16
            )
            db.session.add(trainset)
            db.session.commit()

            saved = Trainset.query.first()
            assert saved.formation == 16

    def test_trainset_with_empty_color(self, app, sample_data):
        """测试涂装为空字符串"""
        with app.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                color=''
            )
            db.session.add(trainset)
            db.session.commit()

            saved = Trainset.query.first()
            assert saved.color == ''


class TestLocomotiveHeadValidation:
    """先头车数据验证测试"""

    def test_locomotive_head_with_null_optional_fields(self, app, sample_data):
        """测试可选字段为 NULL"""
        with app.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO',
                special_color=None,
                interior_light=None,
                price=None,
                purchase_date=None
            )
            db.session.add(head)
            db.session.commit()

            saved = LocomotiveHead.query.first()
            assert saved.special_color is None
            assert saved.price is None


class TestCarriageValidation:
    """车厢数据验证测试"""

    def test_carriage_set_creation(self, app, sample_data):
        """测试车厢套装创建"""
        with app.app_context():
            carriage_set = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T1',
                total_price=500
            )
            db.session.add(carriage_set)
            db.session.commit()

            saved = CarriageSet.query.first()
            assert saved.train_number == 'T1'
            assert saved.total_price == 500

    def test_carriage_set_with_zero_price(self, app, sample_data):
        """测试总价为 0"""
        with app.app_context():
            carriage_set = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T0',
                total_price=0
            )
            db.session.add(carriage_set)
            db.session.commit()

            saved = CarriageSet.query.first()
            assert saved.total_price == 0


class TestBrandValidation:
    """品牌验证测试"""

    def test_brand_with_empty_name(self, app):
        """测试品牌名为空"""
        with app.app_context():
            brand = Brand(name='')
            db.session.add(brand)
            db.session.commit()

            saved = Brand.query.filter_by(name='').first()
            assert saved is not None

    def test_brand_with_search_url(self, app):
        """测试品牌搜索链接"""
        with app.app_context():
            brand = Brand(name='测试品牌URL', search_url='https://example.com/search?q={{query}}')
            db.session.add(brand)
            db.session.commit()

            saved = Brand.query.filter_by(name='测试品牌URL').first()
            assert saved.search_url == 'https://example.com/search?q={{query}}'

    def test_brand_duplicate_name(self, app):
        """测试品牌名重复"""
        with app.app_context():
            brand1 = Brand(name='重复品牌')
            db.session.add(brand1)
            db.session.commit()

            brand2 = Brand(name='重复品牌')
            db.session.add(brand2)
            # 根据数据库约束，可能允许重复或抛出异常
            # 这里测试是否能正常处理
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
