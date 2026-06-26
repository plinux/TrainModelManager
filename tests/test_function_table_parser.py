"""
数码功能表解析模块测试
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import TestConfig
from models import db, FunctionKey
from models import Locomotive, Brand, LocomotiveSeries, LocomotiveModel, PowerType


@pytest.fixture
def parser_app():
  """创建测试应用"""
  app = create_app(TestConfig)
  with app.app_context():
    db.create_all()
    _create_test_data()
    yield app
    db.drop_all()


def _create_test_data():
  """创建测试数据"""
  brand = Brand(name='测试品牌', abbreviation='TB')
  db.session.add(brand)
  power_type = PowerType(name='电力')
  db.session.add(power_type)
  series = LocomotiveSeries(name='测试系列')
  db.session.add(series)
  db.session.commit()
  model = LocomotiveModel(name='SS4', series_id=1, power_type_id=1)
  db.session.add(model)
  db.session.commit()
  loco = Locomotive(model_id=1, brand_id=1, scale='HO', item_number='TEST001')
  db.session.add(loco)
  db.session.commit()


class TestNormalizeParsedKeys:
  """测试解析结果标准化"""

  def test_normalize_standard_keys(self, parser_app):
    """测试标准化标准格式的键"""
    with parser_app.app_context():
      from utils.function_table_parser import _normalize_parsed_keys
      raw = [
        {'key': 0, 'name': '头尾灯', 'description': ''},
        {'key': 1, 'name': '鸣笛', 'description': '短按'},
      ]
      result = _normalize_parsed_keys(raw)
      assert len(result) == 2
      assert result[0]['key_number'] == 0
      assert result[0]['function_name'] == '头尾灯'
      assert result[1]['description'] == '短按'

  def test_normalize_key_number_field(self, parser_app):
    """测试 key_number 字段名兼容"""
    with parser_app.app_context():
      from utils.function_table_parser import _normalize_parsed_keys
      raw = [
        {'key_number': 5, 'function_name': '制动', 'description': ''},
      ]
      result = _normalize_parsed_keys(raw)
      assert len(result) == 1
      assert result[0]['key_number'] == 5
      assert result[0]['function_name'] == '制动'

  def test_normalize_out_of_range_key(self, parser_app):
    """测试超出范围的键号被过滤"""
    with parser_app.app_context():
      from utils.function_table_parser import _normalize_parsed_keys
      raw = [
        {'key': 0, 'name': '合法', 'description': ''},
        {'key': 32, 'name': '超范围', 'description': ''},
        {'key': -1, 'name': '负数', 'description': ''},
      ]
      result = _normalize_parsed_keys(raw)
      assert len(result) == 1
      assert result[0]['key_number'] == 0

  def test_normalize_non_dict_items(self, parser_app):
    """测试非字典项被忽略"""
    with parser_app.app_context():
      from utils.function_table_parser import _normalize_parsed_keys
      raw = [
        {'key': 0, 'name': '合法', 'description': ''},
        'invalid',
        42,
      ]
      result = _normalize_parsed_keys(raw)
      assert len(result) == 1


class TestExtractKeysFromResponse:
  """测试从 AI 响应中提取功能键"""

  def test_extract_json_array(self, parser_app):
    """测试直接 JSON 数组"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_response
      text = '[{"key": 0, "name": "头尾灯", "description": ""}]'
      result = _extract_keys_from_response(text)
      assert result is not None
      assert len(result) == 1
      assert result[0]['function_name'] == '头尾灯'

  def test_extract_json_in_text(self, parser_app):
    """测试从文本中提取 JSON"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_response
      text = '以下是解析结果：\n[{"key": 0, "name": "头灯", "description": ""}, {"key": 1, "name": "鸣笛", "description": ""}]\n以上是所有功能键。'
      result = _extract_keys_from_response(text)
      assert result is not None
      assert len(result) == 2

  def test_extract_invalid_json(self, parser_app):
    """测试无效 JSON 返回 None"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_response
      text = '这不是有效的JSON'
      result = _extract_keys_from_response(text)
      assert result is None


class TestExtractKeysFromText:
  """测试从 OCR 文本中提取功能键"""

  def test_extract_standard_format(self, parser_app):
    """测试标准 F 键格式"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_text
      text = """F0 头尾灯
F1 鸣笛
F2 制动
F3 撒砂"""
      result = _extract_keys_from_text(text)
      assert result is not None
      assert len(result) == 4
      assert result[0]['key_number'] == 0
      assert result[0]['function_name'] == '头尾灯'
      assert result[3]['function_name'] == '撒砂'

  def test_extract_with_description(self, parser_app):
    """测试带说明的格式"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_text
      text = """F0  头尾灯  前后灯开关
F1  鸣笛  短按短鸣"""
      result = _extract_keys_from_text(text)
      assert result is not None
      assert len(result) == 2
      assert result[0]['description'] == '前后灯开关'

  def test_extract_function_prefix(self, parser_app):
    """测试 Function 前缀格式"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_text
      text = """Function0 头灯
