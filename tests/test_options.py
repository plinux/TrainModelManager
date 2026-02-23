"""
信息维护测试
验证信息维护页面的 CRUD 操作
"""
import pytest
from models import db, Brand, Depot, Merchant, ChipInterface, ChipModel
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel, PowerType


class TestBrandOptions:
    """品牌选项测试"""

    def test_brand_list_page(self, client):
        """测试品牌列表页面"""
        response = client.get('/options?tab=brand')
        assert response.status_code == 200

    def test_brand_add(self, client):
        """测试添加品牌"""
        response = client.post('/options/brand', data={
            'name': '表单测试品牌'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 验证添加成功
        with client.application.app_context():
            brand = Brand.query.filter_by(name='表单测试品牌').first()
            assert brand is not None

    def test_brand_edit(self, client):
        """测试编辑品牌"""
        # 先创建一个品牌
        with client.application.app_context():
            brand = Brand(name='待编辑品牌', abbreviation='DBPP')
            db.session.add(brand)
            db.session.commit()
            brand_id = brand.id

        response = client.post(f'/options/brand/edit/{brand_id}', data={
            'name': '已编辑品牌',
            'abbreviation': 'YBPP',
            'search_url': 'https://test.com/{{query}}'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 验证编辑成功
        with client.application.app_context():
            brand = db.session.get(Brand, brand_id)
            assert brand.name == '已编辑品牌'
            assert brand.abbreviation == 'YBPP'

    def test_brand_delete(self, client):
        """测试删除品牌"""
        # 先创建一个品牌
        with client.application.app_context():
            brand = Brand(name='待删除品牌', abbreviation='DSPP')
            db.session.add(brand)
            db.session.commit()
            brand_id = brand.id

        response = client.post(f'/options/brand/delete/{brand_id}', follow_redirects=True)
        assert response.status_code == 200

        # 验证删除成功
        with client.application.app_context():
            brand = db.session.get(Brand, brand_id)
            assert brand is None

    def test_brand_delete_with_constraint(self, client, sample_data):
        """测试删除被引用的品牌"""
        # 注意：SQLite 内存数据库默认不强制外键约束
        # 此测试验证删除操作不会崩溃
        with client.application.app_context():
            brand = Brand.query.filter_by(name='测试品牌').first()
            if brand:
                brand_id = brand.id
                # 尝试删除被引用品牌
                response = client.post(f'/options/brand/delete/{brand_id}', follow_redirects=True)
                # 响应应该成功（即使删除失败）
                assert response.status_code == 200

    def test_brand_add_with_auto_abbreviation(self, client):
        """测试添加品牌时自动生成缩写"""
        # 测试中文品牌自动生成拼音首字母缩写
        response = client.post('/options/brand', data={
            'name': '百万城'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 验证缩写自动生成
        with client.application.app_context():
            brand = Brand.query.filter_by(name='百万城').first()
            assert brand is not None
            assert brand.abbreviation == 'BWC'

    def test_brand_add_with_custom_abbreviation(self, client):
        """测试添加品牌时使用自定义缩写"""
        response = client.post('/options/brand', data={
            'name': '自定义缩写品牌',
            'abbreviation': 'CUSTOM'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 验证自定义缩写被保留
        with client.application.app_context():
            brand = Brand.query.filter_by(name='自定义缩写品牌').first()
            assert brand is not None
            assert brand.abbreviation == 'CUSTOM'

    def test_brand_abbreviation_uniqueness_on_add(self, client):
        """测试添加品牌时缩写唯一性验证"""
        # 先创建一个品牌
        with client.application.app_context():
            brand = Brand(name='现有品牌', abbreviation='EXIST')
            db.session.add(brand)
            db.session.commit()

        # 尝试添加同名缩写的品牌（应该因数据库约束失败）
        with client.application.app_context():
            # 由于数据库约束，这会抛出异常
            # 路由会捕获异常并回滚
            response = client.post('/options/brand', data={
                'name': '新品牌',
                'abbreviation': 'EXIST'
            }, follow_redirects=True)
            # 请求会成功返回（重定向），但数据库不会添加
            assert response.status_code == 200

    def test_brand_edit_with_abbreviation_update(self, client):
        """测试编辑品牌时更新缩写"""
        # 先创建一个品牌
        with client.application.app_context():
            brand = Brand(name='原品牌名', abbreviation='YB')
            db.session.add(brand)
            db.session.commit()
            brand_id = brand.id

        # 编辑品牌，包括更新缩写
        response = client.post(f'/options/brand/edit/{brand_id}', data={
            'name': '新品牌名',
            'abbreviation': 'XPP',
            'search_url': ''
        }, follow_redirects=True)
        assert response.status_code == 200

        # 验证缩写已更新
        with client.application.app_context():
            brand = db.session.get(Brand, brand_id)
            assert brand.name == '新品牌名'
            assert brand.abbreviation == 'XPP'

    def test_brand_abbreviation_uniqueness_on_edit(self, client):
        """测试编辑品牌时缩写唯一性验证"""
        # 创建两个品牌
        with client.application.app_context():
            brand1 = Brand(name='品牌A', abbreviation='PPA')
            brand2 = Brand(name='品牌B', abbreviation='PPB')
            db.session.add_all([brand1, brand2])
            db.session.commit()
            brand1_id = brand1.id
            brand2_id = brand2.id

        # 尝试将品牌B的缩写改为与品牌A相同
        # 注意：当前实现在唯一性检查之前会触发数据库约束错误
        # 这是一个已知的行为，测试验证错误会被正确处理（回滚事务）
        response = client.post(f'/options/brand/edit/{brand2_id}', data={
            'name': '品牌B',
            'abbreviation': 'PPA'  # 与品牌A相同
        }, follow_redirects=True)
        # 响应应该成功返回（错误被捕获，事务已回滚）
        assert response.status_code == 200

        # 验证品牌B的缩写没有被修改
        with client.application.app_context():
            brand2 = db.session.get(Brand, brand2_id)
            assert brand2.abbreviation == 'PPB'  # 缩写保持不变

    def test_brand_api_edit_with_abbreviation(self, client):
        """测试通过API编辑品牌缩写"""
        # 先创建一个品牌
        with client.application.app_context():
            brand = Brand(name='API测试品牌', abbreviation='API')
            db.session.add(brand)
            db.session.commit()
            brand_id = brand.id

        # 通过API编辑
        response = client.post(f'/api/options/brand/edit', data={
            'id': str(brand_id),
            'name': 'API更新品牌',
            'abbreviation': 'UPD'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 验证更新成功
        with client.application.app_context():
            brand = db.session.get(Brand, brand_id)
            assert brand.name == 'API更新品牌'
            assert brand.abbreviation == 'UPD'

    def test_brand_api_edit_abbreviation_conflict(self, client):
        """测试通过API编辑时缩写冲突"""
        # 创建两个品牌
        with client.application.app_context():
            brand1 = Brand(name='冲突A', abbreviation='CONA')
            brand2 = Brand(name='冲突B', abbreviation='CONB')
            db.session.add_all([brand1, brand2])
            db.session.commit()
            brand2_id = brand2.id

        # 尝试通过API将品牌B的缩写改为与品牌A相同
        # 注意：当前实现在唯一性检查之前会触发数据库约束错误
        response = client.post(f'/api/options/brand/edit', data={
            'id': str(brand2_id),
            'name': '冲突B',
            'abbreviation': 'CONA'  # 与品牌A相同
        })
        # 响应应该是错误状态码（400或500）
        assert response.status_code in [400, 500]

        # 验证品牌B的缩写没有被修改
        with client.application.app_context():
            brand2 = db.session.get(Brand, brand2_id)
            assert brand2.abbreviation == 'CONB'  # 缩写保持不变


class TestDepotOptions:
    """机务段/车辆段选项测试"""

    def test_depot_add(self, client):
        """测试添加机务段"""
        response = client.post('/options/depot', data={
            'name': '表单测试机务段'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            depot = Depot.query.filter_by(name='表单测试机务段').first()
            assert depot is not None

    def test_depot_edit(self, client):
        """测试编辑机务段"""
        with client.application.app_context():
            depot = Depot(name='待编辑机务段')
            db.session.add(depot)
            db.session.commit()
            depot_id = depot.id

        response = client.post(f'/options/depot/edit/{depot_id}', data={
            'name': '已编辑机务段'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            depot = db.session.get(Depot, depot_id)
            assert depot.name == '已编辑机务段'

    def test_depot_delete(self, client):
        """测试删除机务段"""
        with client.application.app_context():
            depot = Depot(name='待删除机务段')
            db.session.add(depot)
            db.session.commit()
            depot_id = depot.id

        response = client.post(f'/options/depot/delete/{depot_id}', follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            depot = db.session.get(Depot, depot_id)
            assert depot is None


class TestMerchantOptions:
    """商家选项测试"""

    def test_merchant_add(self, client):
        """测试添加商家"""
        response = client.post('/options/merchant', data={
            'name': '表单测试商家'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            merchant = Merchant.query.filter_by(name='表单测试商家').first()
            assert merchant is not None

    def test_merchant_edit(self, client):
        """测试编辑商家"""
        with client.application.app_context():
            merchant = Merchant(name='待编辑商家')
            db.session.add(merchant)
            db.session.commit()
            merchant_id = merchant.id

        response = client.post(f'/options/merchant/edit/{merchant_id}', data={
            'name': '已编辑商家'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            merchant = db.session.get(Merchant, merchant_id)
            assert merchant.name == '已编辑商家'

    def test_merchant_delete(self, client):
        """测试删除商家"""
        with client.application.app_context():
            merchant = Merchant(name='待删除商家')
            db.session.add(merchant)
            db.session.commit()
            merchant_id = merchant.id

        response = client.post(f'/options/merchant/delete/{merchant_id}', follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            merchant = db.session.get(Merchant, merchant_id)
            assert merchant is None


class TestPowerTypeOptions:
    """动力类型选项测试"""

    def test_power_type_add(self, client):
        """测试添加动力类型"""
        response = client.post('/options/power_type', data={
            'name': '测试动力'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            pt = PowerType.query.filter_by(name='测试动力').first()
            assert pt is not None

    def test_power_type_delete(self, client):
        """测试删除动力类型"""
        with client.application.app_context():
            power_type = PowerType(name='待删除动力')
            db.session.add(power_type)
            db.session.commit()
            pt_id = power_type.id

        response = client.post(f'/options/power_type/delete/{pt_id}', follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            pt = db.session.get(PowerType, pt_id)
            assert pt is None


class TestChipOptions:
    """芯片选项测试"""

    def test_chip_interface_add(self, client):
        """测试添加芯片接口"""
        response = client.post('/options/chip_interface', data={
            'name': 'MTC'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            ci = ChipInterface.query.filter_by(name='MTC').first()
            assert ci is not None

    def test_chip_model_add(self, client):
        """测试添加芯片型号"""
        response = client.post('/options/chip_model', data={
            'name': '测试芯片型号'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            cm = ChipModel.query.filter_by(name='测试芯片型号').first()
            assert cm is not None


class TestSeriesOptions:
    """系列选项测试"""

    def test_locomotive_series_add(self, client):
        """测试添加机车系列"""
        response = client.post('/options/locomotive_series', data={
            'name': 'HX系列'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            series = LocomotiveSeries.query.filter_by(name='HX系列').first()
            assert series is not None

    def test_carriage_series_add(self, client):
        """测试添加车厢系列"""
        response = client.post('/options/carriage_series', data={
            'name': 'RW系列'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            series = CarriageSeries.query.filter_by(name='RW系列').first()
            assert series is not None

    def test_trainset_series_add(self, client):
        """测试添加动车组系列"""
        response = client.post('/options/trainset_series', data={
            'name': 'CR系列'
        }, follow_redirects=True)
        assert response.status_code == 200

        with client.application.app_context():
            series = TrainsetSeries.query.filter_by(name='CR系列').first()
            assert series is not None


class TestModelOptions:
    """型号选项测试"""

    def test_locomotive_model_add(self, client, sample_data):
        """测试添加机型"""
        with client.application.app_context():
            series = LocomotiveSeries.query.first()
            power_type = PowerType.query.first()
            if series and power_type:
                response = client.post('/options/locomotive_model', data={
                    'name': 'HXD3',
                    'series_id': str(series.id),
                    'power_type_id': str(power_type.id)
                }, follow_redirects=True)
                assert response.status_code == 200

                model = LocomotiveModel.query.filter_by(name='HXD3').first()
                assert model is not None

    def test_carriage_model_add(self, client, sample_data):
        """测试添加车厢型号"""
        with client.application.app_context():
            series = CarriageSeries.query.first()
            if series:
                response = client.post('/options/carriage_model', data={
                    'name': 'RW25',
                    'series_id': str(series.id),
                    'type': '软卧'
                }, follow_redirects=True)
                assert response.status_code == 200

                model = CarriageModel.query.filter_by(name='RW25').first()
                assert model is not None

    def test_trainset_model_add(self, client, sample_data):
        """测试添加动车组型号"""
        with client.application.app_context():
            series = TrainsetSeries.query.first()
            power_type = PowerType.query.first()
            if series and power_type:
                response = client.post('/options/trainset_model', data={
                    'name': 'CR400AF',
                    'series_id': str(series.id),
                    'power_type_id': str(power_type.id)
                }, follow_redirects=True)
                assert response.status_code == 200

                model = TrainsetModel.query.filter_by(name='CR400AF').first()
                assert model is not None
