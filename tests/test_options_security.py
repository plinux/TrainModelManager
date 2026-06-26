"""
信息维护安全测试：XSS 防护（P0-2）

验证 options.py 返回的冲突信息转义用户输入，防止存储型 XSS。
"""
import pytest
from models import Brand, db


class TestOptionsXssProtection:
  """品牌缩写等用户输入回显时必须 HTML 转义"""

  def test_brand_abbreviation_conflict_escaped(self, client, app):
    """编辑品牌触发缩写冲突时，响应不得包含未转义的脚本标签"""
    payload = "'<script>"  # 9 字符，符合 Brand.abbreviation String(10)
    with app.app_context():
      db.session.add(Brand(name='BrandA', abbreviation=payload))
      db.session.add(Brand(name='BrandB', abbreviation='BB'))
      db.session.commit()
      b_id = Brand.query.filter_by(name='BrandB').first().id

    # 编辑 BrandB，把缩写改成与 BrandA 相同的 XSS 样本 → 触发唯一冲突
    resp = client.post(f'/options/brand/edit/{b_id}', data={
      'name': 'BrandB', 'abbreviation': payload
    })
    body = resp.data.decode('utf-8')

    # payload 的尖括号必须被转义（不得原样回显为可执行标签）
    assert '&lt;script&gt;' in body
    # payload 原样（'<script>，含前导单引号）不得出现
    assert "'<script>" not in body
