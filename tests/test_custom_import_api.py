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


class TestCustomImportTablesAPI:
  """自定义导入表配置 API 测试"""

  def test_get_tables_config(self, client):
    """测试获取系统表配置"""
    response = client.get('/api/custom-import/tables')
    assert response.status_code == 200
    data = response.get_json()
    assert 'tables' in data
    assert len(data['tables']) > 0

  def test_tables_config_contains_system_tables(self, client):
    """测试表配置包含系统表"""
    response = client.get('/api/custom-import/tables')
    data = response.get_json()
    table_names = [t['name'] for t in data['tables']]

    # 检查系统表
    assert 'brand' in table_names
    assert 'depot' in table_names
    assert 'merchant' in table_names

  def test_tables_config_contains_model_tables(self, client):
    """测试表配置包含模型表"""
    response = client.get('/api/custom-import/tables')
    data = response.get_json()
    table_names = [t['name'] for t in data['tables']]

    # 检查模型表
    assert 'locomotive' in table_names
    assert 'carriage' in table_names
    assert 'trainset' in table_names
    assert 'locomotive_head' in table_names

  def test_tables_config_structure(self, client):
    """测试表配置结构正确"""
    response = client.get('/api/custom-import/tables')
    data = response.get_json()

    for table in data['tables']:
      assert 'name' in table
      assert 'display_name' in table
      assert 'category' in table
      assert table['category'] in ['system', 'model']


class TestCustomImportParseAPI:
  """Excel 解析 API 测试"""

  def test_parse_excel_file(self, client):
    """测试解析 Excel 文件"""
    # Create test Excel file
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "品牌列表"
    ws1.append(['品牌名称', '官网地址'])
    ws1.append(['百万城', 'https://example.com'])

    ws2 = wb.create_sheet("机车数据")
    ws2.append(['品牌', '比例', '机车号'])
    ws2.append(['百万城', 'N', '0001'])

    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # Send request
    response = client.post(
      '/api/custom-import/parse',
      data={'file': (output, 'test.xlsx')},
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['sheets']) == 2
    assert data['sheets'][0]['name'] == '品牌列表'
    assert '品牌名称' in data['sheets'][0]['columns']

  def test_parse_no_file(self, client):
    """测试未选择文件"""
    response = client.post('/api/custom-import/parse')
    assert response.status_code == 400


