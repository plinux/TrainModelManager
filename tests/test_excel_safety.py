"""
Excel 导入安全测试（P0-4）

验证 utils/excel_safety.py 的校验逻辑与导入端点对非法文件的拒绝。
"""
import io
import pytest
from openpyxl import Workbook
from utils.excel_safety import validate_excel_upload


class NamedBytesIO(io.BytesIO):
  """带 filename 属性的 BytesIO，模拟 werkzeug FileStorage 供 openpyxl 读取。"""
  def __init__(self, content, filename):
    super().__init__(content)
    self.filename = filename


def _make_xlsx_bytes(rows=2, cols=2):
  wb = Workbook()
  ws = wb.active
  for r in range(1, rows + 1):
    for c in range(1, cols + 1):
      ws.cell(row=r, column=c, value=f'{r}-{c}')
  buf = io.BytesIO()
  wb.save(buf)
  return buf.getvalue()


class TestValidateExcelUpload:
  def test_rejects_non_xlsx_extension(self):
    """旧 .xls 格式必须被拒（openpyxl 不支持，否则会 500）"""
    fs = NamedBytesIO(b'fake', 'evil.xls')
    with pytest.raises(ValueError, match='xlsx'):
      validate_excel_upload(fs)

  def test_rejects_empty_filename(self):
    fs = NamedBytesIO(b'', '')
    with pytest.raises(ValueError):
      validate_excel_upload(fs)

  def test_accepts_valid_xlsx(self):
    fs = NamedBytesIO(_make_xlsx_bytes(3, 2), 'data.xlsx')
    wb = validate_excel_upload(fs)
    assert wb is not None
    wb.close()


class TestImportEndpointFileCheck:
  def test_import_rejects_xls_extension(self, client, sample_data):
    """导入端点对非 .xlsx 文件返回 400，而非 500"""
    data = {'file': (io.BytesIO(b'fake'), 'evil.xls'), 'mode': 'preview'}
    resp = client.post('/api/import/excel', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False
