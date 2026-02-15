# 火车模型管理系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个完整的火车模型管理系统，支持四种模型类型的 CRUD、自动填充、唯一性验证和统计汇总。

**Architecture:** 单体 Flask 应用，使用 SQLite/MySQL（可配置），SQLAlchemy ORM，纯 HTML + JavaScript 前端。

**Tech Stack:** Python 3.x, Flask, SQLAlchemy, Jinja2, MySQL/SQLite

---

### Task 1: 创建项目基础结构和配置文件

**Files:**
- Create: `requirements.txt`
- Create: `config.py`

**Step 1: Create requirements.txt**

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.0
cryptography==41.0.7
```

**Step 2: Create config.py**

```python
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
```

**Step 3: Commit**

```bash
git add requirements.txt config.py
git commit -m "feat: add project config and dependencies"
```

---

### Task 2: 创建数据库模型 - 参考数据表

**Files:**
- Create: `models.py`

**Step 1: Create models.py with reference data models**

```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date

db = SQLAlchemy()

# 参考数据表 - 跨模型共享
class PowerType(db.Model):
    """动力类型（机车和动车组共享）"""
    __tablename__ = 'power_type'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, unique=True, comment='动力类型名称')

class Brand(db.Model):
    """品牌（所有模型共享）"""
    __tablename__ = 'brand'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(100), nullable=False, unique=True, comment='品牌名称')

class ChipInterface(db.Model):
    """芯片接口（机车和动车组共享）"""
    __tablename__ = 'chip_interface'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, unique=True, comment='芯片接口名称')

class ChipModel(db.Model):
    """芯片型号（机车和动车组共享）"""
    __tablename__ = 'chip_model'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(100), nullable=False, unique=True, comment='芯片型号名称')

class Merchant(db.Model):
    """购买商家（所有模型共享）"""
    __tablename__ = 'merchant'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(100), nullable=False, unique=True, comment='商家名称')

class Depot(db.Model):
    """车辆段/机务段（机车、车厢、动车组共享）"""
    __tablename__ = 'depot'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, unique=True, comment='车辆段/机务段名称')

# 机车专用表
class LocomotiveSeries(db.Model):
    """机车系列"""
    __tablename__ = 'locomotive_series'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, unique=True, comment='机车系列名称')

class LocomotiveModel(db.Model):
    """机车型号（关联系列和类型）"""
    __tablename__ = 'locomotive_model'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, comment='机车型号名称')
    series_id = db.Column(Integer, ForeignKey('locomotive_series.id'), nullable=False, comment='关联系列ID')
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'), nullable=False, comment='关联动力类型ID')

    series = relationship('LocomotiveSeries', backref='models')
    power_type = relationship('PowerType', backref='locomotive_models')

# 车厢专用表
class CarriageSeries(db.Model):
    """车厢系列"""
    __tablename__ = 'carriage_series'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, unique=True, comment='车厢系列名称')

class CarriageModel(db.Model):
    """车厢型号（关联系列和类型）"""
    __tablename__ = 'carriage_model'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, comment='车厢型号名称')
    series_id = db.Column(Integer, ForeignKey('carriage_series.id'), nullable=False, comment='关联系列ID')
    type = db.Column(String(20), nullable=False, comment='类型：客车/货车/工程车')

    series = relationship('CarriageSeries', backref='models')

# 动车组专用表（与先头车共享）
class TrainsetSeries(db.Model):
    """动车组系列"""
    __tablename__ = 'trainset_series'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, unique=True, comment='动车组系列名称')

class TrainsetModel(db.Model):
    """动车组车型（关联系列和类型）"""
    __tablename__ = 'trainset_model'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(50), nullable=False, comment='动车组车型名称')
    series_id = db.Column(Integer, ForeignKey('trainset_series.id'), nullable=False, comment='关联系列ID')
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'), nullable=False, comment='关联动力类型ID')

    series = relationship('TrainsetSeries', backref='models')
    power_type = relationship('PowerType', backref='trainset_models')