class TestCustomImportPreviewAPI:
  """自定义导入预览 API 测试"""

  def create_excel_file(self, sheets_data):
    """
    创建测试用 Excel 文件

    Args:
      sheets_data: dict, {sheet_name: {'headers': [...], 'rows': [[...], ...]}}

    Returns:
      BytesIO: Excel 文件字节流
    """
    wb = openpyxl.Workbook()
    first_sheet = True
    for sheet_name, data in sheets_data.items():
      if first_sheet:
        ws = wb.active
        ws.title = sheet_name
        first_sheet = False
      else:
        ws = wb.create_sheet(sheet_name)

      ws.append(data['headers'])
      for row in data['rows']:
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

  def test_preview_no_file(self, client):
    """测试预览时未选择文件"""
    config = {
      'sheet_mappings': [],
      'column_mappings': {}
    }
    response = client.post(
      '/api/custom-import/preview',
      data={'config': json.dumps(config)},
      content_type='multipart/form-data'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_preview_no_config(self, client):
    """测试预览时缺少配置"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['品牌名称'])
    ws.append(['测试品牌'])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = client.post(
      '/api/custom-import/preview',
      data={'file': (output, 'test.xlsx')},
      content_type='multipart/form-data'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_preview_success_no_conflicts(self, client):
    """测试预览成功且无冲突"""
    # 创建 Excel 文件
    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称', '官网地址'],
        'rows': [['新品牌A', 'https://a.com'], ['新品牌B', 'https://b.com']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True},
            {'source': '官网地址', 'target': 'search_url', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['has_conflicts'] is False
    assert data['can_proceed'] is True
    assert len(data['previews']) == 1
    assert data['previews'][0]['table_name'] == 'brand'
    assert data['previews'][0]['row_count'] == 2
    assert data['previews'][0]['display_name'] == '品牌'
    assert len(data['previews'][0]['conflicts']) == 0
    assert len(data['previews'][0]['missing_required']) == 0

  def test_preview_missing_required_fields(self, client):
    """测试缺少必填字段映射"""
    output = self.create_excel_file({
      '机车数据': {
        'headers': ['品牌', '机车号'],
        'rows': [['百万城', '0001']]
      }
    })

    # 缺少 scale 字段映射（必填）
    config = {
      'sheet_mappings': [
        {'sheet_name': '机车数据', 'table_name': 'locomotive'}
      ],
      'column_mappings': {
        'locomotive': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '机车号', 'target': 'locomotive_number', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['can_proceed'] is False
    assert len(data['previews']) == 1
    assert 'scale' in data['previews'][0]['missing_required']

  def test_preview_unique_conflict(self, client, app):
    """测试唯一约束冲突检测（品牌名称）"""
    # 先在数据库中创建一个品牌
    with app.app_context():
      brand = Brand(name='已存在品牌')
      db.session.add(brand)
      db.session.commit()

    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称'],
        'rows': [['已存在品牌'], ['新品牌']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['has_conflicts'] is True
    assert data['can_proceed'] is True  # 有冲突但可以跳过
    assert len(data['previews'][0]['conflicts']) == 1
    conflict = data['previews'][0]['conflicts'][0]
    assert conflict['type'] == '唯一名称冲突'
    assert conflict['field'] == 'name'
    assert conflict['value'] == '已存在品牌'

  def test_preview_unique_in_scale_conflict(self, client, app):
    """测试比例内唯一约束冲突检测（机车号）"""
    # 先在数据库中创建一个机车
    with app.app_context():
      brand = Brand(name='测试品牌')
      db.session.add(brand)
      db.session.commit()

      loco = Locomotive(
        brand_id=brand.id,
        scale='N',
        locomotive_number='0001'
      )
      db.session.add(loco)
      db.session.commit()

    output = self.create_excel_file({
      '机车数据': {
        'headers': ['品牌', '比例', '机车号'],
        'rows': [['测试品牌', 'N', '0001']]  # 冲突：同比例同机车号
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '机车数据', 'table_name': 'locomotive'}
      ],
      'column_mappings': {
        'locomotive': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '机车号', 'target': 'locomotive_number', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['has_conflicts'] is True
    assert len(data['previews'][0]['conflicts']) == 1
    conflict = data['previews'][0]['conflicts'][0]
    assert conflict['type'] == '比例内唯一冲突'
    assert conflict['field'] == 'locomotive_number'
    assert 'N' in conflict['value']
    assert '0001' in conflict['value']

  def test_preview_multiple_sheets(self, client):
    """测试多工作表预览"""
    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称'],
        'rows': [['品牌A'], ['品牌B']]
      },
      '商家列表': {
        'headers': ['商家名称'],
        'rows': [['商家X']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'},
        {'sheet_name': '商家列表', 'table_name': 'merchant'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        },
        'merchant': {
          'columns': [
            {'source': '商家名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['previews']) == 2

    # 检查两个表的预览
    table_names = [p['table_name'] for p in data['previews']]
    assert 'brand' in table_names
    assert 'merchant' in table_names

    # 检查行数
    brand_preview = next(p for p in data['previews'] if p['table_name'] == 'brand')
    merchant_preview = next(p for p in data['previews'] if p['table_name'] == 'merchant')
    assert brand_preview['row_count'] == 2
    assert merchant_preview['row_count'] == 1

  def test_preview_warnings_for_unmapped_optional_fields(self, client):
    """测试未映射的可选字段警告"""
    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称'],
        'rows': [['新品牌']]
      }
    })

    # 只映射了必填字段，未映射可选字段 search_url
    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 检查警告中是否包含未映射的可选字段
    warnings = data['previews'][0]['warnings']
    assert any('search_url' in w for w in warnings)

  def test_preview_invalid_json_config(self, client):
    """测试无效的 JSON 配置"""
    output = self.create_excel_file({
      '测试': {
        'headers': ['名称'],
        'rows': [['测试']]
      }
    })

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': 'not valid json'
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_preview_unknown_table_name(self, client):
    """测试未知的表名"""
    output = self.create_excel_file({
      '测试': {
        'headers': ['名称'],
        'rows': [['测试']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '测试', 'table_name': 'unknown_table'}
      ],
      'column_mappings': {
        'unknown_table': {
          'columns': [
            {'source': '名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    # 应该跳过未知的表并继续处理
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

  def test_preview_empty_sheet(self, client):
    """测试空工作表"""
    output = self.create_excel_file({
      '空表': {
        'headers': ['品牌名称'],
        'rows': []  # 无数据行
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '空表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/preview',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['previews'][0]['row_count'] == 0


class TestCustomImportExecuteAPI:
  """自定义导入执行 API 测试"""

  def create_excel_file(self, sheets_data):
    """
    创建测试用 Excel 文件

    Args:
      sheets_data: dict, {sheet_name: {'headers': [...], 'rows': [[...], ...]}}

    Returns:
      BytesIO: Excel 文件字节流
    """
    wb = openpyxl.Workbook()
    first_sheet = True
    for sheet_name, data in sheets_data.items():
      if first_sheet:
        ws = wb.active
        ws.title = sheet_name
        first_sheet = False
      else:
        ws = wb.create_sheet(sheet_name)

      ws.append(data['headers'])
      for row in data['rows']:
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

  def test_execute_no_file(self, client):
    """测试执行时未选择文件"""
    config = {
      'sheet_mappings': [],
      'column_mappings': {}
    }
    response = client.post(
      '/api/custom-import/execute',
      data={'config': json.dumps(config)},
      content_type='multipart/form-data'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_execute_no_config(self, client):
    """测试执行时缺少配置"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['品牌名称'])
    ws.append(['测试品牌'])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = client.post(
      '/api/custom-import/execute',
      data={'file': (output, 'test.xlsx')},
      content_type='multipart/form-data'
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_execute_import_brand_success(self, client):
    """测试成功导入品牌数据"""
    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称', '官网地址'],
        'rows': [['新品牌A', 'https://a.com'], ['新品牌B', 'https://b.com']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True},
            {'source': '官网地址', 'target': 'search_url', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['summary']['brand'] == 2

    # 验证数据库中的数据
    brands = Brand.query.all()
    assert len(brands) == 2
    brand_names = [b.name for b in brands]
    assert '新品牌A' in brand_names
    assert '新品牌B' in brand_names

  def test_execute_import_with_skip_mode(self, client, app):
    """测试 skip 模式：跳过已存在的数据"""
    # 先创建一个品牌
    with app.app_context():
      brand = Brand(name='已存在品牌')
      db.session.add(brand)
      db.session.commit()

    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称'],
        'rows': [['已存在品牌'], ['新品牌']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 只导入了新品牌，已存在的被跳过
    assert data['summary']['brand'] == 1

    # 验证数据库中只有 2 个品牌
    brands = Brand.query.all()
    assert len(brands) == 2

  def test_execute_import_with_overwrite_mode(self, client, app):
    """测试 overwrite 模式：更新已存在的数据"""
    # 先创建一个品牌
    with app.app_context():
      brand = Brand(name='测试品牌', search_url='https://old.com')
      db.session.add(brand)
      db.session.commit()

    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称', '官网地址'],
        'rows': [['测试品牌', 'https://new.com']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True},
            {'source': '官网地址', 'target': 'search_url', 'required': False}
          ],
          'conflict_mode': 'overwrite'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # overwrite 模式下更新了 1 条
    assert data['summary']['brand'] == 1

    # 验证 URL 被更新
    brand = Brand.query.filter_by(name='测试品牌').first()
    assert brand.search_url == 'https://new.com'

  def test_execute_import_locomotive_with_fk_resolution(self, client, app):
    """测试机车导入，包含外键解析"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      series = LocomotiveSeries(name='和谐系列')
      power_type = PowerType(name='电力')
      db.session.add_all([brand, series, power_type])
      db.session.commit()

      loco_model = LocomotiveModel(
        name='HXD1',
        series_id=series.id,
        power_type_id=power_type.id
      )
      db.session.add(loco_model)
      db.session.commit()

    output = self.create_excel_file({
      '机车数据': {
        'headers': ['品牌', '比例', '系列', '动力', '车型', '机车号'],
        'rows': [['百万城', 'N', '和谐系列', '电力', 'HXD1', '0001']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '机车数据', 'table_name': 'locomotive'}
      ],
      'column_mappings': {
        'locomotive': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '系列', 'target': 'series_id', 'required': False},
            {'source': '动力', 'target': 'power_type_id', 'required': False},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '机车号', 'target': 'locomotive_number', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['summary']['locomotive'] == 1

    # 验证机车数据
    loco = Locomotive.query.first()
    assert loco is not None
    assert loco.brand.name == '百万城'
    assert loco.scale == 'N'
    assert loco.series.name == '和谐系列'
    assert loco.locomotive_number == '0001'

  def test_execute_import_locomotive_skip_on_conflict(self, client, app):
    """测试机车导入时跳过冲突数据"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      db.session.add(brand)
      db.session.commit()

      # 创建一个已存在的机车
      loco = Locomotive(
        brand_id=brand.id,
        scale='N',
        locomotive_number='0001'
      )
      db.session.add(loco)
      db.session.commit()

    output = self.create_excel_file({
      '机车数据': {
        'headers': ['品牌', '比例', '机车号'],
        'rows': [
          ['百万城', 'N', '0001'],  # 冲突：同比例同机车号
          ['百万城', 'N', '0002']   # 新数据
        ]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '机车数据', 'table_name': 'locomotive'}
      ],
      'column_mappings': {
        'locomotive': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '机车号', 'target': 'locomotive_number', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 只导入了 1 条（跳过了冲突的）
    assert data['summary']['locomotive'] == 1

  def test_execute_import_locomotive_overwrite_on_conflict(self, client, app):
    """测试机车导入时覆盖冲突数据"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      new_brand = Brand(name='新品牌')
      db.session.add_all([brand, new_brand])
      db.session.commit()

      # 创建一个已存在的机车
      loco = Locomotive(
        brand_id=brand.id,
        scale='N',
        locomotive_number='0001',
        color='旧颜色'
      )
      db.session.add(loco)
      db.session.commit()
      original_id = loco.id

    output = self.create_excel_file({
      '机车数据': {
        'headers': ['品牌', '比例', '机车号', '颜色'],
        'rows': [['新品牌', 'N', '0001', '新颜色']]  # 冲突但会覆盖
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '机车数据', 'table_name': 'locomotive'}
      ],
      'column_mappings': {
        'locomotive': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '机车号', 'target': 'locomotive_number', 'required': False},
            {'source': '颜色', 'target': 'color', 'required': False}
          ],
          'conflict_mode': 'overwrite'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['summary']['locomotive'] == 1

    # 验证数据被更新
    loco = db.session.get(Locomotive, original_id)
    assert loco.color == '新颜色'
    assert loco.brand.name == '新品牌'

  def test_execute_import_missing_fk_skips_row(self, client, app):
    """测试外键找不到时跳过该行"""
    # 不创建任何品牌，导入应该失败
    output = self.create_excel_file({
      '机车数据': {
        'headers': ['品牌', '比例', '机车号'],
        'rows': [['不存在的品牌', 'N', '0001']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '机车数据', 'table_name': 'locomotive'}
      ],
      'column_mappings': {
        'locomotive': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '机车号', 'target': 'locomotive_number', 'required': False}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 因为品牌找不到，所以没有导入任何数据
    assert data['summary']['locomotive'] == 0

  def test_execute_import_multiple_tables(self, client):
    """测试同时导入多个表"""
    output = self.create_excel_file({
      '品牌列表': {
        'headers': ['品牌名称'],
        'rows': [['品牌A'], ['品牌B']]
      },
      '商家列表': {
        'headers': ['商家名称'],
        'rows': [['商家X']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '品牌列表', 'table_name': 'brand'},
        {'sheet_name': '商家列表', 'table_name': 'merchant'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        },
        'merchant': {
          'columns': [
            {'source': '商家名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['summary']['brand'] == 2
    assert data['summary']['merchant'] == 1

  def test_execute_import_empty_sheet(self, client):
    """测试导入空工作表"""
    output = self.create_excel_file({
      '空表': {
        'headers': ['品牌名称'],
        'rows': []
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '空表', 'table_name': 'brand'}
      ],
      'column_mappings': {
        'brand': {
          'columns': [
            {'source': '品牌名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['summary']['brand'] == 0

  def test_execute_import_invalid_json_config(self, client):
    """测试无效的 JSON 配置"""
    output = self.create_excel_file({
      '测试': {
        'headers': ['名称'],
        'rows': [['测试']]
      }
    })

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': 'not valid json'
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False

  def test_execute_import_unknown_table_name(self, client):
    """测试未知的表名（应该跳过）"""
    output = self.create_excel_file({
      '测试': {
        'headers': ['名称'],
        'rows': [['测试']]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '测试', 'table_name': 'unknown_table'}
      ],
      'column_mappings': {
        'unknown_table': {
          'columns': [
            {'source': '名称', 'target': 'name', 'required': True}
          ],
          'conflict_mode': 'skip'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    # 应该跳过未知的表并返回成功
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'unknown_table' not in data['summary']


class TestCarriageMergedCellDetection:
  """车厢合并单元格检测测试"""

  def create_excel_with_merged_cells(self, sheets_data, merged_ranges=None):
    """
    创建带有合并单元格的 Excel 文件

    Args:
      sheets_data: dict, {sheet_name: {'headers': [...], 'rows': [[...], ...]}}
      merged_ranges: dict, {sheet_name: [(start_row, start_col, end_row, end_col), ...]}
        注意：行、列索引都是 1-based

    Returns:
      BytesIO: Excel 文件字节流
    """
    wb = openpyxl.Workbook()
    first_sheet = True
    for sheet_name, data in sheets_data.items():
      if first_sheet:
        ws = wb.active
        ws.title = sheet_name
        first_sheet = False
      else:
        ws = wb.create_sheet(sheet_name)

      ws.append(data['headers'])
      for row in data['rows']:
        ws.append(row)

      # 添加合并单元格
      if merged_ranges and sheet_name in merged_ranges:
        for start_row, start_col, end_row, end_col in merged_ranges[sheet_name]:
          ws.merge_cells(start_row=start_row, start_column=start_col,
                         end_row=end_row, end_column=end_col)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

  def test_carriage_import_with_merged_cells(self, client, app):
    """测试合并单元格识别套装"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      series = CarriageSeries(name='YZ系列')
      model1 = CarriageModel(name='YZ22', series_id=1, type='客车')
      model2 = CarriageModel(name='YZ25', series_id=1, type='客车')
      db.session.add_all([brand, series, model1, model2])
      db.session.commit()

    # 创建带合并单元格的 Excel 文件
    # 套装1: 百万城, N, 3节车厢 (行 2-4)
    # 套装2: 百万城, N, 2节车厢 (行 5-6)
    output = self.create_excel_with_merged_cells(
      {
        '车厢数据': {
          'headers': ['品牌', '比例', '系列', '车次', '车型', '车辆号', '颜色'],
          'rows': [
            ['百万城', 'N', 'YZ系列', 'K123', 'YZ22', '001', '绿色'],
            ['百万城', 'N', 'YZ系列', 'K123', 'YZ22', '002', '绿色'],
            ['百万城', 'N', 'YZ系列', 'K123', 'YZ25', '003', '绿色'],
            ['百万城', 'N', 'YZ系列', 'T456', 'YZ25', '101', '蓝色'],
            ['百万城', 'N', 'YZ系列', 'T456', 'YZ22', '102', '蓝色'],
          ]
        }
      },
      merged_ranges={
        '车厢数据': [
          # 套装1: 合并品牌(A列)、比例(B列)、系列(C列)、车次(D列) - 行2-4
          (2, 1, 4, 1),  # 品牌
          (2, 2, 4, 2),  # 比例
          (2, 3, 4, 3),  # 系列
          (2, 4, 4, 4),  # 车次
          # 套装2: 合并品牌(A列)、比例(B列)、系列(C列)、车次(D列) - 行5-6
          (5, 1, 6, 1),  # 品牌
          (5, 2, 6, 2),  # 比例
          (5, 3, 6, 3),  # 系列
          (5, 4, 6, 4),  # 车次
        ]
      }
    )

    config = {
      'sheet_mappings': [
        {'sheet_name': '车厢数据', 'table_name': 'carriage'}
      ],
      'column_mappings': {
        'carriage': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '系列', 'target': 'series_id', 'required': False},
            {'source': '车次', 'target': 'train_number', 'required': False},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '车辆号', 'target': 'car_number', 'required': False},
            {'source': '颜色', 'target': 'color', 'required': False}
          ],
          'conflict_mode': 'skip',
          'set_detection_mode': 'merged'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 应该识别出 2 个套装
    assert data['summary']['carriage'] == 2

    # 验证数据库中的数据
    with app.app_context():
      sets = CarriageSet.query.all()
      assert len(sets) == 2

      # 套装1: 3节车厢
      set1 = CarriageSet.query.filter_by(train_number='K123').first()
      assert set1 is not None
      assert len(set1.items) == 3

      # 套装2: 2节车厢
      set2 = CarriageSet.query.filter_by(train_number='T456').first()
      assert set2 is not None
      assert len(set2.items) == 2

  def test_carriage_import_without_merged_cells(self, client, app):
    """测试无合并单元格时按品牌+比例识别套装"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      series = CarriageSeries(name='YZ系列')
      model1 = CarriageModel(name='YZ22', series_id=1, type='客车')
      db.session.add_all([brand, series, model1])
      db.session.commit()

    # 创建不带合并单元格的 Excel 文件
    # 由于没有合并单元格，每行都是独立套装（brand+scale 都有值）
    output = self.create_excel_with_merged_cells({
      '车厢数据': {
        'headers': ['品牌', '比例', '车型', '车辆号'],
        'rows': [
          ['百万城', 'N', 'YZ22', '001'],
          ['百万城', 'N', 'YZ22', '002'],
        ]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '车厢数据', 'table_name': 'carriage'}
      ],
      'column_mappings': {
        'carriage': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '车辆号', 'target': 'car_number', 'required': False}
          ],
          'conflict_mode': 'skip',
          'set_detection_mode': 'merged'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 没有合并单元格时，每行都是独立套装
    assert data['summary']['carriage'] == 2

  def test_carriage_import_row_mode(self, client, app):
    """测试每行作为独立套装模式"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      model1 = CarriageModel(name='YZ22', series_id=1, type='客车')
      model2 = CarriageModel(name='YZ25', series_id=1, type='客车')
      db.session.add_all([brand, model1, model2])
      db.session.commit()

    # 即使有合并单元格，set_detection_mode='row' 也会忽略
    output = self.create_excel_with_merged_cells(
      {
        '车厢数据': {
          'headers': ['品牌', '比例', '车型', '车辆号'],
          'rows': [
            ['百万城', 'N', 'YZ22', '001'],
            ['百万城', 'N', 'YZ25', '002'],
          ]
        }
      },
      merged_ranges={
        '车厢数据': [
          (2, 1, 3, 1),  # 合并品牌
          (2, 2, 3, 2),  # 合并比例
        ]
      }
    )

    config = {
      'sheet_mappings': [
        {'sheet_name': '车厢数据', 'table_name': 'carriage'}
      ],
      'column_mappings': {
        'carriage': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '车辆号', 'target': 'car_number', 'required': False}
          ],
          'conflict_mode': 'skip',
          'set_detection_mode': 'row'  # 每行独立套装
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 每行都是独立套装
    assert data['summary']['carriage'] == 2

    # 验证每个套装只有 1 个车厢项
    with app.app_context():
      sets = CarriageSet.query.all()
      assert len(sets) == 2
      for s in sets:
        assert len(s.items) == 1

  def test_carriage_import_inconsistent_merged_values(self, client, app):
    """测试合并单元格内值不一致时的警告"""
    # 创建必要的参考数据
    with app.app_context():
      brand1 = Brand(name='百万城')
      brand2 = Brand(name='ROC')
      series = CarriageSeries(name='YZ系列')
      model1 = CarriageModel(name='YZ22', series_id=1, type='客车')
      db.session.add_all([brand1, brand2, series, model1])
      db.session.commit()

    # 创建带合并单元格但实际值不一致的 Excel
    # 注意：openpyxl 合并单元格后，只有左上角单元格有值
    # 这里我们手动设置不一致的值来测试警告
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '车厢数据'
    ws.append(['品牌', '比例', '车型', '车辆号'])

    # 行2-3 合并，但设置不同值
    ws.append(['百万城', 'N', 'YZ22', '001'])
    ws.append(['ROC', 'N', 'YZ22', '002'])  # 品牌值不一致

    # 合并品牌列
    ws.merge_cells(start_row=2, start_column=1, end_row=3, end_column=1)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    config = {
      'sheet_mappings': [
        {'sheet_name': '车厢数据', 'table_name': 'carriage'}
      ],
      'column_mappings': {
        'carriage': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '车辆号', 'target': 'car_number', 'required': False}
          ],
          'conflict_mode': 'skip',
          'set_detection_mode': 'merged'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 由于合并单元格后只有第一个值可见，所以应该只创建 1 个套装
    assert data['summary']['carriage'] == 1

  def test_carriage_import_single_row_per_set(self, client, app):
    """测试每个套装只有一行数据"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      model1 = CarriageModel(name='YZ22', series_id=1, type='客车')
      model2 = CarriageModel(name='YZ25', series_id=1, type='客车')
      db.session.add_all([brand, model1, model2])
      db.session.commit()

    # 每个套装只有一行，不需要合并单元格
    output = self.create_excel_with_merged_cells({
      '车厢数据': {
        'headers': ['品牌', '比例', '车型', '车辆号'],
        'rows': [
          ['百万城', 'N', 'YZ22', '001'],
          ['百万城', 'N', 'YZ25', '002'],
          ['百万城', 'HO', 'YZ22', '101'],
        ]
      }
    })

    config = {
      'sheet_mappings': [
        {'sheet_name': '车厢数据', 'table_name': 'carriage'}
      ],
      'column_mappings': {
        'carriage': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '车辆号', 'target': 'car_number', 'required': False}
          ],
          'conflict_mode': 'skip',
          'set_detection_mode': 'merged'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 3 行，每行一个套装
    assert data['summary']['carriage'] == 3

  def test_carriage_import_empty_rows_in_merged_range(self, client, app):
    """测试合并单元格范围内有空行"""
    # 创建必要的参考数据
    with app.app_context():
      brand = Brand(name='百万城')
      model1 = CarriageModel(name='YZ22', series_id=1, type='客车')
      db.session.add_all([brand, model1])
      db.session.commit()

    # 创建带合并单元格的 Excel，包含空行
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '车厢数据'
    ws.append(['品牌', '比例', '车型', '车辆号'])
    ws.append(['百万城', 'N', 'YZ22', '001'])
    ws.append(['百万城', 'N', 'YZ22', '002'])
    ws.append([None, None, None, None])  # 空行
    ws.append(['百万城', 'N', 'YZ22', '003'])

    # 合并前两行
    ws.merge_cells(start_row=2, start_column=1, end_row=3, end_column=1)
    ws.merge_cells(start_row=2, start_column=2, end_row=3, end_column=2)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    config = {
      'sheet_mappings': [
        {'sheet_name': '车厢数据', 'table_name': 'carriage'}
      ],
      'column_mappings': {
        'carriage': {
          'columns': [
            {'source': '品牌', 'target': 'brand_id', 'required': True},
            {'source': '比例', 'target': 'scale', 'required': True},
            {'source': '车型', 'target': 'model_id', 'required': False},
            {'source': '车辆号', 'target': 'car_number', 'required': False}
          ],
          'conflict_mode': 'skip',
          'set_detection_mode': 'merged'
        }
      }
    }

    response = client.post(
      '/api/custom-import/execute',
      data={
        'file': (output, 'test.xlsx'),
        'config': json.dumps(config)
      },
      content_type='multipart/form-data'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    # 空行会被跳过，但合并单元格检测仍然会处理有效的行
