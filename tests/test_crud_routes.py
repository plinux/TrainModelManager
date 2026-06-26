"""
CRUD 路由测试
覆盖 routes/locomotive.py, routes/carriage.py, routes/trainset.py,
routes/locomotive_head.py, routes/system.py 的所有路由
"""
import pytest
import json
import sys
import subprocess
from models import (db, Locomotive, CarriageSet, CarriageItem, Trainset,
  LocomotiveHead, Brand, Depot, Merchant, PowerType,
  LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel,
  TrainsetSeries, TrainsetModel, ChipInterface, ChipModel)


# ============================================================
# Shared helpers
# ============================================================

def _base_locomotive_data(**overrides):
  """Return a base dict for locomotive form/API data."""
  data = {
    'model_id': '1',
    'series_id': '1',
    'power_type_id': '1',
    'brand_id': '1',
    'depot_id': '1',
    'scale': 'HO',
    'locomotive_number': '',
    'decoder_number': '',
    'plaque': '',
    'color': '',
    'chip_interface_id': '',
    'chip_model_id': '',
    'price': '500',
    'item_number': 'ITEM001',
    'product_url': '',
    'purchase_date': '2024-01-15',
    'merchant_id': '1'
  }
  data.update(overrides)
  return data


def _base_trainset_data(**overrides):
  """Return a base dict for trainset form/API data."""
  data = {
    'model_id': '1',
    'series_id': '1',
    'power_type_id': '1',
    'brand_id': '1',
    'depot_id': '1',
    'scale': 'HO',
    'trainset_number': '',
    'decoder_number': '',
    'formation': '8',
    'plaque': '',
    'color': '',
    'head_light': 'true',
    'light_model_id': '',
    'chip_interface_id': '',
    'chip_model_id': '',
    'price': '1200',
    'item_number': 'TS001',
    'product_url': '',
    'purchase_date': '2024-03-01',
    'merchant_id': '1'
  }
  data.update(overrides)
  return data


def _base_carriage_data(**overrides):
  """Return a base dict for carriage set form/API data."""
  data = {
    'brand_id': '1',
    'series_id': '1',
    'depot_id': '1',
    'train_number': 'G123',
    'plaque': '',
    'item_number': 'CRG001',
    'scale': 'HO',
    'total_price': '800',
    'product_url': '',
    'purchase_date': '2024-02-20',
    'merchant_id': '1',
    # One carriage item
    'model_0': '1',
    'car_number_0': 'YZ-01',
    'color_0': 'green',
    'light_model_id_0': ''
  }
  data.update(overrides)
  return data


def _base_locomotive_head_data(**overrides):
  """Return a base dict for locomotive head form/API data."""
  data = {
    'model_id': '1',
    'brand_id': '1',
    'special_color': '',
    'scale': 'HO',
    'head_light': 'true',
    'light_model_id': '',
    'price': '350',
    'item_number': 'LH001',
    'product_url': '',
    'purchase_date': '2024-04-10',
    'merchant_id': '1'
  }
  data.update(overrides)
  return data


# ============================================================
# Locomotive route tests
# ============================================================