```

**Step 2: Commit**

```bash
git add models.py
git commit -m "feat: add reference data models"
```

---

### Task 3: 创建数据库模型 - 核心数据表（机车）

**Files:**
- Modify: `models.py`

**Step 1: Add locomotive model to models.py**

```python
# 核心数据表
class Locomotive(db.Model):
    """机车模型"""
    __tablename__ = 'locomotive'

    id = db.Column(Integer, primary_key=True, comment='主键')
    series_id = db.Column(Integer, ForeignKey('locomotive_series.id'), comment='关联机车系列ID')
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'), comment='关联动力类型ID')
    model_id = db.Column(Integer, ForeignKey('locomotive_model.id'), comment='关联机车型号ID')
    brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
    depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联机务段ID')
    plaque = db.Column(String(50), comment='挂牌')
    color = db.Column(String(50), comment='颜色')
    scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
    locomotive_number = db.Column(String(12), comment='机车号（4-12位数字，前导0）')
    decoder_number = db.Column(String(4), comment='编号（1-4位数字，无前导0）')
    chip_interface_id = db.Column(Integer, ForeignKey('chip_interface.id'), comment='关联芯片接口ID')
    chip_model_id = db.Column(Integer, ForeignKey('chip_model.id'), comment='关联芯片型号ID')
    price = db.Column(String(50), comment='价格表达式（如288+538）')
    total_price = db.Column(Float, comment='总价（自动计算）')
    item_number = db.Column(String(50), comment='货号')
    purchase_date = db.Column(Date, default=date.today, comment='购买日期')
    merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

    # 关系
    series = relationship('LocomotiveSeries', backref='locomotives')
    power_type = relationship('PowerType', backref='locomotives')
    model = relationship('LocomotiveModel', backref='locomotives')
    brand = relationship('Brand', backref='locomotives')
    depot = relationship('Depot', backref='locomotives')
    chip_interface = relationship('ChipInterface', backref='locomotives')
    chip_model = relationship('ChipModel', backref='locomotives')
    merchant = relationship('Merchant', backref='locomotives')
```

**Step 2: Commit**

```bash
git add models.py
git commit -m "feat: add locomotive model"
```

---

### Task 4: 创建数据库模型 - 核心数据表（车厢套装）

**Files:**
- Modify: `models.py`

**Step 1: Add carriage set and item models to models.py**

```python
class CarriageSet(db.Model):
    """车厢套装主表"""
    __tablename__ = 'carriage_set'

    id = db.Column(Integer, primary_key=True, comment='主键')
    brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
    series_id = db.Column(Integer, ForeignKey('carriage_series.id'), comment='关联车厢系列ID')
    depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联车辆段ID')
    train_number = db.Column(String(20), comment='车次')
    plaque = db.Column(String(50), comment='挂牌')
    item_number = db.Column(String(50), comment='货号')
    scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
    total_price = db.Column(Float, comment='总价')
    purchase_date = db.Column(Date, default=date.today, comment='购买日期')
    merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

    # 关系
    brand = relationship('Brand', backref='carriage_sets')
    series = relationship('CarriageSeries', backref='carriage_sets')
    depot = relationship('Depot', backref='carriage_sets')
    merchant = relationship('Merchant', backref='carriage_sets')
    items = relationship('CarriageItem', backref='set', cascade='all, delete-orphan')

class CarriageItem(db.Model):
    """车厢套装子表（每辆车的详细信息）"""
    __tablename__ = 'carriage_item'

    id = db.Column(Integer, primary_key=True, comment='主键')
    set_id = db.Column(Integer, ForeignKey('carriage_set.id'), nullable=False, comment='关联套装ID')
    model_id = db.Column(Integer, ForeignKey('carriage_model.id'), comment='关联车厢型号ID')
    car_number = db.Column(String(10), comment='车辆号（3-10位数字，无前导0）')
    color = db.Column(String(50), comment='颜色')
    lighting = db.Column(String(50), comment='灯光')

    # 关系
    model = relationship('CarriageModel', backref='items')
