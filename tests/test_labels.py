"""
表单标签测试
验证页面中的标签文字是否正确
"""
import pytest


class TestFormLabels:
    """表单标签测试"""

    def test_locomotive_form_labels(self, client, sample_data):
        """测试机车表单标签"""
        response = client.get('/locomotive')
        assert response.status_code == 200

        # 动力（不是动力类型）
        assert b'\xe5\x8a\xa8\xe5\x8a\x9b' in response.data  # 动力
        # 不应包含 "动力类型"
        assert '动力类型' not in response.data.decode('utf-8')

    def test_trainset_form_labels(self, client, sample_data):
        """测试动车组表单标签"""
        response = client.get('/trainset')
        assert response.status_code == 200

        # 涂装（不是颜色）
        html = response.data.decode('utf-8')
        assert '涂装' in html
        # 颜色应该被改为涂装
        # 注意：字段名仍是 color，但标签是涂装

    def test_locomotive_head_form_labels(self, client, sample_data):
        """测试先头车表单标签"""
        response = client.get('/locomotive-head')
        assert response.status_code == 200

        html = response.data.decode('utf-8')
        # 涂装（不是特涂）
        assert '涂装' in html
        # 不应包含 "特涂"
        assert '特涂' not in html
        # 不应包含 "动车段"
        assert '动车段' not in html

    def test_carriage_form_price_placeholder(self, client, sample_data):
        """测试车厢总价占位符"""
        response = client.get('/carriage')
        assert response.status_code == 200

        html = response.data.decode('utf-8')
        assert '不支持表达式计算' in html

    def test_locomotive_form_price_placeholder(self, client, sample_data):
        """测试机车价格占位符"""
        response = client.get('/locomotive')
        assert response.status_code == 200

        html = response.data.decode('utf-8')
        assert '支持表达式计算' in html

    def test_trainset_form_price_placeholder(self, client, sample_data):
        """测试动车组价格占位符"""
        response = client.get('/trainset')
        assert response.status_code == 200

        html = response.data.decode('utf-8')
        assert '支持表达式计算' in html


class TestOptionsLabels:
    """选项维护页面标签测试"""

    def test_options_page_labels(self, client):
        """测试选项维护页面标签"""
        response = client.get('/options')
        assert response.status_code == 200

        html = response.data.decode('utf-8')
        # 动力（不是动力类型）
        assert '动力' in html
