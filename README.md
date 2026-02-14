# 火车模型管理系统

用于管理火车模型藏品、统计和展示的 Web 应用。

## 功能特性

- 支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型
- 自动填充：选择车型后自动填充系列和类型
- 唯一性验证：同一比例内的机车号、编号等唯一性检查
- 价格表达式：支持 "288+538" 形式的价格计算
- 车厢套装：支持动态添加/删除车厢
- 统计汇总：展示各类型的花费统计
- 选项维护：集中管理所有下拉选项

## 技术栈

- Python 3.x
- Flask
- SQLAlchemy
- MySQL / SQLite

## 安装依赖

```bash
pip install -r requirements.txt
```

## 数据库初始化

```bash
python init_db.py
```

## 启动应用

```bash
python app.py
```

## 访问系统

浏览器打开：http://localhost:5000

## 切换数据库

默认使用 SQLite。要使用 MySQL，设置环境变量：

```bash
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=train_model_manager
```

## 依赖组件

- Flask==3.0.0
- Flask-SQLAlchemy==3.1.1
- PyMySQL==1.1.0
- cryptography==41.0.7
