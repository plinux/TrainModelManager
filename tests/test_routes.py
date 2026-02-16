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
        """测试选项维护页面"""
        response = client.get('/options')
        assert response.status_code == 200
        assert '选项维护' in response.data.decode('utf-8')

    def test_system_page(self, client):
        """测试系统维护页面"""
        response = client.get('/system')
        assert response.status_code == 200
        assert '系统维护' in response.data.decode('utf-8')
        # 验证三个功能按钮
        assert '导出数据到 Excel' in response.data.decode('utf-8')
        assert '从 Excel 导入数据' in response.data.decode('utf-8')
        assert '重新初始化数据库' in response.data.decode('utf-8')


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
