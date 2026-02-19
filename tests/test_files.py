"""
文件管理功能测试
"""
import pytest
import os
import io
import tempfile
import shutil
from datetime import date

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import TestConfig
from models import db, ModelFile
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead
from models import Brand, Depot, Merchant
from models import LocomotiveSeries, LocomotiveModel, TrainsetSeries, TrainsetModel, PowerType


@pytest.fixture
def file_test_app():
  """创建带临时文件目录的测试应用"""
  # 创建临时目录
  temp_dir = tempfile.mkdtemp()

  # 创建自定义测试配置
  class FileTestConfig(TestConfig):
    DATA_DIR = temp_dir
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {
      'image': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
      'manual': {'pdf', 'doc', 'docx', 'zip'},
      'function_table': {'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    }

  app = create_app(FileTestConfig)

  with app.app_context():
    db.create_all()
    # 创建测试数据
    _create_test_data()
    yield app
    db.drop_all()

  # 清理临时目录
  if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_test_client(file_test_app):
  """创建测试客户端"""
  return file_test_app.test_client()


def _create_test_data():
  """创建测试数据"""
  # 品牌
  brand = Brand(name='测试品牌', search_url='https://example.com/search?q={query}')
  db.session.add(brand)

  # 机务段
  depot = Depot(name='测试机务段')
  db.session.add(depot)

  # 商家
  merchant = Merchant(name='测试商家')
  db.session.add(merchant)

  # 动力类型
  power_type = PowerType(name='电力')
  db.session.add(power_type)

  # 机车系列和型号
  loco_series = LocomotiveSeries(name='SS系列')
  db.session.add(loco_series)

  # 动车组系列和型号
  trainset_series = TrainsetSeries(name='CRH系列')
  db.session.add(trainset_series)

  db.session.commit()

  # 创建型号
  loco_model = LocomotiveModel(name='SS4', series_id=1, power_type_id=1)
  db.session.add(loco_model)

  trainset_model = TrainsetModel(name='CRH380A', series_id=1, power_type_id=1)
  db.session.add(trainset_model)

  db.session.commit()

  # 创建机车
  locomotive = Locomotive(
    model_id=1,
    brand_id=1,
    scale='HO',
    item_number='TEST001',
    purchase_date=date.today()
  )
  db.session.add(locomotive)

  # 创建动车组
  trainset = Trainset(
    model_id=1,
    brand_id=1,
    scale='HO',
    item_number='TEST002',
    purchase_date=date.today()
  )
  db.session.add(trainset)

  # 创建先头车
  locomotive_head = LocomotiveHead(
    model_id=1,
    brand_id=1,
    scale='HO',
    item_number='TEST003',
    purchase_date=date.today()
  )
  db.session.add(locomotive_head)

  # 创建车厢套装
  carriage_set = CarriageSet(
    brand_id=1,
    scale='HO',
    item_number='TEST004',
    purchase_date=date.today()
  )
  db.session.add(carriage_set)

  db.session.commit()


class TestFileUpload:
  """文件上传测试"""

  def test_upload_image_success(self, file_test_app, file_test_client):
    """测试上传图片成功"""
    with file_test_app.app_context():
      # 创建测试图片
      image_data = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
      image_data.name = 'test.jpg'

      response = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'image',
          'file': (image_data, 'test.jpg', 'image/jpeg')
        },
        content_type='multipart/form-data'
      )

      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True
      assert data['file']['file_type'] == 'image'

  def test_upload_function_table_success(self, file_test_app, file_test_client):
    """测试上传数码功能表成功"""
    with file_test_app.app_context():
      pdf_data = io.BytesIO(b'%PDF-1.4' + b'\x00' * 100)
      pdf_data.name = 'test.pdf'

      response = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'function_table',
          'file': (pdf_data, 'test.pdf', 'application/pdf')
        },
        content_type='multipart/form-data'
      )

      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True
      assert data['file']['file_type'] == 'function_table'

  def test_upload_function_table_to_locomotive_head_forbidden(self, file_test_app, file_test_client):
    """测试先头车不能上传数码功能表"""
    with file_test_app.app_context():
      pdf_data = io.BytesIO(b'%PDF-1.4' + b'\x00' * 100)
      pdf_data.name = 'test.pdf'

      response = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive_head',
          'model_id': 1,
          'file_type': 'function_table',
          'file': (pdf_data, 'test.pdf', 'application/pdf')
        },
        content_type='multipart/form-data'
      )

      assert response.status_code == 400
      data = response.get_json()
      assert data['success'] is False
      assert '先头车' in data['error']

  def test_upload_manual_success(self, file_test_app, file_test_client):
    """测试上传说明书成功"""
    with file_test_app.app_context():
      pdf_data = io.BytesIO(b'%PDF-1.4' + b'\x00' * 100)
      pdf_data.name = 'manual.pdf'

      response = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'manual',
          'file': (pdf_data, 'manual.pdf', 'application/pdf')
        },
        content_type='multipart/form-data'
      )

      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True

  def test_upload_invalid_file_type(self, file_test_app, file_test_client):
    """测试上传不支持的文件类型"""
    with file_test_app.app_context():
      # 创建一个不在允许列表中的文件
      file_data = io.BytesIO(b'test content')
      file_data.name = 'test.exe'

      response = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'image',
          'file': (file_data, 'test.exe', 'application/octet-stream')
        },
        content_type='multipart/form-data'
      )

      assert response.status_code == 400
      data = response.get_json()
      assert data['success'] is False

  def test_upload_image_replaces_old(self, file_test_app, file_test_client):
    """测试上传新图片会替换旧图片"""
    with file_test_app.app_context():
      # 第一次上传
      image_data1 = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x01' * 100)
      response1 = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'image',
          'file': (image_data1, 'test1.jpg', 'image/jpeg')
        },
        content_type='multipart/form-data'
      )
      assert response1.status_code == 200
      file1_id = response1.get_json()['file']['id']

      # 第二次上传（应该替换第一次的）
      image_data2 = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x02' * 100)
      response2 = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'image',
          'file': (image_data2, 'test2.jpg', 'image/jpeg')
        },
        content_type='multipart/form-data'
      )
      assert response2.status_code == 200

      # 检查只有一个图片记录
      files = ModelFile.query.filter_by(
        model_type='locomotive',
        model_id=1,
        file_type='image'
      ).all()
      assert len(files) == 1
      assert files[0].id != file1_id  # 新记录的 ID 应该不同


