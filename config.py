import os


class Config:
    """应用配置类"""
    # 数据库配置：支持 SQLite 和 MySQL
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

    if DB_TYPE == 'mysql':
        MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
        MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
        MYSQL_USER = os.getenv('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
        MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'train_model_manager')
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        )
    else:
        # 默认使用 SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///train_model.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


class TestConfig(Config):
    """测试配置类 - 使用内存数据库"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
