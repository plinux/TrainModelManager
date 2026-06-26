"""应用安全测试：配置 fail-fast（P1-1）"""
import pytest
from app import create_app


class TestCreateAppSecurity:
  def test_production_requires_secret_key(self, monkeypatch):
    """生产环境未设置 SECRET_KEY 时，create_app 必须 fail-fast"""
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
      create_app()
