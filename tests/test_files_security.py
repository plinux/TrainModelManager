"""
文件安全测试：路径遍历防护（P0-1）

验证 utils/file_sync.py 的 sanitize_path_segment / safe_join_within / get_absolute_file_path
能阻止路径遍历，确保文件读写删操作不会越出 DATA_DIR。
"""
import os
import pytest
from utils.file_sync import sanitize_path_segment, safe_join_within, get_absolute_file_path


class TestSanitizePathSegment:
  """路径段净化单元测试"""

  def test_replaces_path_separators(self):
    """路径分隔符必须被替换，防止目录跳转"""
    assert '/' not in sanitize_path_segment('a/b/c')
    assert '\\' not in sanitize_path_segment('a\\b\\c')

  def test_strips_control_chars(self):
    """控制字符（含空字符）必须被去除"""
    assert sanitize_path_segment('a\x00b\x01c') == 'abc'

  def test_strips_leading_dots(self):
    """前导点必须被去除，防隐藏文件/相对跳转"""
    assert not sanitize_path_segment('..hidden').startswith('.')
    assert not sanitize_path_segment('.bashrc').startswith('.')

  def test_preserves_chinese(self):
    """中文等普通字符必须保留（品牌缩写/货号可能含）"""
    assert sanitize_path_segment('百万城_HXD3D001') == '百万城_HXD3D001'

  def test_empty_returns_underscore(self):
    """空输入返回占位符，避免拼出 base 本身"""
    assert sanitize_path_segment('') == '_'
    assert sanitize_path_segment(None) == '_'


class TestSafeJoinWithin:
  """路径拼接边界校验单元测试"""

  def test_normal_path_joins_correctly(self, tmp_path):
    base = str(tmp_path)
    result = safe_join_within(base, 'locomotive', 'BWC_001')
    assert os.path.realpath(result) == os.path.realpath(
      os.path.join(base, 'locomotive', 'BWC_001'))

  def test_traversal_input_stays_within_base(self, tmp_path):
    """各种路径遍历输入经净化后必须仍在 base 目录内"""
    base = str(tmp_path)
    base_real = os.path.realpath(base)
    malicious_inputs = [
      '../../../etc/passwd',
      '..\\..\\windows\\system32',
      '/etc/passwd',
      'locomotive/../../etc',
      '....//....//etc',
    ]
    for malicious in malicious_inputs:
      result = safe_join_within(base, malicious)
      result_real = os.path.realpath(result)
      assert result_real == base_real or result_real.startswith(base_real + os.sep), \
        f'路径越界: {malicious!r} -> {result_real}'

  def test_empty_parts_raises(self, tmp_path):
    with pytest.raises(ValueError):
      safe_join_within(str(tmp_path))


class TestGetAbsoluteFilePath:
  """get_absolute_file_path 必须把结果限制在 DATA_DIR 内"""

  def test_normal_relative_path(self, app):
    with app.app_context():
      result = get_absolute_file_path('locomotive/BWC_001/BWC_001.jpg')
      data_dir_real = os.path.realpath(app.config.get('DATA_DIR'))
      assert os.path.realpath(result).startswith(data_dir_real + os.sep)


class TestEndpointPathTraversal:
  """端到端：恶意 file_path 不能读取 DATA_DIR 外的文件"""

  def test_download_malicious_path_does_not_leak(self, client, app, sample_data, tmp_path):
    """DB 中存指向 DATA_DIR 外的恶意 file_path，download 不得返回其内容"""
    from models import ModelFile, db
    # 在 DATA_DIR 外放置标记文件
    secret = tmp_path / 'secret.txt'
    secret.write_text('TOP_SECRET_CONTENT_12345')

    with app.app_context():
      data_dir = os.path.realpath(app.config.get('DATA_DIR'))
      rel = os.path.relpath(str(secret), data_dir)  # 形如 ../../tmp/xxx/secret.txt
      mf = ModelFile(
        model_type='locomotive', model_id=1, file_type='image',
        file_path=rel, original_filename='evil.jpg',
        mime_type='image/jpeg'
      )
      db.session.add(mf)
      db.session.commit()
      fid = mf.id

    resp = client.get(f'/api/files/download/{fid}')
    # 关键：净化后路径被限制在 DATA_DIR 内，读不到 secret 文件
    assert b'TOP_SECRET_CONTENT_12345' not in resp.data


class TestDeleteModelFiles:
  """删除模型时清理关联文件和功能键（P2-2）"""

  def test_delete_clears_files_and_function_keys(self, app):
    from utils.file_cleanup import delete_model_files
    from models import ModelFile, FunctionKey, db
    with app.app_context():
      db.session.add_all([
        ModelFile(model_type='locomotive', model_id=999, file_type='image',
                  file_path='locomotive/X_999/X.jpg', original_filename='X.jpg'),
        FunctionKey(model_type='locomotive', model_id=999, key_number=0, function_name='test'),
      ])
      db.session.commit()
      delete_model_files('locomotive', 999)
      db.session.commit()
      assert ModelFile.query.filter_by(model_type='locomotive', model_id=999).count() == 0
      assert FunctionKey.query.filter_by(model_type='locomotive', model_id=999).count() == 0
