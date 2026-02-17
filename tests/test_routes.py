"""
路由测试
验证页面路由和表单提交
"""
import pytest


class TestPageRoutes:
    """页面路由测试"""

    def test_home_page(self, client):
        """测试首页"""
        response = client.get('/')
        assert response.status_code == 200
        assert '火车模型管理系统' in response.data.decode('utf-8')

    def test_locomotive_page(self, client):
        """测试机车模型页面"""
        response = client.get('/locomotive')
        assert response.status_code == 200
        assert '机车模型' in response.data.decode('utf-8')

    def test_trainset_page(self, client):
        """测试动车组模型页面"""
        response = client.get('/trainset')
        assert response.status_code == 200
        assert '动车组模型' in response.data.decode('utf-8')

    def test_locomotive_head_page(self, client):
        """测试先头车模型页面"""
        response = client.get('/locomotive-head')
        assert response.status_code == 200
        assert '先头车模型' in response.data.decode('utf-8')

    def test_carriage_page(self, client):
        """测试车厢模型页面"""
        response = client.get('/carriage')
        assert response.status_code == 200
        assert '车厢模型' in response.data.decode('utf-8')

    def test_options_page(self, client):
        """测试信息维护页面"""
        response = client.get('/options')
        assert response.status_code == 200
        assert '信息维护' in response.data.decode('utf-8')

    def test_system_page(self, client):
        """测试系统维护页面"""
        response = client.get('/system')
        assert response.status_code == 200
        assert '系统维护' in response.data.decode('utf-8')
        # 验证导出按钮（三种模式）
        assert '导出模型数据' in response.data.decode('utf-8')
        assert '导出系统信息' in response.data.decode('utf-8')
        assert '全部导出' in response.data.decode('utf-8')
        # 验证导入和初始化按钮
        assert '从 Excel 导入数据' in response.data.decode('utf-8')
        assert '重新初始化数据库' in response.data.decode('utf-8')


class TestCopyButtons:
    """复制按钮测试 - 验证各模型页面都有复制按钮"""

    def test_locomotive_copy_button(self, client, sample_data):
        """测试机车页面有复制按钮"""
        from models import db, Locomotive

        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='COPY001'
            )
            db.session.add(loco)
            db.session.commit()

        response = client.get('/locomotive')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '复制' in html
        assert 'copyLocomotive' in html

    def test_trainset_copy_button(self, client, sample_data):
        """测试动车组页面有复制按钮"""
        from models import db, Trainset

        with client.application.app_context():
            trainset = Trainset(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                trainset_number='COPY001'
            )
            db.session.add(trainset)
            db.session.commit()

        response = client.get('/trainset')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '复制' in html
        assert 'copyTrainset' in html

    def test_locomotive_head_copy_button(self, client, sample_data):
        """测试先头车页面有复制按钮"""
        from models import db, LocomotiveHead

        with client.application.app_context():
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO'
            )
            db.session.add(head)
            db.session.commit()

        response = client.get('/locomotive-head')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '复制' in html
        assert 'copyLocomotiveHead' in html

    def test_carriage_copy_button(self, client, sample_data):
        """测试车厢页面有复制按钮"""
        from models import db, CarriageSet

        with client.application.app_context():
            carriage = CarriageSet(
                brand_id=1,
                series_id=1,
                scale='HO',
                train_number='COPY001'
            )
            db.session.add(carriage)
            db.session.commit()

        response = client.get('/carriage')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '复制' in html
        assert 'copyCarriage' in html

    def test_locomotive_copy_data_attributes(self, client, sample_data):
        """测试机车表格行包含复制所需的 data 属性"""
        from models import db, Locomotive

        with client.application.app_context():
            loco = Locomotive(
                series_id=1,
                power_type_id=1,
                model_id=1,
                brand_id=1,
                scale='HO',
                locomotive_number='DATA001',
                decoder_number='01',
                plaque='测试挂牌',
                price='100',
                item_number='ITEM001'
            )
            db.session.add(loco)
            db.session.commit()

        response = client.get('/locomotive')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # 验证关键 data 属性存在（ID 和名称属性）
        assert 'data-model_id=' in html
        assert 'data-model=' in html
        assert 'data-series_id=' in html
        assert 'data-series=' in html
        assert 'data-brand_id=' in html
        assert 'data-brand=' in html
        assert 'data-item_number=' in html
        assert 'data-purchase_date=' in html


class TestLocomotiveHeadRoutes:
    """先头车路由测试 - 验证 depot 已被移除"""

    def test_locomotive_head_edit_page_no_depot(self, client, sample_data):
        """测试先头车编辑页面不包含动车段字段"""
        from models import db, LocomotiveHead

        with client.application.app_context():
            # 创建一个先头车
            head = LocomotiveHead(
                model_id=1,
                brand_id=1,
                scale='HO',
                head_light=True
            )
            db.session.add(head)
            db.session.commit()
            head_id = head.id

        response = client.get(f'/locomotive-head/edit/{head_id}')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # 确保页面不包含动车段
        assert 'depot_id' not in html
        assert '动车段' not in html

    def test_locomotive_head_list_no_depot_column(self, client):
        """测试先头车列表页面不包含动车段列"""
        response = client.get('/locomotive-head')
        assert response.status_code == 200
        html = response.data.decode('utf-8').lower()
        # 表头不应包含动车段
        assert 'depot' not in html


class TestLocomotiveCRUD:
    """机车 CRUD 测试"""

    def test_locomotive_add_page(self, client):
        """测试机车添加页面"""
        response = client.get('/locomotive')
        assert response.status_code == 200
        # 检查表单字段
        assert b'model_id' in response.data
        assert b'brand_id' in response.data


class TestTrainsetCRUD:
    """动车组 CRUD 测试"""

    def test_trainset_add_page(self, client):
        """测试动车组添加页面"""
        response = client.get('/trainset')
        assert response.status_code == 200
        # 检查表单字段
        assert b'model_id' in response.data
        assert b'formation' in response.data  # 编组
