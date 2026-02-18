"""
CRUD 完整测试
验证所有模型类型的增删改查操作
"""
import pytest
from models import db, Locomotive, CarriageSet, CarriageItem, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel, TrainsetSeries, TrainsetModel, PowerType


class TestLocomotiveCRUD:
    """机车 CRUD 完整测试"""

    def test_locomotive_create(self, client, sample_data):
        """测试机车创建"""
        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                depot_id=1,
                scale='HO',
                locomotive_number='1234',
                decoder_number='01',
                price='500',
                total_price=500,
                item_number='ITEM001'
            )
            db.session.add(loco)
            db.session.commit()

            saved = Locomotive.query.filter_by(locomotive_number='1234').first()
            assert saved is not None
            assert saved.price == '500'

    def test_locomotive_read(self, client, sample_data):
        """测试机车读取"""
        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='READ001'
            )
            db.session.add(loco)
            db.session.commit()

            # 通过 API 读取
            response = client.get('/locomotive')
            assert response.status_code == 200
            assert 'READ001' in response.data.decode('utf-8')

    def test_locomotive_update(self, client, sample_data):
        """测试机车更新"""
        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='UPDATE001',
                price='100'
            )
            db.session.add(loco)
            db.session.commit()
            loco_id = loco.id

            # 更新
            saved = db.session.get(Locomotive,loco_id)
            saved.price = '200'
            saved.locomotive_number = 'UPDATED'
            db.session.commit()

            updated = db.session.get(Locomotive,loco_id)
            assert updated.price == '200'
            assert updated.locomotive_number == 'UPDATED'

    def test_locomotive_delete(self, client, sample_data):
        """测试机车删除"""
        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='DELETE001'
            )
            db.session.add(loco)
            db.session.commit()
            loco_id = loco.id

            # 删除
            saved = db.session.get(Locomotive,loco_id)
            db.session.delete(saved)
            db.session.commit()

            # 验证已删除
            deleted = db.session.get(Locomotive,loco_id)
            assert deleted is None

    def test_locomotive_delete_via_api(self, client, sample_data):
        """测试通过 API 删除机车"""
        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='API_DELETE'
            )
            db.session.add(loco)
            db.session.commit()
            loco_id = loco.id

        response = client.post(f'/locomotive/delete/{loco_id}', follow_redirects=True)
        # 删除成功后重定向到列表页
        assert response.status_code == 200

        # 验证已删除
        with client.application.app_context():
            deleted = db.session.get(Locomotive, loco_id)
            assert deleted is None


class TestTrainsetCRUD:
    """动车组 CRUD 完整测试"""

    def test_trainset_create(self, client, sample_data):
        """测试动车组创建"""
        with client.application.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                trainset_number='CRH001',
                formation=8,
                head_light=True,
                interior_light='LED',
                color='白色'
            )
            db.session.add(trainset)
            db.session.commit()

            saved = Trainset.query.filter_by(trainset_number='CRH001').first()
            assert saved is not None
            assert saved.formation == 8

    def test_trainset_update(self, client, sample_data):
        """测试动车组更新"""
        with client.application.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                trainset_number='UPDATE_TS',
                formation=8
            )
            db.session.add(trainset)
            db.session.commit()
            ts_id = trainset.id

            # 更新编组
            saved = db.session.get(Trainset,ts_id)
            saved.formation = 16
            saved.color = '绿色'
            db.session.commit()

            updated = db.session.get(Trainset,ts_id)
            assert updated.formation == 16
            assert updated.color == '绿色'

    def test_trainset_delete(self, client, sample_data):
        """测试动车组删除"""
        with client.application.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                trainset_number='DELETE_TS'
            )
            db.session.add(trainset)
            db.session.commit()
            ts_id = trainset.id

            saved = db.session.get(Trainset,ts_id)
            db.session.delete(saved)
            db.session.commit()

            deleted = db.session.get(Trainset,ts_id)
            assert deleted is None

    def test_trainset_delete_via_api(self, client, sample_data):
        """测试通过 API 删除动车组"""
        with client.application.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                trainset_number='API_DEL_TS'
            )
            db.session.add(trainset)
            db.session.commit()
            ts_id = trainset.id

        response = client.post(f'/trainset/delete/{ts_id}', follow_redirects=True)
        # 删除成功后重定向到列表页
        assert response.status_code == 200

        # 验证已删除
        with client.application.app_context():
            deleted = db.session.get(Trainset, ts_id)
            assert deleted is None