```

**Step 2: Commit**

```bash
git add models.py
git commit -m "feat: add carriage set and item models"
```

---

### Task 5: 创建数据库模型 - 核心数据表（动车组和先头车）

**Files:**
- Modify: `models.py`

**Step 1: Add trainset and locomotive head models to models.py**

```python
class Trainset(db.Model):
    """动车组模型"""
    __tablename__ = 'trainset'

    id = db.Column(Integer, primary_key=True, comment='主键')
    series_id = db.Column(Integer, ForeignKey('trainset_series.id'), comment='关联动车组系列ID')
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'), comment='关联动力类型ID')
    model_id = db.Column(Integer, ForeignKey('trainset_model.id'), comment='关联动车组车型ID')
    brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
    depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联动车段ID')
    plaque = db.Column(String(50), comment='挂牌')
    color = db.Column(String(50), comment='颜色')
    scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
    formation = db.Column(Integer, comment='编组数')
    trainset_number = db.Column(String(12), comment='动车号（3-12位数字，前导0）')
    decoder_number = db.Column(String(4), comment='编号（1-4位数字，无前导0）')
    head_light = db.Column(Boolean, comment='头车灯（有/无）')
    interior_light = db.Column(String(50), comment='室内灯')
    chip_interface_id = db.Column(Integer, ForeignKey('chip_interface.id'), comment='关联芯片接口ID')
    chip_model_id = db.Column(Integer, ForeignKey('chip_model.id'), comment='关联芯片型号ID')
    price = db.Column(String(50), comment='价格表达式（如288+538）')
    total_price = db.Column(Float, comment='总价（自动计算）')
    item_number = db.Column(String(50), comment='货号')
    purchase_date = db.Column(Date, default=date.today, comment='购买日期')
    merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

    # 关系
    series = relationship('TrainsetSeries', backref='trainsets')
    power_type = relationship('PowerType', backref='trainsets')
    model = relationship('TrainsetModel', backref='trainsets')
    brand = relationship('Brand', backref='trainsets')
    depot = relationship('Depot', backref='trainsets')
    chip_interface = relationship('ChipInterface', backref='trainsets')
    chip_model = relationship('ChipModel', backref='trainsets')
    merchant = relationship('Merchant', backref='trainsets')

class LocomotiveHead(db.Model):
    """先头车模型"""
    __tablename__ = 'locomotive_head'

    id = db.Column(Integer, primary_key=True, comment='主键')
    model_id = db.Column(Integer, ForeignKey('trainset_model.id'), comment='关联动车组车型ID')
    brand_id = db.Column(Integer, ForeignKey('brand.id'), comment='关联品牌ID')
    depot_id = db.Column(Integer, ForeignKey('depot.id'), comment='关联动车段ID')
    special_color = db.Column(String(32), comment='特涂')
    scale = db.Column(String(2), nullable=False, comment='比例：HO/N')
    head_light = db.Column(Boolean, comment='头车灯（有/无）')
    interior_light = db.Column(String(50), comment='室内灯')
    price = db.Column(String(50), comment='价格表达式（如288+538）')
    total_price = db.Column(Float, comment='总价（自动计算）')
    item_number = db.Column(String(50), comment='货号')
    purchase_date = db.Column(Date, default=date.today, comment='购买日期')
    merchant_id = db.Column(Integer, ForeignKey('merchant.id'), comment='关联商家ID')

    # 关系
    model = relationship('TrainsetModel', backref='locomotive_heads')
    brand = relationship('Brand', backref='locomotive_heads')
    depot = relationship('Depot', backref='locomotive_heads')
    merchant = relationship('Merchant', backref='locomotive_heads')
```

**Step 2: Commit**

```bash
git add models.py
git commit -m "feat: add trainset and locomotive head models"
```

---

### Task 6: 创建数据库初始化脚本

**Files:**
- Create: `init_db.py`

**Step 1: Create init_db.py with initial data**

```python
from app import app
from models import db, PowerType, Brand, ChipInterface, ChipModel, Merchant, Depot
from models import LocomotiveSeries, LocomotiveModel, CarriageSeries, CarriageModel
from models import TrainsetSeries, TrainsetModel

