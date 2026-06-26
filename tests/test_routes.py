"""路由测试"""
import pytest


class TestPageRoutes:
    def test_home_page(self, client):
        """测试首页"""
        response = client.get('/')
        assert response.status_code == 200
        assert '火车模型管理系统' in response.data.decode('utf-8')
