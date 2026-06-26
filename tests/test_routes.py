"""路由测试"""
import pytest

class TestPageRoutes:
    def test_home_page(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert '火车模型管理系统' in response.data.decode('utf-8')

    def test_locomotive_page(self, client):
        response = client.get('/locomotive')
        assert response.status_code == 200
        assert '机车模型' in response.data.decode('utf-8')

class TestCopyButtons:
    def test_locomotive_copy_button(self, client, sample_data):
        from models import db, Locomotive
        with client.application.app_context():
            loco = Locomotive(series_id=1, power_type_id=1, model_id=1, brand_id=1, scale='HO', locomotive_number='COPY001')
            db.session.add(loco); db.session.commit()
        response = client.get('/locomotive')
        html = response.data.decode('utf-8')
        assert '复制' in html and 'copyLocomotive' in html

    def test_locomotive_copy_data_attributes(self, client, sample_data):
        from models import db, Locomotive
        with client.application.app_context():
            loco = Locomotive(series_id=1, power_type_id=1, model_id=1, brand_id=1, scale='HO', locomotive_number='DATA001', decoder_number='01', plaque='测试', price='100', item_number='ITEM001')
            db.session.add(loco); db.session.commit()
        response = client.get('/locomotive')
        html = response.data.decode('utf-8')
        assert 'data-model_id=' in html and 'data-brand_id=' in html and 'data-item_number=' in html

class TestLocomotiveCRUD:
    def test_locomotive_add_page(self, client):
        response = client.get('/locomotive')
        assert b'model_id' in response.data and b'brand_id' in response.data