def init_db():
    """初始化数据库并插入预置数据"""
    with app.app_context():
        db.create_all()
        insert_reference_data()
        print("数据库初始化完成！")

def insert_reference_data():
    """插入参考数据"""

    # 1. 动力类型
    power_types = ['蒸汽', '电力', '内燃', '双源']
    for name in power_types:
        if not PowerType.query.filter_by(name=name).first():
            db.session.add(PowerType(name=name))

    # 2. 机车系列
    locomotive_series = ['内电', '内集', '东风', '韶山', '和谐电', '和谐内', '复兴电', '复兴内', 'Vossloh', 'Vectron', 'EMD', 'TRAXX']
    for name in locomotive_series:
        if not LocomotiveSeries.query.filter_by(name=name).first():
            db.session.add(LocomotiveSeries(name=name))

    # 3. 车厢系列
    carriage_series = ['22', '25B', '25G', '25T', '25Z', '19T', '棚车', '敞车', '平车', '罐车']
    for name in carriage_series:
        if not CarriageSeries.query.filter_by(name=name).first():
            db.session.add(CarriageSeries(name=name))

    # 4. 动车组系列
    trainset_series = ['ICE', 'TGV', 'CRH', 'CRH380', 'CR400', 'CR450', 'DESIRO', 'RailJet', '新干线', '特急', '旅游列车']
    for name in trainset_series:
        if not TrainsetSeries.query.filter_by(name=name).first():
            db.session.add(TrainsetSeries(name=name))

    # 5. 芯片接口
    chip_interfaces = ['NEM651(6pin)', 'NEM652(8pin)', 'MTC21', 'MKL21', 'NEXT18', 'PluX16', 'PluX22', 'E24']
    for name in chip_interfaces:
        if not ChipInterface.query.filter_by(name=name).first():
            db.session.add(ChipInterface(name=name))

    # 6. 芯片型号
    chip_models = ['动芯5323', '动芯8004', '动芯8003', 'ESU5.0', 'MS450P22', 'XP5.1', 'Pragon4', 'Tsunami2']
    for name in chip_models:
        if not ChipModel.query.filter_by(name=name).first():
            db.session.add(ChipModel(name=name))

    # 7. 品牌
    brands = ['1435', 'ATHEARN', 'BLI', 'CMR', 'PIKO', 'ROCO', 'TRIX', '百万城', '浩瀚', '深东', '猩猩', '长鸣', '跨越', 'Kunter', '茂杉', 'KATO', 'HCMX', 'HTMX', 'KukePig', 'N27', '毫米制造', '火车花园', '曙光', 'WALTHERS', 'Tomix', '微景', 'ARNOLD', 'Fleischmann', 'MicroAce']
    for name in brands:
        if not Brand.query.filter_by(name=name).first():
            db.session.add(Brand(name=name))

    # 8. 商家
    merchants = ['星期五火车模型', 'SRE铁路模型店', '火车女侠店', '长鸣淘宝', '长鸣京东', '中车文创', 'Kunter飘局的模型店', '南京攀登者模型', '铸造模型', '天易模型', '日本N比例火车模型店', '百万城百克曼', '魔都铁路模型社', '火车模型之家', '百万城旗舰店', '1435火车模型', '浩瀚火车模型', '宁东火车模型', '百酷火车模型', '阿易火车模型', '闲鱼']
    for name in merchants:
        if not Merchant.query.filter_by(name=name).first():
            db.session.add(Merchant(name=name))

    # 9. 车辆段/机务段
    depots = ['京局京段', '京局丰段', '上局沪段', '上局杭段']
    for name in depots:
        if not Depot.query.filter_by(name=name).first():
            db.session.add(Depot(name=name))

    db.session.commit()

