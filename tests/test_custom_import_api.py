"""自定义导入 API 测试"""
import pytest
import io
import json
import openpyxl
from models import db, ImportTemplate, Brand, Locomotive, LocomotiveSeries, PowerType, LocomotiveModel
from models import CarriageSet, CarriageSeries, CarriageModel


class TestImportTemplateAPI:
  """导入模板 API 测试"""

  def test_list_templates_empty(self, client):
    """测试空模板列表"""
    response = client.get('/api/import-templates')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['templates'] == []

  def test_create_template(self, client):
    """测试创建模板"""
    response = client.post('/api/import-templates', json={
      'name': '测试模板',
      'config': {'sheet_mappings': [], 'column_mappings': {}}
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['template']['name'] == '测试模板'

  def test_list_templates_with_data(self, client):
    """测试有数据时的模板列表"""
    client.post('/api/import-templates', json={'name': '模板1', 'config': {}})
    client.post('/api/import-templates', json={'name': '模板2', 'config': {}})
    response = client.get('/api/import-templates')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['templates']) == 2

  def test_update_template(self, client):
    """测试更新模板"""
    create_response = client.post('/api/import-templates', json={'name': '原名称', 'config': {}})
    template_id = create_response.get_json()['template']['id']
    response = client.put(f'/api/import-templates/{template_id}', json={
      'name': '新名称',
      'config': {'test': 'value'}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['template']['name'] == '新名称'

  def test_delete_template(self, client):
    """测试删除模板"""
    create_response = client.post('/api/import-templates', json={'name': '要删除的模板', 'config': {}})
    template_id = create_response.get_json()['template']['id']
    response = client.delete(f'/api/import-templates/{template_id}')
    assert response.status_code == 200
    list_response = client.get('/api/import-templates')
    assert len(list_response.get_json()['templates']) == 0

  def test_get_template_by_id(self, client):
    """测试获取单个模板"""
    create_response = client.post('/api/import-templates', json={'name': '测试模板', 'config': {'key': 'value'}})
    template_id = create_response.get_json()['template']['id']
    response = client.get(f'/api/import-templates/{template_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['template']['name'] == '测试模板'
    assert data['template']['config'] == {'key': 'value'}

  def test_get_nonexistent_template(self, client):
    """测试获取不存在的模板"""
    response = client.get('/api/import-templates/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False

  def test_update_nonexistent_template(self, client):
    """测试更新不存在的模板"""
    response = client.put('/api/import-templates/9999', json={'name': '测试', 'config': {}})
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False

  def test_delete_nonexistent_template(self, client):
    """测试删除不存在的模板"""
    response = client.delete('/api/import-templates/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False

  def test_copy_template(self, client, app):
    """测试复制模板"""
    # 先创建一个模板
    with app.app_context():
      template = ImportTemplate(name='原模板', config={'key': 'value'})
      db.session.add(template)
      db.session.commit()
      template_id = template.id

    # 复制模板
    new_name = '原模板_副本_20260101_120000'
    response = client.post(f'/api/import-templates/{template_id}/copy', json={'name': new_name})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['template']['name'] == new_name
    assert data['template']['config'] == {'key': 'value'}

    # 验证新模板已创建
    with app.app_context():
      new_template = ImportTemplate.query.filter_by(name=new_name).first()
      assert new_template is not None
      assert new_template.config == {'key': 'value'}

  def test_copy_nonexistent_template(self, client):
    """测试复制不存在的模板"""
    response = client.post('/api/import-templates/9999/copy', json={'name': '新名称'})
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False

  def test_copy_template_without_name(self, client, app):
    """测试复制模板时缺少名称"""
    with app.app_context():
      template = ImportTemplate(name='测试模板', config={})
      db.session.add(template)
      db.session.commit()
      template_id = template.id

    response = client.post(f'/api/import-templates/{template_id}/copy', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_copy_template_duplicate_name(self, client, app):
    """测试复制模板时名称重复"""
    with app.app_context():
      template1 = ImportTemplate(name='模板1', config={})
      template2 = ImportTemplate(name='已存在', config={})
      db.session.add_all([template1, template2])
      db.session.commit()
      template_id = template1.id

    response = client.post(f'/api/import-templates/{template_id}/copy', json={'name': '已存在'})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert '已存在' in data['error']

  def test_create_template_without_name(self, client):
    """测试创建模板时缺少名称"""
    response = client.post('/api/import-templates', json={'config': {}})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_create_template_without_config(self, client):
    """测试创建模板时缺少配置"""
    response = client.post('/api/import-templates', json={'name': '测试模板'})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