class TestFileList:
  """文件列表测试"""

  def test_list_files_empty(self, file_test_app, file_test_client):
    """测试获取空文件列表"""
    with file_test_app.app_context():
      response = file_test_client.get('/api/files/list/locomotive/1')

      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True
      assert data['files']['image'] is None
      assert data['files']['function_table'] is None
      assert data['files']['manual'] == []

  def test_list_files_with_data(self, file_test_app, file_test_client):
    """测试获取有文件的列表"""
    with file_test_app.app_context():
      # 先上传一个文件
      image_data = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
      file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'image',
          'file': (image_data, 'test.jpg', 'image/jpeg')
        },
        content_type='multipart/form-data'
      )

      # 获取列表
      response = file_test_client.get('/api/files/list/locomotive/1')

      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True
      assert data['files']['image'] is not None
      assert data['files']['image']['original_filename'] == 'test.jpg'


class TestFileDelete:
  """文件删除测试"""

  def test_delete_file_success(self, file_test_app, file_test_client):
    """测试删除文件成功"""
    with file_test_app.app_context():
      # 先上传一个文件
      image_data = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
      upload_response = file_test_client.post(
        '/api/files/upload',
        data={
          'model_type': 'locomotive',
          'model_id': 1,
          'file_type': 'image',
          'file': (image_data, 'test.jpg', 'image/jpeg')
        },
        content_type='multipart/form-data'
      )
      file_id = upload_response.get_json()['file']['id']

      # 删除文件
      delete_response = file_test_client.delete(f'/api/files/delete/{file_id}')

      assert delete_response.status_code == 200
      data = delete_response.get_json()
      assert data['success'] is True

      # 验证文件已删除
      file_record = ModelFile.query.get(file_id)
      assert file_record is None


class TestModelDetail:
  """模型详情测试"""

  def test_get_model_detail(self, file_test_app, file_test_client):
    """测试获取模型详情"""
    with file_test_app.app_context():
      response = file_test_client.get('/api/files/model/locomotive/1')

      assert response.status_code == 200
      data = response.get_json()
      assert data['success'] is True
      assert data['model']['type'] == 'locomotive'
      assert 'attributes' in data['model']
      assert 'files' in data['model']


class TestModelFileModel:
  """ModelFile 模型测试"""

  def test_to_dict(self, file_test_app):
    """测试 to_dict 方法"""
    with file_test_app.app_context():
      # 创建文件记录
      file_record = ModelFile(
        model_type='locomotive',
        model_id=1,
        file_type='image',
        file_path='locomotive/test_brand_TEST001/test.jpg',
        original_filename='test.jpg',
        file_size=1024,
        mime_type='image/jpeg'
      )
      db.session.add(file_record)
      db.session.commit()

      # 测试 to_dict
      result = file_record.to_dict()
      assert result['model_type'] == 'locomotive'
      assert result['model_id'] == 1
      assert result['file_type'] == 'image'
      assert result['original_filename'] == 'test.jpg'
      assert result['file_size'] == 1024


class TestFileSync:
  """文件同步测试"""

  def test_sync_directory(self, file_test_app):
    """测试目录同步功能"""
    with file_test_app.app_context():
      from utils.file_sync import sync_data_directory

      # 创建手动文件（模拟手动添加的文件）
      data_dir = file_test_app.config['DATA_DIR']
      loco_dir = os.path.join(data_dir, 'locomotive', '测试品牌_TEST001')
      os.makedirs(loco_dir, exist_ok=True)

      # 创建测试图片文件
      test_file_path = os.path.join(loco_dir, '测试品牌_TEST001.jpg')
      with open(test_file_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

      # 执行同步
      sync_data_directory()

      # 验证数据库中有记录
      file_record = ModelFile.query.filter_by(
        model_type='locomotive',
        model_id=1,
        file_type='image'
      ).first()

      assert file_record is not None
      assert file_record.original_filename == '测试品牌_TEST001.jpg'