if __name__ == '__main__':
    init_db()
```

**Step 2: Commit**

```bash
git add init_db.py
git commit -m "feat: add database initialization script"
```

---

### Task 7: 创建 Flask 主应用框架

**Files:**
- Create: `app.py`

**Step 1: Create app.py with Flask application structure**

```python
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    """汇总统计页面"""
    return render_template('index.html')

@app.route('/options')
def options():
    """选项维护页面"""
    return render_template('options.html')

if __name__ == '__main__':
    app.run(debug=True)
```

**Step 2: Commit**

```bash
git add app.py
git commit -m "feat: add Flask application structure"
```

---

### Task 8: 创建基础模板和样式

**Files:**
- Create: `templates/base.html`
- Create: `static/css/style.css`

**Step 1: Create base.html template**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}火车模型管理系统{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav>
        <ul>
            <li><a href="{{ url_for('index') }}">首页</a></li>
            <li><a href="{{ url_for('locomotive') }}">机车模型</a></li>
            <li><a href="{{ url_for('carriage') }}">车厢模型</a></li>
            <li><a href="{{ url_for('trainset') }}">动车组模型</a></li>
            <li><a href="{{ url_for('locomotive_head') }}">先头车模型</a></li>
            <li><a href="{{ url_for('options') }}">选项维护</a></li>
        </ul>
    </nav>

    <main>
        {% block content %}{% endblock %}
    </main>

    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Step 2: Create style.css**

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    background-color: #f5f5f5;
}

nav {
    background-color: #333;
    padding: 1rem;
}

nav ul {
    list-style: none;
    display: flex;
    gap: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
}

nav a:hover {
    background-color: #555;
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 2rem;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 1rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

input, select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    padding: 0.5rem 1rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #0056b3;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 2rem;
}

th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background-color: #f8f9fa;
}

.error {
    color: red;
}

.btn-danger {
    background-color: #dc3545;
}

.btn-danger:hover {
    background-color: #c82333;
}

.form-row {
    display: flex;
    gap: 1rem;
}

.form-row .form-group {
    flex: 1;
}
```

**Step 3: Commit**

```bash
git add templates/base.html static/css/style.css
git commit -m "feat: add base template and styles"
```

---

### Task 9: 创建首页（汇总统计）

**Files:**
- Create: `templates/index.html`
- Modify: `app.py`

**Step 1: Create index.html template**

```html
{% extends "base.html" %}

{% block title %}汇总统计 - 火车模型管理系统{% endblock %}

{% block content %}
<h1>汇总统计</h1>

<div id="statistics">
    <h2>各类型统计</h2>
    <div class="stats-grid">
        <div class="stat-card">
            <h3>机车模型</h3>
            <p>数量: <span id="locomotive-count">0</span></p>
            <p>总价: ¥<span id="locomotive-total">0</span></p>
        </div>
        <div class="stat-card">
            <h3>车厢模型</h3>
            <p>数量: <span id="carriage-count">0</span></p>
            <p>总价: ¥<span id="carriage-total">0</span></p>
        </div>
        <div class="stat-card">
            <h3>动车组模型</h3>
            <p>数量: <span id="trainset-count">0</span></p>
            <p>总价: ¥<span id="trainset-total">0</span></p>
        </div>
        <div class="stat-card">
            <h3>先头车模型</h3>
            <p>数量: <span id="locomotive-head-count">0</span></p>
            <p>总价: ¥<span id="locomotive-head-total">0</span></p>
        </div>
    </div>
</div>

<script>
// 页面加载时获取统计数据
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            document.getElementById('locomotive-count').textContent = data.locomotive.count;
            document.getElementById('locomotive-total').textContent = data.locomotive.total;
            document.getElementById('carriage-count').textContent = data.carriage.count;
            document.getElementById('carriage-total').textContent = data.carriage.total;
            document.getElementById('trainset-count').textContent = data.trainset.count;
            document.getElementById('trainset-total').textContent = data.trainset.total;
            document.getElementById('locomotive-head-count').textContent = data.locomotive_head.count;
            document.getElementById('locomotive-head-total').textContent = data.locomotive_head.total;
        });
});
</script>

<style>
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.stat-card {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;
}

.stat-card h3 {
    margin-bottom: 0.5rem;
}
</style>
{% endblock %}
```