class TestLocomotiveHeadCRUD:
    """先头车 CRUD 完整测试"""

    def test_locomotive_head_create(self, client, sample_data):
        """测试先头车创建"""
        with client.application.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO',
                head_light=True,
                interior_light='LED',
                special_color='红色'
            )
            db.session.add(head)
            db.session.commit()

            saved = LocomotiveHead.query.first()
            assert saved is not None
            assert saved.special_color == '红色'

    def test_locomotive_head_update(self, client, sample_data):
        """测试先头车更新"""
        with client.application.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO',
                special_color='红色'
            )
            db.session.add(head)
            db.session.commit()
            head_id = head.id

            saved = db.session.get(LocomotiveHead,head_id)
            saved.special_color = '蓝色'
            db.session.commit()

            updated = db.session.get(LocomotiveHead,head_id)
            assert updated.special_color == '蓝色'

    def test_locomotive_head_delete(self, client, sample_data):
        """测试先头车删除"""
        with client.application.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO'
            )
            db.session.add(head)
            db.session.commit()
            head_id = head.id

            saved = db.session.get(LocomotiveHead,head_id)
            db.session.delete(saved)
            db.session.commit()

            deleted = db.session.get(LocomotiveHead,head_id)
            assert deleted is None

    def test_locomotive_head_delete_via_api(self, client, sample_data):
        """测试通过 API 删除先头车"""
        with client.application.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO'
            )
            db.session.add(head)
            db.session.commit()
            head_id = head.id

        response = client.post(f'/locomotive-head/delete/{head_id}', follow_redirects=True)
        # 删除成功后重定向到列表页
        assert response.status_code == 200

        # 验证已删除
        with client.application.app_context():
            deleted = db.session.get(LocomotiveHead, head_id)
            assert deleted is None


class TestCarriageCRUD:
    """车厢 CRUD 完整测试"""

    def test_carriage_set_create(self, client, sample_data):
        """测试车厢套装创建"""
        with client.application.app_context():
            carriage = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T1',
                total_price=500
            )
            db.session.add(carriage)
            db.session.commit()

            saved = CarriageSet.query.first()
            assert saved is not None
            assert saved.total_price == 500
            assert saved.train_number == 'T1'

    def test_carriage_set_update(self, client, sample_data):
        """测试车厢套装更新"""
        with client.application.app_context():
            carriage = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T1',
                total_price=500
            )
            db.session.add(carriage)
            db.session.commit()
            c_id = carriage.id

            saved = db.session.get(CarriageSet,c_id)
            saved.total_price = 600
            saved.train_number = 'T2'
            db.session.commit()

            updated = db.session.get(CarriageSet,c_id)
            assert updated.total_price == 600
            assert updated.train_number == 'T2'

    def test_carriage_set_delete(self, client, sample_data):
        """测试车厢套装删除"""
        with client.application.app_context():
            carriage = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T_DELETE'
            )
            db.session.add(carriage)
            db.session.commit()
            c_id = carriage.id

            saved = db.session.get(CarriageSet,c_id)
            db.session.delete(saved)
            db.session.commit()

            deleted = db.session.get(CarriageSet,c_id)
            assert deleted is None

    def test_carriage_set_delete_via_api(self, client, sample_data):
        """测试通过 API 删除车厢套装"""
        with client.application.app_context():
            carriage = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T_API_DEL'
            )
            db.session.add(carriage)
            db.session.commit()
            c_id = carriage.id

        response = client.post(f'/carriage/delete/{c_id}', follow_redirects=True)
        # 删除成功后重定向到列表页
        assert response.status_code == 200

        # 验证已删除
        with client.application.app_context():
            deleted = db.session.get(CarriageSet, c_id)
            assert deleted is None

    def test_carriage_item_create(self, client, sample_data):
        """测试车厢项创建"""
        with client.application.app_context():
            # 先创建套装
            carriage_set = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='T_ITEM'
            )
            db.session.add(carriage_set)
            db.session.commit()
            set_id = carriage_set.id

            # 创建车厢项
            item = CarriageItem(
                set_id=set_id,
                model_id=1,
                car_number='01',
                color='绿色',
                lighting='LED'
            )
            db.session.add(item)
            db.session.commit()

            saved = CarriageItem.query.filter_by(set_id=set_id).first()
            assert saved is not None
            assert saved.car_number == '01'