Function1 尾灯"""
      result = _extract_keys_from_text(text)
      assert result is not None
      assert len(result) == 2
      assert result[0]['key_number'] == 0

  def test_extract_empty_text(self, parser_app):
    """测试空文本"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_text
      result = _extract_keys_from_text('')
      assert result is None

  def test_extract_no_f_keys(self, parser_app):
    """测试没有 F 键的文本"""
    with parser_app.app_context():
      from utils.function_table_parser import _extract_keys_from_text
      text = """这是标题
没有功能键
只有普通文字"""
      result = _extract_keys_from_text(text)
      assert result is None


class TestSaveAndGetFunctionKeys:
  """测试保存和获取功能键"""

  def test_save_keys(self, parser_app):
    """测试保存功能键"""
    with parser_app.app_context():
      from utils.function_table_parser import save_function_keys, get_function_keys
      parsed = [
        {'key_number': 0, 'function_name': '头尾灯', 'description': ''},
        {'key_number': 1, 'function_name': '鸣笛', 'description': '短按'},
      ]
      saved = save_function_keys('locomotive', 1, parsed)
      assert len(saved) == 2
      assert saved[0].function_name == '头尾灯'
      assert saved[1].description == '短按'

  def test_get_keys(self, parser_app):
    """测试获取功能键"""
    with parser_app.app_context():
      from utils.function_table_parser import save_function_keys, get_function_keys
      parsed = [
        {'key_number': 0, 'function_name': '头灯', 'description': ''},
      ]
      save_function_keys('locomotive', 1, parsed)
      keys = get_function_keys('locomotive', 1)
      assert len(keys) == 1
      assert keys[0]['function_name'] == '头灯'

  def test_save_overwrites_old(self, parser_app):
    """测试保存会覆盖旧数据"""
    with parser_app.app_context():
      from utils.function_table_parser import save_function_keys, get_function_keys
      # 第一次保存
      save_function_keys('locomotive', 1, [
        {'key_number': 0, 'function_name': '旧数据', 'description': ''},
      ])
      # 第二次保存
      save_function_keys('locomotive', 1, [
        {'key_number': 0, 'function_name': '新数据', 'description': ''},
        {'key_number': 1, 'function_name': '新增', 'description': ''},
      ])
      keys = get_function_keys('locomotive', 1)
      assert len(keys) == 2
      assert keys[0]['function_name'] == '新数据'


class TestUpdateFunctionKeys:
  """测试更新功能键"""

  def test_update_keys(self, parser_app):
    """测试更新功能键"""
    with parser_app.app_context():
      from utils.function_table_parser import update_function_keys, get_function_keys
      keys_data = [
        {'key_number': 0, 'function_name': '修改后', 'description': '更新'},
      ]
      updated = update_function_keys('locomotive', 1, keys_data)
      assert len(updated) == 1
      assert updated[0].function_name == '修改后'

      # 验证数据库
      keys = get_function_keys('locomotive', 1)
      assert keys[0]['function_name'] == '修改后'


class TestExportFunctionKeys:
  """测试导出功能键"""

  def test_export_empty(self, parser_app):
    """测试导出空数据"""
    with parser_app.app_context():
      from utils.function_table_parser import export_function_keys_excel
      buf = export_function_keys_excel('locomotive', 1, 'TB', 'TEST001')
      assert buf is not None
      assert buf.getvalue()  # 不为空

  def test_export_with_data(self, parser_app):
    """测试导出有数据的 Excel"""
    with parser_app.app_context():
      from utils.function_table_parser import save_function_keys, export_function_keys_excel
      save_function_keys('locomotive', 1, [
        {'key_number': 0, 'function_name': '头灯', 'description': ''},
        {'key_number': 1, 'function_name': '鸣笛', 'description': '短按'},
      ])
      buf = export_function_keys_excel('locomotive', 1, 'TB', 'TEST001')
      assert buf is not None
      data = buf.getvalue()
      assert len(data) > 0
      # 验证是 xlsx 格式 (ZIP magic bytes)
      assert data[:2] == b'PK'


class TestParseFunctionTableConfig:
  """测试解析配置"""

  def test_auto_mode_no_key_uses_local(self, parser_app):
    """测试 auto 模式无 API Key 时使用本地解析"""
    with parser_app.app_context():
      from utils.function_table_parser import parse_function_table
      # TestConfig 没有 AI_PARSER_API_KEY，应该走本地解析路径
      # 本地解析因缺少 OCR 引擎会返回 None，但不应抛异常
      # 我们用 mock 验证调用路径
      with patch('utils.function_table_parser._parse_with_local_ocr', return_value=[]) as mock_local:
        result = parse_function_table('/nonexistent/file.png', 'image/png')
        mock_local.assert_called_once()

  def test_ai_mode_with_key(self, parser_app):
    """测试 AI 模式使用 AI 解析"""
    with parser_app.app_context():
      parser_app.config['FUNCTION_TABLE_PARSER'] = 'ai'
      parser_app.config['AI_PARSER_API_KEY'] = 'test-key'
      from utils.function_table_parser import parse_function_table
      with patch('utils.function_table_parser._parse_with_ai', return_value=[]) as mock_ai:
        result = parse_function_table('/nonexistent/file.png', 'image/png')
        mock_ai.assert_called_once()