**Step 2: Add statistics API route to app.py**

```python
from models import Locomotive, CarriageSet, Trainset, LocomotiveHead

@app.route('/api/statistics')
def statistics():
    """获取汇总统计数据"""
    locomotives = Locomotive.query.all()
    carriage_sets = CarriageSet.query.all()
    trainsets = Trainset.query.all()
    locomotive_heads = LocomotiveHead.query.all()

    return jsonify({
        'locomotive': {
            'count': len(locomotives),
            'total': sum(l.total_price or 0 for l in locomotives)
        },
        'carriage': {
            'count': len(carriage_sets),
            'total': sum(c.total_price or 0 for c in carriage_sets)
        },
        'trainset': {
            'count': len(trainsets),
            'total': sum(t.total_price or 0 for t in trainsets)
        },
        'locomotive_head': {
            'count': len(locomotive_heads),
            'total': sum(l.total_price or 0 for l in locomotive_heads)
        }
    })
```

**Step 3: Commit**

```bash
git add templates/index.html app.py
git commit -m "feat: add statistics page and API"
```

---

### Task 10: 创建机车模型页面

**Files:**
- Create: `templates/locomotive.html`
- Modify: `app.py`

**Step 1: Create locomotive.html template**

```html
{% extends "base.html" %}

{% block title %}机车模型 - 火车模型管理系统{% endblock %}

{% block content %}
<h1>机车模型</h1>

<form id="locomotive-form" method="POST">
    <div class="form-row">
        <div class="form-group">
            <label for="model_id">车型 *</label>
            <select id="model_id" name="model_id" required onchange="autoFillLocomotive()">
                <option value="">请选择</option>
                {% for model in locomotive_models %}
                <option value="{{ model.id }}">{{ model.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="series_id">系列</label>
            <select id="series_id" name="series_id">
                <option value="">请选择</option>
                {% for series in locomotive_series %}
                <option value="{{ series.id }}">{{ series.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="power_type_id">动力类型</label>
            <select id="power_type_id" name="power_type_id">
                <option value="">请选择</option>
                {% for type in power_types %}
                <option value="{{ type.id }}">{{ type.name }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <div class="form-row">
        <div class="form-group">
            <label for="brand_id">品牌 *</label>
            <select id="brand_id" name="brand_id" required>
                <option value="">请选择</option>
                {% for brand in brands %}
                <option value="{{ brand.id }}">{{ brand.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="depot_id">机务段</label>
            <select id="depot_id" name="depot_id">
                <option value="">请选择</option>
                {% for depot in depots %}
                <option value="{{ depot.id }}">{{ depot.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="scale">比例 *</label>
            <select id="scale" name="scale" required>
                <option value="HO">HO</option>
                <option value="N">N</option>
            </select>
        </div>
    </div>

    <div class="form-row">
        <div class="form-group">
            <label for="locomotive_number">机车号 *</label>
            <input type="text" id="locomotive_number" name="locomotive_number" required>
        </div>
        <div class="form-group">
            <label for="decoder_number">编号</label>
            <input type="text" id="decoder_number" name="decoder_number">
        </div>
    </div>

    <div class="form-row">
        <div class="form-group">
            <label for="plaque">挂牌</label>
            <input type="text" id="plaque" name="plaque">
        </div>
        <div class="form-group">
            <label for="color">颜色</label>
            <input type="text" id="color" name="color">
        </div>
    </div>

    <div class="form-row">
        <div class="form-group">
            <label for="chip_interface_id">芯片接口</label>
            <select id="chip_interface_id" name="chip_interface_id">
                <option value="">请选择</option>
                {% for interface in chip_interfaces %}
                <option value="{{ interface.id }}">{{ interface.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="chip_model_id">芯片型号</label>
            <select id="chip_model_id" name="chip_model_id">
                <option value="">请选择</option>
                {% for model in chip_models %}
                <option value="{{ model.id }}">{{ model.name }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <div class="form-row">
        <div class="form-group">
            <label for="price">价格（表达式，如288+538）</label>
            <input type="text" id="price" name="price">
        </div>
        <div class="form-group">
            <label for="item_number">货号</label>
            <input type="text" id="item_number" name="item_number">
        </div>
    </div>

    <div class="form-group">
        <label for="purchase_date">购买日期</label>
        <input type="date" id="purchase_date" name="purchase_date">
    </div>

    <div class="form-group">
        <label for="merchant_id">购买商家</label>
        <select id="merchant_id" name="merchant_id">
            <option value="">请选择</option>
            {% for merchant in merchants %}
            <option value="{{ merchant.id }}">{{ merchant.name }}</option>
            {% endfor %}
        </select>
    </div>

    <button type="submit">添加</button>
</form>

{% if errors %}
<div class="error">
    {% for error in errors %}
    <p>{{ error }}</p>
    {% endfor %}
</div>
{% endif %}

<table>
    <thead>
        <tr>
            <th>车型</th>
            <th>系列</th>
            <th>品牌</th>
            <th>比例</th>
            <th>机车号</th>
            <th>编号</th>
            <th>总价</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        {% for locomotive in locomotives %}
        <tr>
            <td>{{ locomotive.model.name }}</td>
            <td>{{ locomotive.series.name if locomotive.series else '-' }}</td>
            <td>{{ locomotive.brand.name }}</td>
            <td>{{ locomotive.scale }}</td>
            <td>{{ locomotive.locomotive_number }}</td>
            <td>{{ locomotive.decoder_number }}</td>
            <td>{{ locomotive.total_price }}</td>
            <td>
                <form method="POST" action="{{ url_for('delete_locomotive', id=locomotive.id) }}" onsubmit="return confirm('确定删除？')">
                    <button type="submit" class="btn-danger">删除</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<script>
function autoFillLocomotive() {
    const modelId = document.getElementById('model_id').value;
    if (!modelId) return;

    fetch(`/api/auto-fill/locomotive/${modelId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('series_id').value = data.series_id;
            document.getElementById('power_type_id').value = data.power_type_id;
        });
}
</script>
{% endblock %}
```

**Step 2: Add locomotive routes to app.py**

```python
import re
from models import Locomotive, LocomotiveModel, LocomotiveSeries, PowerType, Brand, Depot, ChipInterface, ChipModel, Merchant
from datetime import date