class TestLocomotiveRoutes:
  """机车模型路由测试"""

  # --- GET /locomotive ---

  def test_list_page_returns_200(self, client, sample_data):
    """测试 GET /locomotive 返回列表页"""
    response = client.get('/locomotive')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '机车模型' in html

  def test_list_page_shows_existing_data(self, client, sample_data):
    """测试列表页显示已有机车数据"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', locomotive_number='9999', item_number='ITM_LIST'
      )
      db.session.add(loco)
      db.session.commit()

    response = client.get('/locomotive')
    assert response.status_code == 200
    assert '9999' in response.data.decode('utf-8')

  # --- POST /locomotive (form add) ---

  def test_form_add_success_redirects(self, client, sample_data):
    """测试表单添加机车成功后重定向"""
    data = _base_locomotive_data()
    response = client.post('/locomotive', data=data, follow_redirects=False)
    assert response.status_code == 302
    assert '/locomotive' in response.headers['Location']

  def test_form_add_persists_data(self, client, sample_data):
    """测试表单添加机车后数据库有记录"""
    data = _base_locomotive_data(item_number='FORM_ADD_1')
    client.post('/locomotive', data=data, follow_redirects=True)

    with client.application.app_context():
      loco = Locomotive.query.filter_by(item_number='FORM_ADD_1').first()
      assert loco is not None
      assert loco.scale == 'HO'
      assert loco.total_price == 500.0

  def test_form_add_with_all_fields(self, client, sample_data):
    """测试表单添加机车包含所有字段"""
    data = _base_locomotive_data(
      locomotive_number='1234',
      decoder_number='1',
      plaque='测试挂牌',
      color='红色',
      chip_interface_id='1',
      chip_model_id='1',
      item_number='FULL_FORM'
    )
    response = client.post('/locomotive', data=data, follow_redirects=True)
    assert response.status_code == 200

    with client.application.app_context():
      loco = Locomotive.query.filter_by(item_number='FULL_FORM').first()
      assert loco is not None
      assert loco.locomotive_number == '1234'
      assert loco.decoder_number == '1'
      assert loco.plaque == '测试挂牌'
      assert loco.color == '红色'
      assert loco.chip_interface_id == 1
      assert loco.chip_model_id == 1

  def test_form_add_invalid_locomotive_number_no_redirect(self, client, sample_data):
    """测试表单添加机车号格式错误时不重定向（验证失败）"""
    data = _base_locomotive_data(locomotive_number='AB', scale='HO')
    response = client.post('/locomotive', data=data, follow_redirects=False)
    # Validation errors cause re-render (200) instead of redirect (302)
    assert response.status_code == 200
    assert '机车模型' in response.data.decode('utf-8')

  def test_form_add_invalid_decoder_number_no_redirect(self, client, sample_data):
    """测试表单添加编号格式错误时不重定向（验证失败）"""
    data = _base_locomotive_data(decoder_number='0', scale='HO')
    response = client.post('/locomotive', data=data, follow_redirects=False)
    assert response.status_code == 200
    assert '机车模型' in response.data.decode('utf-8')

  def test_form_add_duplicate_locomotive_number_no_redirect(self, client, sample_data):
    """测试表单添加重复机车号时不重定向（唯一性验证失败）"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', locomotive_number='5678'
      )
      db.session.add(loco)
      db.session.commit()

    data = _base_locomotive_data(locomotive_number='5678', scale='HO')
    response = client.post('/locomotive', data=data, follow_redirects=False)
    assert response.status_code == 200
    assert '机车模型' in response.data.decode('utf-8')

  def test_form_add_price_expression_calculated(self, client, sample_data):
    """测试表单添加机车时价格表达式被正确计算"""
    data = _base_locomotive_data(price='288+538', item_number='PRICE_EXPR')
    client.post('/locomotive', data=data, follow_redirects=True)

    with client.application.app_context():
      loco = Locomotive.query.filter_by(item_number='PRICE_EXPR').first()
      assert loco is not None
      assert loco.total_price == 826.0

  # --- POST /api/locomotive/add ---

  def test_api_add_success_returns_ok(self, client, sample_data):
    """测试 API 添加机车成功返回 200"""
    data = _base_locomotive_data(item_number='API_OK')
    response = client.post('/api/locomotive/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True
    assert 'id' in result

  def test_api_add_persists_data(self, client, sample_data):
    """测试 API 添加机车后数据库有记录"""
    data = _base_locomotive_data(item_number='API_PERSIST')
    client.post('/api/locomotive/add',
                data=json.dumps(data),
                content_type='application/json')

    with client.application.app_context():
      loco = Locomotive.query.filter_by(item_number='API_PERSIST').first()
      assert loco is not None

  def test_api_add_with_locomotive_number(self, client, sample_data):
    """测试 API 添加带机车号的机车"""
    data = _base_locomotive_data(
      locomotive_number='1234',
      decoder_number='1',
      item_number='API_NUM'
    )
    response = client.post('/api/locomotive/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True

  def test_api_add_invalid_locomotive_number_returns_400(self, client, sample_data):
    """测试 API 添加机车号格式错误返回 400"""
    data = _base_locomotive_data(locomotive_number='ABCD', scale='HO')
    response = client.post('/api/locomotive/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] is False

  def test_api_add_duplicate_locomotive_number_returns_400(self, client, sample_data):
    """测试 API 添加重复机车号返回 400"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', locomotive_number='8888'
      )
      db.session.add(loco)
      db.session.commit()

    data = _base_locomotive_data(locomotive_number='8888', scale='HO')
    response = client.post('/api/locomotive/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400

  # --- POST /api/locomotive/edit/<id> ---

  def test_api_edit_success(self, client, sample_data):
    """测试 API 编辑机车成功"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='EDIT_BEFORE'
      )
      db.session.add(loco)
      db.session.commit()
      locoId = loco.id

    data = _base_locomotive_data(item_number='EDIT_AFTER', price='999')
    response = client.post(f'/api/locomotive/edit/{locoId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True

    with client.application.app_context():
      updated = db.session.get(Locomotive, locoId)
      assert updated.item_number == 'EDIT_AFTER'
      assert updated.total_price == 999.0

  def test_api_edit_nonexistent_returns_500(self, client, sample_data):
    """测试 API 编辑不存在的机车返回 500（get_or_404 异常被泛 except 捕获）"""
    data = _base_locomotive_data()
    response = client.post('/api/locomotive/edit/99999',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 500

  def test_api_edit_validation_error_returns_400(self, client, sample_data):
    """测试 API 编辑机车验证失败返回 400"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO'
      )
      db.session.add(loco)
      db.session.commit()
      locoId = loco.id

    data = _base_locomotive_data(locomotive_number='INVALID', scale='HO')
    response = client.post(f'/api/locomotive/edit/{locoId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400

  def test_api_edit_self_unique_check_passes(self, client, sample_data):
    """测试 API 编辑时排除自身的唯一性检查通过"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', locomotive_number='7777', item_number='SELF_EDIT'
      )
      db.session.add(loco)
      db.session.commit()
      locoId = loco.id

    # Edit with same locomotive_number - should succeed (exclude self)
    data = _base_locomotive_data(
      locomotive_number='7777', scale='HO', item_number='SELF_EDIT_UPD'
    )
    response = client.post(f'/api/locomotive/edit/{locoId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200

  # --- POST /locomotive/delete/<id> ---

  def test_delete_success_redirects(self, client, sample_data):
    """测试删除机车成功后重定向"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='DEL_ME'
      )
      db.session.add(loco)
      db.session.commit()
      locoId = loco.id

    response = client.post(f'/locomotive/delete/{locoId}', follow_redirects=False)
    assert response.status_code == 302
    assert '/locomotive' in response.headers['Location']

  def test_delete_removes_from_db(self, client, sample_data):
    """测试删除机车后数据库无该记录"""
    with client.application.app_context():
      loco = Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='DEL_CONFIRM'
      )
      db.session.add(loco)
      db.session.commit()
      locoId = loco.id

    client.post(f'/locomotive/delete/{locoId}', follow_redirects=True)

    with client.application.app_context():
      deleted = db.session.get(Locomotive, locoId)
      assert deleted is None

  def test_delete_nonexistent_redirects(self, client, sample_data):
    """测试删除不存在的机车仍重定向（异常被捕获后仍重定向）"""
    response = client.post('/locomotive/delete/99999', follow_redirects=True)
    assert response.status_code == 200


# ============================================================
# Carriage route tests
# ============================================================

class TestCarriageRoutes:
  """车厢模型路由测试"""

  # --- GET /carriage ---

  def test_list_page_returns_200(self, client, sample_data):
    """测试 GET /carriage 返回列表页"""
    response = client.get('/carriage')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '车厢模型' in html

  def test_list_page_shows_existing_data(self, client, sample_data):
    """测试列表页显示已有车厢数据"""
    with client.application.app_context():
      cs = CarriageSet(
        brand_id=1, series_id=1, scale='HO',
        train_number='G999', item_number='CRG_LIST'
      )
      db.session.add(cs)
      db.session.commit()

    response = client.get('/carriage')
    assert response.status_code == 200
    assert 'G999' in response.data.decode('utf-8')

  # --- POST /carriage (form add) ---

  def test_form_add_success_redirects(self, client, sample_data):
    """测试表单添加车厢套装成功后重定向"""
    data = _base_carriage_data(item_number='FORM_CRG_1')
    response = client.post('/carriage', data=data, follow_redirects=False)
    assert response.status_code == 302
    assert '/carriage' in response.headers['Location']

  def test_form_add_persists_set_and_items(self, client, sample_data):
    """测试表单添加车厢套装后数据库有套装和车厢项"""
    data = _base_carriage_data(item_number='CRG_PERSIST')
    client.post('/carriage', data=data, follow_redirects=True)

    with client.application.app_context():
      cs = CarriageSet.query.filter_by(item_number='CRG_PERSIST').first()
      assert cs is not None
      assert cs.train_number == 'G123'
      assert cs.total_price == 800.0
      items = CarriageItem.query.filter_by(set_id=cs.id).all()
      assert len(items) == 1
      assert items[0].car_number == 'YZ-01'
      assert items[0].color == 'green'

  def test_form_add_multiple_items(self, client, sample_data):
    """测试表单添加车厢套装含多个车厢项"""
    data = _base_carriage_data(item_number='MULTI_ITEMS')
    data.update({
      'model_1': '1',
      'car_number_1': 'YZ-02',
      'color_1': 'blue',
      'light_model_id_1': ''
    })
    client.post('/carriage', data=data, follow_redirects=True)

    with client.application.app_context():
      cs = CarriageSet.query.filter_by(item_number='MULTI_ITEMS').first()
      assert cs is not None
      items = CarriageItem.query.filter_by(set_id=cs.id).all()
      assert len(items) == 2

  def test_form_add_invalid_car_number_renders_errors(self, client, sample_data):
    """测试表单添加车厢项车辆号格式错误时返回错误页"""
    data = _base_carriage_data(
      car_number_0='@#$', item_number='BAD_CAR_NUM'
    )
    response = client.post('/carriage', data=data, follow_redirects=False)
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '车辆号' in html or '格式错误' in html

  def test_form_add_empty_items_no_error(self, client, sample_data):
    """测试表单添加车厢套装不带车厢项时不报验证错误"""
    data = _base_carriage_data(item_number='NO_ITEMS')
    del data['model_0']
    del data['car_number_0']
    del data['color_0']
    del data['light_model_id_0']
    response = client.post('/carriage', data=data, follow_redirects=False)
    assert response.status_code == 302

  # --- POST /api/carriage/add ---

  def test_api_add_success_returns_ok(self, client, sample_data):
    """测试 API 添加车厢套装成功返回 200"""
    data = _base_carriage_data(item_number='API_CRG_OK')
    response = client.post('/api/carriage/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True
    assert 'id' in result

  def test_api_add_persists_set_and_items(self, client, sample_data):
    """测试 API 添加车厢套装后数据库有记录"""
    data = _base_carriage_data(item_number='API_CRG_P')
    client.post('/api/carriage/add',
                data=json.dumps(data),
                content_type='application/json')

    with client.application.app_context():
      cs = CarriageSet.query.filter_by(item_number='API_CRG_P').first()
      assert cs is not None
      items = CarriageItem.query.filter_by(set_id=cs.id).all()
      assert len(items) == 1

  def test_api_add_invalid_car_number_returns_400(self, client, sample_data):
    """测试 API 添加车厢项车辆号格式错误返回 400"""
    data = _base_carriage_data(car_number_0='@@@', item_number='BAD_API')
    response = client.post('/api/carriage/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] is False

  def test_api_add_multiple_items(self, client, sample_data):
    """测试 API 添加车厢套装含多个车厢项"""
    data = _base_carriage_data(item_number='API_MULTI')
    data.update({
      'model_1': '1',
      'car_number_1': 'RZ-03',
      'color_1': 'yellow',
      'light_model_id_1': ''
    })
    response = client.post('/api/carriage/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200

    with client.application.app_context():
      cs = CarriageSet.query.filter_by(item_number='API_MULTI').first()
      items = CarriageItem.query.filter_by(set_id=cs.id).all()
      assert len(items) == 2

  # --- POST /api/carriage/edit/<id> ---

  def test_api_edit_success(self, client, sample_data):
    """测试 API 编辑车厢套装成功"""
    with client.application.app_context():
      cs = CarriageSet(
        brand_id=1, series_id=1, scale='HO',
        train_number='G100', item_number='EDIT_CRG'
      )
      db.session.add(cs)
      db.session.commit()
      csId = cs.id

    data = _base_carriage_data(item_number='EDIT_CRG_UPD', train_number='G200')
    response = client.post(f'/api/carriage/edit/{csId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True

    with client.application.app_context():
      updated = db.session.get(CarriageSet, csId)
      assert updated.train_number == 'G200'

  def test_api_edit_replaces_items(self, client, sample_data):
    """测试 API 编辑车厢套装替换车厢项"""
    with client.application.app_context():
      cs = CarriageSet(
        brand_id=1, series_id=1, scale='HO',
        item_number='EDIT_ITEMS'
      )
      db.session.add(cs)
      db.session.commit()
      csId = cs.id
      # Add old item
      old_item = CarriageItem(
        set_id=csId, model_id=1, car_number='OLD-01',
        color='red'
      )
      db.session.add(old_item)
      db.session.commit()

    data = _base_carriage_data(item_number='EDIT_ITEMS')
    data['car_number_0'] = 'NEW-01'
    response = client.post(f'/api/carriage/edit/{csId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200

    with client.application.app_context():
      items = CarriageItem.query.filter_by(set_id=csId).all()
      assert len(items) == 1
      assert items[0].car_number == 'NEW-01'

  def test_api_edit_nonexistent_returns_500(self, client, sample_data):
    """测试 API 编辑不存在的车厢套装返回 500（get_or_404 异常被泛 except 捕获）"""
    data = _base_carriage_data()
    response = client.post('/api/carriage/edit/99999',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 500

  def test_api_edit_validation_error_returns_400(self, client, sample_data):
    """测试 API 编辑车厢验证失败返回 400"""
    with client.application.app_context():
      cs = CarriageSet(
        brand_id=1, series_id=1, scale='HO', item_number='VAL_CRG'
      )
      db.session.add(cs)
      db.session.commit()
      csId = cs.id

    data = _base_carriage_data(item_number='VAL_CRG', car_number_0='!!!')
    response = client.post(f'/api/carriage/edit/{csId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400

  # --- POST /carriage/delete/<id> ---

  def test_delete_success_redirects(self, client, sample_data):
    """测试删除车厢套装成功后重定向"""
    with client.application.app_context():
      cs = CarriageSet(
        brand_id=1, series_id=1, scale='HO', item_number='DEL_CRG'
      )
      db.session.add(cs)
      db.session.commit()
      csId = cs.id

    response = client.post(f'/carriage/delete/{csId}', follow_redirects=False)
    assert response.status_code == 302
    assert '/carriage' in response.headers['Location']

  def test_delete_cascades_items(self, client, sample_data):
    """测试删除车厢套装时级联删除车厢项"""
    with client.application.app_context():
      cs = CarriageSet(
        brand_id=1, series_id=1, scale='HO', item_number='CASCADE_CRG'
      )
      db.session.add(cs)
      db.session.commit()
      csId = cs.id
      item = CarriageItem(
        set_id=csId, model_id=1, car_number='CAS-01'
      )
      db.session.add(item)
      db.session.commit()
      itemId = item.id

    client.post(f'/carriage/delete/{csId}', follow_redirects=True)

    with client.application.app_context():
      deleted_set = db.session.get(CarriageSet, csId)
      assert deleted_set is None
      deleted_item = db.session.get(CarriageItem, itemId)
      assert deleted_item is None

  def test_delete_nonexistent_redirects(self, client, sample_data):
    """测试删除不存在的车厢套装仍重定向（异常被捕获后仍重定向）"""
    response = client.post('/carriage/delete/99999', follow_redirects=True)
    assert response.status_code == 200


# ============================================================
# Trainset route tests
# ============================================================

class TestTrainsetRoutes:
  """动车组模型路由测试"""

  # --- GET /trainset ---

  def test_list_page_returns_200(self, client, sample_data):
    """测试 GET /trainset 返回列表页"""
    response = client.get('/trainset')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '动车组模型' in html

  def test_list_page_shows_existing_data(self, client, sample_data):
    """测试列表页显示已有动车组数据"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', trainset_number='CRH001', item_number='TS_LIST'
      )
      db.session.add(ts)
      db.session.commit()

    response = client.get('/trainset')
    assert response.status_code == 200
    assert 'CRH001' in response.data.decode('utf-8')

  # --- POST /trainset (form add) ---

  def test_form_add_success_redirects(self, client, sample_data):
    """测试表单添加动车组成功后重定向"""
    data = _base_trainset_data(item_number='FORM_TS_1')
    response = client.post('/trainset', data=data, follow_redirects=False)
    assert response.status_code == 302
    assert '/trainset' in response.headers['Location']

  def test_form_add_persists_data(self, client, sample_data):
    """测试表单添加动车组后数据库有记录"""
    data = _base_trainset_data(item_number='TS_PERSIST')
    client.post('/trainset', data=data, follow_redirects=True)

    with client.application.app_context():
      ts = Trainset.query.filter_by(item_number='TS_PERSIST').first()
      assert ts is not None
      assert ts.scale == 'HO'
      assert ts.formation == 8
      assert ts.total_price == 1200.0

  def test_form_add_with_all_fields(self, client, sample_data):
    """测试表单添加动车组包含所有字段"""
    data = _base_trainset_data(
      trainset_number='3001',
      decoder_number='2',
      plaque='测试挂牌',
      color='白色',
      head_light='true',
      chip_interface_id='1',
      chip_model_id='1',
      item_number='FULL_TS'
    )
    client.post('/trainset', data=data, follow_redirects=True)

    with client.application.app_context():
      ts = Trainset.query.filter_by(item_number='FULL_TS').first()
      assert ts is not None
      assert ts.trainset_number == '3001'
      assert ts.decoder_number == '2'
      assert ts.plaque == '测试挂牌'
      assert ts.color == '白色'
      assert ts.head_light is True

  def test_form_add_invalid_trainset_number_renders_page(self, client, sample_data):
    """测试表单添加动车号格式错误时重新渲染页面（无错误消息显示）"""
    data = _base_trainset_data(trainset_number='AB', scale='HO')
    response = client.post('/trainset', data=data, follow_redirects=False)
    assert response.status_code == 200
    # 页面重新渲染但不会显示服务端错误消息（错误通过JS API处理）
  def test_form_add_duplicate_trainset_number_renders_errors(self, client, sample_data):
    """测试表单添加重复动车号时返回错误页"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', trainset_number='4001'
      )
      db.session.add(ts)
      db.session.commit()

    data = _base_trainset_data(trainset_number='4001', scale='HO')
    response = client.post('/trainset', data=data, follow_redirects=False)
    assert response.status_code == 200
    # 页面重新渲染，不显示服务端错误消息

  # --- POST /api/trainset/add ---

  def test_api_add_success_returns_ok(self, client, sample_data):
    """测试 API 添加动车组成功返回 200"""
    data = _base_trainset_data(item_number='API_TS_OK')
    response = client.post('/api/trainset/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True
    assert 'id' in result

  def test_api_add_persists_data(self, client, sample_data):
    """测试 API 添加动车组后数据库有记录"""
    data = _base_trainset_data(item_number='API_TS_P')
    client.post('/api/trainset/add',
                data=json.dumps(data),
                content_type='application/json')

    with client.application.app_context():
      ts = Trainset.query.filter_by(item_number='API_TS_P').first()
      assert ts is not None

  def test_api_add_invalid_trainset_number_returns_400(self, client, sample_data):
    """测试 API 添加动车号格式错误返回 400"""
    data = _base_trainset_data(trainset_number='XX', scale='HO')
    response = client.post('/api/trainset/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] is False

  def test_api_add_duplicate_trainset_number_returns_400(self, client, sample_data):
    """测试 API 添加重复动车号返回 400"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', trainset_number='5001'
      )
      db.session.add(ts)
      db.session.commit()

    data = _base_trainset_data(trainset_number='5001', scale='HO')
    response = client.post('/api/trainset/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400

  # --- POST /api/trainset/edit/<id> ---

  def test_api_edit_success(self, client, sample_data):
    """测试 API 编辑动车组成功"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='EDIT_TS'
      )
      db.session.add(ts)
      db.session.commit()
      tsId = ts.id

    data = _base_trainset_data(item_number='EDIT_TS_UPD', formation='16', price='2000')
    response = client.post(f'/api/trainset/edit/{tsId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True

    with client.application.app_context():
      updated = db.session.get(Trainset, tsId)
      assert updated.formation == 16
      assert updated.total_price == 2000.0

  def test_api_edit_nonexistent_returns_500(self, client, sample_data):
    """测试 API 编辑不存在的动车组返回 500（get_or_404 异常被泛 except 捕获）"""
    data = _base_trainset_data()
    response = client.post('/api/trainset/edit/99999',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 500

  def test_api_edit_validation_error_returns_400(self, client, sample_data):
    """测试 API 编辑动车组验证失败返回 400"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO'
      )
      db.session.add(ts)
      db.session.commit()
      tsId = ts.id

    data = _base_trainset_data(trainset_number='INVALID', scale='HO')
    response = client.post(f'/api/trainset/edit/{tsId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 400

  def test_api_edit_self_unique_check_passes(self, client, sample_data):
    """测试 API 编辑时排除自身的唯一性检查通过"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', trainset_number='6001', item_number='SELF_TS'
      )
      db.session.add(ts)
      db.session.commit()
      tsId = ts.id

    data = _base_trainset_data(
      trainset_number='6001', scale='HO', item_number='SELF_TS_UPD'
    )
    response = client.post(f'/api/trainset/edit/{tsId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200

  # --- POST /trainset/delete/<id> ---

  def test_delete_success_redirects(self, client, sample_data):
    """测试删除动车组成功后重定向"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='DEL_TS'
      )
      db.session.add(ts)
      db.session.commit()
      tsId = ts.id

    response = client.post(f'/trainset/delete/{tsId}', follow_redirects=False)
    assert response.status_code == 302
    assert '/trainset' in response.headers['Location']

  def test_delete_removes_from_db(self, client, sample_data):
    """测试删除动车组后数据库无该记录"""
    with client.application.app_context():
      ts = Trainset(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='DEL_TS_CONFIRM'
      )
      db.session.add(ts)
      db.session.commit()
      tsId = ts.id

    client.post(f'/trainset/delete/{tsId}', follow_redirects=True)

    with client.application.app_context():
      deleted = db.session.get(Trainset, tsId)
      assert deleted is None

  def test_delete_nonexistent_redirects(self, client, sample_data):
    """测试删除不存在的动车组仍重定向（异常被捕获后仍重定向)"""
    response = client.post('/trainset/delete/99999', follow_redirects=True)
    assert response.status_code == 200


# ============================================================
# Locomotive Head route tests
# ============================================================

class TestLocomotiveHeadRoutes:
  """先头车模型路由测试"""

  # --- GET /locomotive-head ---

  def test_list_page_returns_200(self, client, sample_data):
    """测试 GET /locomotive-head 返回列表页"""
    response = client.get('/locomotive-head')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '先头车模型' in html

  def test_list_page_shows_existing_data(self, client, sample_data):
    """测试列表页显示已有先头车数据"""
    with client.application.app_context():
      head = LocomotiveHead(
        model_id=1, brand_id=1, scale='HO', item_number='LH_LIST'
      )
      db.session.add(head)
      db.session.commit()

    response = client.get('/locomotive-head')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'LH_LIST' in html

  # --- POST /locomotive-head (form add) ---

  def test_form_add_success_redirects(self, client, sample_data):
    """测试表单添加先头车成功后重定向"""
    data = _base_locomotive_head_data(item_number='FORM_LH_1')
    response = client.post('/locomotive-head', data=data, follow_redirects=False)
    assert response.status_code == 302
    assert '/locomotive-head' in response.headers['Location']

  def test_form_add_persists_data(self, client, sample_data):
    """测试表单添加先头车后数据库有记录"""
    data = _base_locomotive_head_data(item_number='LH_PERSIST')
    client.post('/locomotive-head', data=data, follow_redirects=True)

    with client.application.app_context():
      head = LocomotiveHead.query.filter_by(item_number='LH_PERSIST').first()
      assert head is not None
      assert head.scale == 'HO'
      assert head.total_price == 350.0

  def test_form_add_with_all_fields(self, client, sample_data):
    """测试表单添加先头车包含所有字段"""
    data = _base_locomotive_head_data(
      special_color='红色特涂',
      head_light='true',
      item_number='FULL_LH'
    )
    client.post('/locomotive-head', data=data, follow_redirects=True)

    with client.application.app_context():
      head = LocomotiveHead.query.filter_by(item_number='FULL_LH').first()
      assert head is not None
      assert head.special_color == '红色特涂'
      assert head.head_light is True

  def test_form_add_price_expression_calculated(self, client, sample_data):
    """测试表单添加先头车时价格表达式被正确计算"""
    data = _base_locomotive_head_data(price='200+100', item_number='PRICE_LH')
    client.post('/locomotive-head', data=data, follow_redirects=True)

    with client.application.app_context():
      head = LocomotiveHead.query.filter_by(item_number='PRICE_LH').first()
      assert head is not None
      assert head.total_price == 300.0

  # --- POST /api/locomotive-head/add ---

  def test_api_add_success_returns_ok(self, client, sample_data):
    """测试 API 添加先头车成功返回 200"""
    data = _base_locomotive_head_data(item_number='API_LH_OK')
    response = client.post('/api/locomotive-head/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True
    assert 'id' in result

  def test_api_add_persists_data(self, client, sample_data):
    """测试 API 添加先头车后数据库有记录"""
    data = _base_locomotive_head_data(item_number='API_LH_P')
    client.post('/api/locomotive-head/add',
                data=json.dumps(data),
                content_type='application/json')

    with client.application.app_context():
      head = LocomotiveHead.query.filter_by(item_number='API_LH_P').first()
      assert head is not None

  def test_api_add_with_special_color(self, client, sample_data):
    """测试 API 添加先头车带特涂字段"""
    data = _base_locomotive_head_data(
      special_color='蓝色特涂', item_number='SPEC_LH'
    )
    response = client.post('/api/locomotive-head/add',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200

    with client.application.app_context():
      head = LocomotiveHead.query.filter_by(item_number='SPEC_LH').first()
      assert head.special_color == '蓝色特涂'

  # --- POST /api/locomotive-head/edit/<id> ---

  def test_api_edit_success(self, client, sample_data):
    """测试 API 编辑先头车成功"""
    with client.application.app_context():
      head = LocomotiveHead(
        model_id=1, brand_id=1, scale='HO', item_number='EDIT_LH'
      )
      db.session.add(head)
      db.session.commit()
      headId = head.id

    data = _base_locomotive_head_data(
      item_number='EDIT_LH_UPD', special_color='绿色', price='888'
    )
    response = client.post(f'/api/locomotive-head/edit/{headId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True

    with client.application.app_context():
      updated = db.session.get(LocomotiveHead, headId)
      assert updated.special_color == '绿色'
      assert updated.total_price == 888.0

  def test_api_edit_nonexistent_returns_500(self, client, sample_data):
    """测试 API 编辑不存在的先头车返回 500（get_or_404 异常被泛 except 捕获）"""
    data = _base_locomotive_head_data()
    response = client.post('/api/locomotive-head/edit/99999',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 500

  def test_api_edit_updates_head_light(self, client, sample_data):
    """测试 API 编辑先头车更新头车灯"""
    with client.application.app_context():
      head = LocomotiveHead(
        model_id=1, brand_id=1, scale='HO', head_light=True,
        item_number='LIGHT_LH'
      )
      db.session.add(head)
      db.session.commit()
      headId = head.id

    data = _base_locomotive_head_data(
      item_number='LIGHT_LH_UPD', head_light='false'
    )
    response = client.post(f'/api/locomotive-head/edit/{headId}',
                           data=json.dumps(data),
                           content_type='application/json')
    assert response.status_code == 200

    with client.application.app_context():
      updated = db.session.get(LocomotiveHead, headId)
      assert updated.head_light is False

  # --- POST /locomotive-head/delete/<id> ---

  def test_delete_success_redirects(self, client, sample_data):
    """测试删除先头车成功后重定向"""
    with client.application.app_context():
      head = LocomotiveHead(
        model_id=1, brand_id=1, scale='HO', item_number='DEL_LH'
      )
      db.session.add(head)
      db.session.commit()
      headId = head.id

    response = client.post(f'/locomotive-head/delete/{headId}', follow_redirects=False)
    assert response.status_code == 302
    assert '/locomotive-head' in response.headers['Location']

  def test_delete_removes_from_db(self, client, sample_data):
    """测试删除先头车后数据库无该记录"""
    with client.application.app_context():
      head = LocomotiveHead(
        model_id=1, brand_id=1, scale='HO', item_number='DEL_LH_C'
      )
      db.session.add(head)
      db.session.commit()
      headId = head.id

    client.post(f'/locomotive-head/delete/{headId}', follow_redirects=True)

    with client.application.app_context():
      deleted = db.session.get(LocomotiveHead, headId)
      assert deleted is None

  def test_delete_nonexistent_redirects(self, client, sample_data):
    """测试删除不存在的先头车仍重定向 (异常被捕获后仍重定向)"""
    response = client.post('/locomotive-head/delete/99999', follow_redirects=True)
    assert response.status_code == 200


# ============================================================
# System route tests
# ============================================================

class TestSystemRoutes:
  """系统维护路由测试"""

  def test_system_page_returns_200(self, client):
    """测试 GET /system 返回系统维护页"""
    response = client.get('/system')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert '系统维护' in html

  def test_system_page_contains_buttons(self, client):
    """测试系统维护页包含操作按钮"""
    response = client.get('/system')
    html = response.data.decode('utf-8')
    assert '导出模型数据' in html
    assert '导出系统信息' in html
    assert '全部导出' in html
    assert '从 Excel 导入数据' in html
    assert '重新初始化数据库' in html

  def test_reinit_requires_confirm_header(self, client, sample_data):
    """缺少 X-Confirm 头时返回 400，防误触"""
    response = client.post('/system/reinit')
    assert response.status_code == 400

  def test_reinit_database_success(self, client, sample_data, monkeypatch):
    """测试重新初始化数据库成功

    mock subprocess.run 以避免真实子进程——既有实现既依赖系统 Python 环境
    （需 Flask 已安装），又会副作用操作开发库 instance/train_model.db
    （init_db.py 用默认 Config）。此处只验证业务逻辑：
    1. 当前测试库的业务数据被清空；
    2. subprocess 以当前解释器（sys.executable）调用 init_db.py。
    """
    from routes import system as system_module

    # 先写入数据，验证 reinit 会清空
    with client.application.app_context():
      db.session.add(Locomotive(
        series_id=1, power_type_id=1, model_id=1, brand_id=1,
        scale='HO', item_number='REINIT_TEST'
      ))
      db.session.commit()
      assert Locomotive.query.count() >= 1

    # mock subprocess.run，避免真实子进程的环境依赖与副作用
    subprocess_calls = []

    def fake_run(cmd, *args, **kwargs):
      subprocess_calls.append(cmd)
      return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(system_module.subprocess, 'run', fake_run)

    response = client.post('/system/reinit', headers={'X-Confirm': 'REINIT'})
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] is True
    assert '初始化成功' in result['message']

    # 验证以当前解释器调用 init_db.py（修复后用 sys.executable）
    assert len(subprocess_calls) == 1
    assert subprocess_calls[0][0] == sys.executable
    assert subprocess_calls[0][1] == 'init_db.py'

    # 验证当前数据库业务数据已被清空
    with client.application.app_context():
      assert Locomotive.query.count() == 0

  def test_reinit_database_subprocess_failure_returns_500(self, client, sample_data, monkeypatch):
    """测试 subprocess 失败时返回 500 错误"""
    from routes import system as system_module

    def fake_run(cmd, *args, **kwargs):
      raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(system_module.subprocess, 'run', fake_run)

    response = client.post('/system/reinit', headers={'X-Confirm': 'REINIT'})
    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['success'] is False