def calculate_price(price_expr):
    """安全计算价格表达式"""
    if not price_expr:
        return 0
    # 只允许数字、+、-、*、/、()
    if not re.match(r'^[\d+\-*/().\s]+$', price_expr):
        return 0
    try:
        return eval(price_expr)
    except:
        return 0

def check_duplicate(table, field, value, scale=None):
    """检查同一比例内的唯一性"""
    if table == 'locomotive':
        if field == 'locomotive_number':
            return Locomotive.query.filter_by(locomotive_number=value, scale=scale).first()
        elif field == 'decoder_number':
            return Locomotive.query.filter_by(decoder_number=value, scale=scale).first()
    return None

@app.route('/locomotive', methods=['GET', 'POST'])
def locomotive():
    """机车模型列表和添加"""
    locomotives = Locomotive.query.all()
    locomotive_models = LocomotiveModel.query.all()
    locomotive_series = LocomotiveSeries.query.all()
    power_types = PowerType.query.all()
    brands = Brand.query.all()
    depots = Depot.query.all()
    chip_interfaces = ChipInterface.query.all()
    chip_models = ChipModel.query.all()
    merchants = Merchant.query.all()

    errors = []

    if request.method == 'POST':
        scale = request.form.get('scale')
        locomotive_number = request.form.get('locomotive_number')
        decoder_number = request.form.get('decoder_number')

        # 唯一性验证
        if locomotive_number and check_duplicate('locomotive', 'locomotive_number', locomotive_number, scale):
            errors.append(f"机车号 {locomotive_number} 在 {scale} 比例下已存在")
        if decoder_number and check_duplicate('locomotive', 'decoder_number', decoder_number, scale):
            errors.append(f"编号 {decoder_number} 在 {scale} 比例下已存在")

        if not errors:
            locomotive = Locomotive(
                model_id=int(request.form.get('model_id')),
                series_id=request.form.get('series_id'),
                power_type_id=request.form.get('power_type_id'),
                brand_id=int(request.form.get('brand_id')),
                depot_id=request.form.get('depot_id'),
                plaque=request.form.get('plaque'),
                color=request.form.get('color'),
                scale=scale,
                locomotive_number=locomotive_number,
                decoder_number=decoder_number,
                chip_interface_id=request.form.get('chip_interface_id'),
                chip_model_id=request.form.get('chip_model_id'),
                price=request.form.get('price'),
                total_price=calculate_price(request.form.get('price')),
                item_number=request.form.get('item_number'),
                purchase_date=request.form.get('purchase_date') or date.today(),
                merchant_id=request.form.get('merchant_id')
            )
            db.session.add(locomotive)
            db.session.commit()
            return redirect(url_for('locomotive'))

    return render_template('locomotive.html',
        locomotives=locomotives,
        locomotive_models=locomotive_models,
        locomotive_series=locomotive_series,
        power_types=power_types,
        brands=brands,
        depots=depots,
        chip_interfaces=chip_interfaces,
        chip_models=chip_models,
        merchants=merchants,
        errors=errors
    )

@app.route('/locomotive/delete/<int:id>', methods=['POST'])
def delete_locomotive(id):
    """删除机车模型"""
    locomotive = Locomotive.query.get_or_404(id)
    db.session.delete(locomotive)
    db.session.commit()
    return redirect(url_for('locomotive'))
```

**Step 3: Commit**

```bash
git add templates/locomotive.html app.py
git commit -m "feat: add locomotive model CRUD"
```

---

### Task 11: 创建自动填充 API

**Files:**
- Modify: `app.py`

**Step 1: Add auto-fill API to app.py**

```python
@app.route('/api/auto-fill/locomotive/<int:model_id>')
def auto_fill_locomotive(model_id):
    """机车车型自动填充"""
    model = LocomotiveModel.query.get_or_404(model_id)
    return jsonify({
        'series_id': model.series_id,
        'power_type_id': model.power_type_id
    })

@app.route('/api/auto-fill/carriage/<int:model_id>')
def auto_fill_carriage(model_id):
    """车厢车型自动填充"""
    model = CarriageModel.query.get_or_404(model_id)
    return jsonify({
        'series_id': model.series_id,
        'type': model.type
    })

@app.route('/api/auto-fill/trainset/<int:model_id>')
def auto_fill_trainset(model_id):
    """动车组车型自动填充"""
    model = TrainsetModel.query.get_or_404(model_id)
    return jsonify({
        'series_id': model.series_id,
        'power_type_id': model.power_type_id
    })
```

**Step 2: Commit**

```bash
git add app.py
git commit -m "feat: add auto-fill API endpoints"
```

---

### Task 12-15: 创建车厢、动车组、先头车和选项维护页面

（由于篇幅原因，这些任务的详细步骤与机车模型页面类似，遵循相同的模式）

---

### Task 16: 创建 README 文档

**Files:**
- Create: `README.md`

**Step 1: Create README.md**

```markdown
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
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## 执行说明

计划完成并保存至 `docs/plans/2025-02-14-train-model-manager-implementation.md`。

两种执行选项：

**1. 子代理驱动（当前会话）** - 我为每个任务分派新的子代理，任务间审查，快速迭代

**2. 并行会话（独立）** - 在新会话中使用 executing-plans 批量执行并设置检查点

您选择哪种方式？
