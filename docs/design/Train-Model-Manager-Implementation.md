# 火车模型管理系统 - 详细实现文档

**版本**: v0.8.0
**最后更新**: 2026-02-23

---

## 一、项目概述

### 1.1 系统简介

火车模型管理系统是一个用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型的完整生命周期管理，包括数据录入、文件管理、统计分析和数据导入导出。

### 1.2 功能特性

| 功能模块 | 描述 |
|---------|------|
| 模型管理 | 四种模型类型（机车、车厢、动车组、先头车）的 CRUD 操作 |
| 文件管理 | 模型图片、说明书、数码功能表的上传、下载、预览、删除 |
| 数据统计 | 多维度统计（类型/比例/品牌/商家），支持表格和饼图展示 |
| 数据导入导出 | Excel 导入导出，支持多种模式和冲突检测 |
| 自定义导入 | 5 步向导式导入，支持模板管理和灵活列映射 |
| 信息维护 | 集中管理所有参考数据（品牌、商家、芯片等） |

### 1.3 技术栈

| 技术 | 版本/说明 |
|-----|----------|
| Python | 3.10+ |
| Flask | 3.0.0（Blueprint 模块化架构）|
| SQLAlchemy | 3.1.1（ORM）|
| 数据库 | SQLite（开发）/ MySQL（生产）|
| 前端 | HTML5 + JavaScript（无构建工具）|
| 图表 | Chart.js 4.x（CDN 引入）|
| Excel | openpyxl |
| 测试 | pytest |

---

## 二、架构设计

### 2.1 目录结构

```
TrainModelManager/
├── app.py                    # Flask 应用工厂
├── models.py                 # SQLAlchemy 数据模型
├── config.py                 # 配置类（含 TestConfig）
├── init_db.py               # 数据库初始化脚本
├── requirements.txt         # Python 依赖
│
├── routes/                  # Blueprint 路由模块
│   ├── __init__.py
│   ├── main.py              # 首页和统计
│   ├── locomotive.py        # 机车模型路由
│   ├── carriage.py          # 车厢模型路由
│   ├── trainset.py          # 动车组模型路由
│   ├── locomotive_head.py   # 先头车模型路由
│   ├── options.py           # 信息维护（工厂函数）
│   ├── api.py               # API 端点（自动填充、导入导出）
│   └── files.py             # 文件管理 API
│
├── utils/                   # 公共辅助函数
│   ├── __init__.py
│   ├── helpers.py           # 通用辅助函数
│   ├── validators.py        # 验证函数
│   ├── price_calculator.py  # 价格计算（AST 安全解析）
│   ├── system_tables.py     # 系统表配置（自定义导入）
│   └── file_sync.py         # 文件同步工具
│
├── static/
│   ├── css/style.css        # 主样式文件（CSS 变量）
│   └── js/
│       ├── utils.js         # 核心工具模块
│       ├── app.js           # 页面初始化
│       ├── options.js       # 信息维护专用
│       ├── system.js        # 系统维护专用
│       └── custom-import.js # 自定义导入向导
│
├── templates/               # Jinja2 模板
│   ├── base.html            # 基础布局模板
│   ├── index.html           # 首页统计
│   ├── locomotive.html      # 机车列表（含模态框）
│   ├── carriage.html        # 车厢列表（含模态框）
│   ├── trainset.html        # 动车组列表（含模态框）
│   ├── locomotive_head.html # 先头车列表（含模态框）
│   ├── options.html         # 信息维护
│   ├── system.html          # 系统维护
│   ├── macros/              # Jinja2 宏
│   │   ├── form.html        # 表单字段宏
│   │   └── table.html       # 表格相关宏
│   ├── 404.html
│   └── 500.html
│
├── tests/                   # 测试文件
│   ├── conftest.py          # 测试配置
│   ├── test_api.py          # API 测试
│   ├── test_crud.py         # CRUD 测试
│   ├── test_files.py        # 文件功能测试
│   └── ...
│
├── data/                    # 文件存储目录（默认）
│   ├── locomotive/
│   ├── carriage/
│   ├── trainset/
│   └── locomotive_head/
│
└── docs/                    # 文档
    ├── design/              # 设计文档
    └── plans/               # 需求文档
```

### 2.2 后端架构

采用 Flask Blueprint 模块化架构：

```python
# app.py - 应用工厂模式
from flask import Flask
from config import Config
from models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    # 注册蓝图
    from routes.main import main_bp
    from routes.locomotive import locomotive_bp
    from routes.carriage import carriage_bp
    from routes.trainset import trainset_bp
    from routes.locomotive_head import locomotive_head_bp
    from routes.options import options_bp
    from routes.api import api_bp
    from routes.files import files_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(locomotive_bp)
    app.register_blueprint(carriage_bp)
    app.register_blueprint(trainset_bp)
    app.register_blueprint(locomotive_head_bp)
    app.register_blueprint(options_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(files_bp)

    return app
```

### 2.3 前端架构

#### JavaScript 模块结构

```javascript
// static/js/utils.js - 核心工具模块

// 通用工具
const Utils = {
  filterModelsBySeries(seriesId, modelSelectId, models),
  autoFill(modelId, apiUrl, fieldMappings),
  showTab(tabId, tabGroup),
  // ...
};

// API 封装
const Api = {
  post(url, data),
  postForm(url, formData),
  // ...
};

// 表单处理
const FormHelper = {
  clearErrors(form),
  showErrors(form, errors),
  showSuccess(form, message),
  // ...
};

// 表格管理
const TableManager = {
  init(tableId),
  handleSort(table, th),
  handleFilter(table, select, column),
  // ...
};

// 文件管理
const FileManager = {
  showModelDetail(modelType, modelId),
  triggerUpload(fileType),
  downloadFile(fileId),
  viewFile(fileId),
  deleteFile(fileId),
  // ...
};

// 表单填充（复制按钮）
const FormFiller = {
  copyFromRow(button, fieldMappings),
  fillField(fieldId, value),
  // ...
};
```

#### CSS 变量系统

```css
/* static/css/style.css */
:root {
  --color-primary: #007bff;
  --color-success: #28a745;
  --color-danger: #dc3545;
  --color-info: #17a2b8;
  --color-secondary: #6c757d;
  --border-radius: 4px;
  --spacing-md: 1rem;
  --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
}
```

---

## 三、数据模型

### 3.1 参考数据表（共享）

```python
# models.py

class PowerType(db.Model):
    """动力类型（机车和动车组共享）"""
    __tablename__ = 'power_type'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False, unique=True)

class Brand(db.Model):
    """品牌（所有模型共享）"""
    __tablename__ = 'brand'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, unique=True)
    abbreviation = db.Column(String(10), nullable=False, unique=True)  # 品牌缩写，用于文件命名
    website = db.Column(String(255))  # 官方网站
    search_url = db.Column(String(255))  # 搜索URL模板，{query}为搜索词占位符

class ChipInterface(db.Model):
    """芯片接口（机车和动车组共享）"""
    __tablename__ = 'chip_interface'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False, unique=True)

class ChipModel(db.Model):
    """芯片型号（机车和动车组共享）"""
    __tablename__ = 'chip_model'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, unique=True)

class Merchant(db.Model):
    """购买商家（所有模型共享）"""
    __tablename__ = 'merchant'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, unique=True)

class Depot(db.Model):
    """车辆段/机务段（机车、车厢、动车组共享）"""
    __tablename__ = 'depot'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False, unique=True)
```

### 3.2 系列和型号表

```python
# 机车系列和型号
class LocomotiveSeries(db.Model):
    __tablename__ = 'locomotive_series'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False, unique=True)

class LocomotiveModel(db.Model):
    __tablename__ = 'locomotive_model'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False)
    series_id = db.Column(Integer, ForeignKey('locomotive_series.id'))
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'))
    series = relationship('LocomotiveSeries', backref='models')
    power_type = relationship('PowerType', backref='locomotive_models')

# 车厢系列和型号
class CarriageSeries(db.Model):
    __tablename__ = 'carriage_series'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False, unique=True)

class CarriageModel(db.Model):
    __tablename__ = 'carriage_model'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False)
    series_id = db.Column(Integer, ForeignKey('carriage_series.id'))
    type = db.Column(String(20))  # 客车/货车/工程车
    series = relationship('CarriageSeries', backref='models')

# 动车组系列和型号
class TrainsetSeries(db.Model):
    __tablename__ = 'trainset_series'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False, unique=True)

class TrainsetModel(db.Model):
    __tablename__ = 'trainset_model'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(50), nullable=False)
    series_id = db.Column(Integer, ForeignKey('trainset_series.id'))
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'))
    series = relationship('TrainsetSeries', backref='models')
    power_type = relationship('PowerType', backref='trainset_models')
```

### 3.3 核心数据表（四种模型类型）

```python
# 机车模型
class Locomotive(db.Model):
    __tablename__ = 'locomotive'
    id = db.Column(Integer, primary_key=True)
    series_id = db.Column(Integer, ForeignKey('locomotive_series.id'))
    power_type_id = db.Column(Integer, ForeignKey('power_type.id'))
    model_id = db.Column(Integer, ForeignKey('locomotive_model.id'))
    brand_id = db.Column(Integer, ForeignKey('brand.id'))
    depot_id = db.Column(Integer, ForeignKey('depot.id'))
    plaque = db.Column(String(50))
    color = db.Column(String(50))
    scale = db.Column(String(2), nullable=False)
    locomotive_number = db.Column(String(12))
    decoder_number = db.Column(String(4))
    chip_interface_id = db.Column(Integer, ForeignKey('chip_interface.id'))
    chip_model_id = db.Column(Integer, ForeignKey('chip_model.id'))
    price = db.Column(String(50))
    total_price = db.Column(Float)
    item_number = db.Column(String(50))
    product_url = db.Column(String(255))
    purchase_date = db.Column(Date)
    merchant_id = db.Column(Integer, ForeignKey('merchant.id'))
    # 关系...
    files = relationship('ModelFile', backref='locomotive',
                         foreign_keys='ModelFile.model_id',
                         primaryjoin="and_(Locomotive.id==ModelFile.model_id, "
                                     "ModelFile.model_type=='locomotive')")

# 车厢套装（主表）
class CarriageSet(db.Model):
    __tablename__ = 'carriage_set'
    id = db.Column(Integer, primary_key=True)
    brand_id = db.Column(Integer, ForeignKey('brand.id'))
    series_id = db.Column(Integer, ForeignKey('carriage_series.id'))
    depot_id = db.Column(Integer, ForeignKey('depot.id'))
    train_number = db.Column(String(20))
    plaque = db.Column(String(50))
    item_number = db.Column(String(50))
    scale = db.Column(String(2), nullable=False)
    total_price = db.Column(Float)
    product_url = db.Column(String(255))
    purchase_date = db.Column(Date)
    merchant_id = db.Column(Integer, ForeignKey('merchant.id'))
    items = relationship('CarriageItem', backref='set', cascade='all, delete-orphan')

# 车厢项（子表）
class CarriageItem(db.Model):
    __tablename__ = 'carriage_item'
    id = db.Column(Integer, primary_key=True)
    set_id = db.Column(Integer, ForeignKey('carriage_set.id'), nullable=False)
    model_id = db.Column(Integer, ForeignKey('carriage_model.id'))
    car_number = db.Column(String(10))
    color = db.Column(String(50))
    lighting = db.Column(String(50))

# 动车组模型
class Trainset(db.Model):
    __tablename__ = 'trainset'
    # 类似 Locomotive，额外字段：
    formation = db.Column(Integer)      # 编组数
    trainset_number = db.Column(String(12))
    head_light = db.Column(Boolean)
    interior_light = db.Column(String(50))

# 先头车模型（无动车段、无芯片）
class LocomotiveHead(db.Model):
    __tablename__ = 'locomotive_head'
    # 简化字段：无 chip_interface, chip_model, depot
    model_id = db.Column(Integer, ForeignKey('trainset_model.id'))
    special_color = db.Column(String(32))
    head_light = db.Column(Boolean)
    interior_light = db.Column(String(50))
```

### 3.4 文件跟踪表

```python
class ModelFile(db.Model):
    """模型文件跟踪表"""
    __tablename__ = 'model_file'
    id = db.Column(Integer, primary_key=True)
    model_type = db.Column(String(20), nullable=False)  # locomotive/carriage/trainset/locomotive_head
    model_id = db.Column(Integer, nullable=False)
    file_type = db.Column(String(20), nullable=False)   # image/manual/function_table
    file_path = db.Column(String(255), nullable=False)  # 相对路径
    stored_filename = db.Column(String(255), nullable=False)  # 存储文件名
    original_filename = db.Column(String(255), nullable=False)  # 原始文件名
    file_size = db.Column(Integer)
    mime_type = db.Column(String(100))
    uploaded_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'model_type': self.model_type,
            'model_id': self.model_id,
            'file_type': self.file_type,
            'file_path': self.file_path,
            'stored_filename': self.stored_filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
```

### 3.5 导入模板表

```python
class ImportTemplate(db.Model):
    """自定义导入模板"""
    __tablename__ = 'import_template'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    target_table = db.Column(String(50), nullable=False)
    column_mapping = db.Column(JSON, nullable=False)  # {"Excel列名": "系统字段名"}
    created_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
```

---

## 四、API 路由

### 4.1 统计 API

| 路由 | 方法 | 描述 |
|------|------|------|
| `GET /api/statistics` | GET | 返回多维度统计数据 |

**响应示例：**
```json
{
  "type_stats": [...],
  "scale_stats": [...],
  "brand_stats": [...],
  "merchant_stats": [...]
}
```

### 4.2 模型操作 API

| 路由 | 方法 | 描述 |
|------|------|------|
| `POST /api/locomotive/add` | POST | 添加机车模型 |
| `POST /api/locomotive/edit/<id>` | POST | 编辑机车模型 |
| `POST /api/carriage/add` | POST | 添加车厢套装 |
| `POST /api/carriage/edit/<id>` | POST | 编辑车厢套装 |
| `POST /api/trainset/add` | POST | 添加动车组模型 |
| `POST /api/trainset/edit/<id>` | POST | 编辑动车组模型 |
| `POST /api/locomotive-head/add` | POST | 添加先头车模型 |
| `POST /api/locomotive-head/edit/<id>` | POST | 编辑先头车模型 |

### 4.3 自动填充 API

| 路由 | 方法 | 描述 |
|------|------|------|
| `GET /api/auto-fill/locomotive/<model_id>` | GET | 机车型号自动填充 |
| `GET /api/auto-fill/trainset/<model_id>` | GET | 动车组车型自动填充 |

### 4.4 Excel 导入导出 API

| 路由 | 方法 | 描述 |
|------|------|------|
| `GET /api/export/excel?mode=<models\|system\|all>` | GET | 导出 Excel |
| `POST /api/import/excel` | POST | 导入 Excel（智能识别） |

### 4.5 自定义导入 API

| 路由 | 方法 | 描述 |
|------|------|------|
| `GET /api/import-templates` | GET | 获取导入模板列表 |
| `POST /api/import-templates` | POST | 创建导入模板 |
| `GET /api/import-templates/<id>` | GET | 获取指定模板 |
| `PUT /api/import-templates/<id>` | PUT | 更新模板 |
| `DELETE /api/import-templates/<id>` | DELETE | 删除模板 |
| `GET /api/custom-import/tables` | GET | 获取系统表配置 |
| `POST /api/custom-import/parse` | POST | 解析 Excel 文件 |
| `POST /api/custom-import/preview` | POST | 预览导入数据（含冲突检测）|
| `POST /api/custom-import/execute` | POST | 执行导入 |

### 4.6 文件管理 API

| 路由 | 方法 | 描述 |
|------|------|------|
| `POST /api/files/upload` | POST | 上传文件 |
| `GET /api/files/download/<id>` | GET | 下载文件 |
| `GET /api/files/view/<id>` | GET | 在浏览器中预览文件 |
| `DELETE /api/files/delete/<id>` | DELETE | 删除文件 |
| `GET /api/files/list/<type>/<id>` | GET | 获取模型文件列表 |
| `GET /api/files/export-all` | GET | 导出所有模型文件为 ZIP |
| `GET /api/files/model/<type>/<id>` | GET | 获取模型详情（含文件）|

---

## 五、文件存储

### 5.1 目录结构

```
data/
├── locomotive/
│   └── {品牌缩写}_{货号}/
│       ├── {品牌缩写}_{货号}.{ext}                    # 模型图片
│       ├── {品牌缩写}_{货号}_FunctionKey.{ext}        # 数码功能表
│       └── {品牌缩写}_{货号}_Manual_{原始文件名}.{ext} # 说明书（可多个）
├── carriage/
│   └── {品牌缩写}_{货号}/
├── trainset/
│   └── {品牌缩写}_{货号}/
└── locomotive_head/
    └── {品牌缩写}_{货号}/
        ├── {品牌缩写}_{货号}.{ext}                    # 模型图片
        └── {品牌缩写}_{货号}_Manual_{原始文件名}.{ext} # 说明书（无数码功能表）
```

**注意**：目录名和文件名使用品牌缩写而非品牌全名，以保持文件路径简洁。

### 5.2 文件命名规则

| 文件类型 | 文件名格式 | 唯一性 |
|----------|-----------|--------|
| 模型图片 | `{品牌缩写}_{货号}.{ext}` | 每个模型唯一 |
| 数码功能表 | `{品牌缩写}_{货号}_FunctionKey.{ext}` | 每个模型唯一 |
| 说明书 | `{品牌缩写}_{货号}_Manual_{原始文件名}.{ext}` | 可多个 |

### 5.3 文件上传逻辑

```python
# routes/files.py

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    model_type = request.form.get('model_type')
    model_id = request.form.get('model_id')
    file_type = request.form.get('file_type')
    file = request.files.get('file')

    # 获取模型信息构建目录名（使用品牌缩写）
    model = get_model_by_type(model_type, model_id)
    brand_abbreviation = model.brand.abbreviation or ''
    item_number = model.item_number or ''
    dir_name = f"{brand_abbreviation}_{item_number}"

    # 构建存储路径
    storage_dir = os.path.join(DATA_DIR, model_type, dir_name)

    # 生成文件名
    if file_type == 'image':
        filename = f"{dir_name}.{extension}"
    elif file_type == 'function_table':
        filename = f"{dir_name}_FunctionKey.{extension}"
    elif file_type == 'manual':
        safe_name = secure_filename(original_name)
        filename = f"{dir_name}_Manual_{safe_name}"

    # 保存文件
    file_path = os.path.join(storage_dir, filename)

    # 更新数据库
    model_file = ModelFile(
        model_type=model_type,
        model_id=model_id,
        file_type=file_type,
        file_path=file_path,
        stored_filename=filename,
        original_filename=file.filename,
        file_size=file_size,
        mime_type=file.mimetype
    )
    db.session.add(model_file)
    db.session.commit()
```

---

## 六、核心业务逻辑

### 6.1 价格计算

使用 AST 安全解析表达式，防止代码注入：

```python
# utils/price_calculator.py

import ast
import operator

class SafeEval(ast.NodeVisitor):
    """
    安全的表达式计算器
    通过 AST 验证限制只允许数学运算，防止代码注入
    """
    ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp,
        ast.Num, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub
    )

    def visit(self, node):
        if not isinstance(node, self.ALLOWED_NODES):
            raise ValueError(f"不允许的操作: {type(node).__name__}")
        return super().visit(node)

def calculate_price(expression):
    """
    安全计算价格表达式
    支持基本四则运算，如 "288+538"、"100*2+50"
    """
    if not expression:
        return 0.0
    try:
        tree = ast.parse(expression, mode='eval')
        SafeEval().visit(tree)  # 验证 AST 节点
        # 使用 operator 模块安全计算
        return _eval_node(tree.body)
    except:
        return 0.0

def _eval_node(node):
    """递归计算 AST 节点"""
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }
        return ops[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand)
    raise ValueError("不支持的操作")
```

### 6.2 唯一性验证

```python
# utils/validators.py

def validate_locomotive_number(number, scale, exclude_id=None):
    """验证机车号在同一比例内的唯一性"""
    query = Locomotive.query.filter_by(
        locomotive_number=number,
        scale=scale
    )
    if exclude_id:
        query = query.filter(Locomotive.id != exclude_id)
    return query.first() is None

def validate_decoder_number(number, scale, exclude_id=None):
    """验证编号在同一比例内的唯一性"""
    query = Locomotive.query.filter_by(
        decoder_number=number,
        scale=scale
    )
    if exclude_id:
        query = query.filter(Locomotive.id != exclude_id)
    return query.first() is None
```

### 6.3 文件同步

```python
# utils/file_sync.py

def sync_files_on_startup():
    """启动时同步 data 目录到数据库"""
    for model_type in ['locomotive', 'carriage', 'trainset', 'locomotive_head']:
        type_dir = os.path.join(DATA_DIR, model_type)
        if not os.path.exists(type_dir):
            continue

        for dir_name in os.listdir(type_dir):
            # 解析目录名获取品牌和货号
            # 匹配模型记录
            # 同步文件记录
```

---

## 七、前端实现

### 7.1 模态框表单

所有模型类型使用模态框进行添加和编辑，无需跳转页面：

```html
<!-- 添加/编辑模态框 -->
<div id="locomotive-modal" class="modal-overlay" style="display: none;">
  <div class="modal-dialog modal-form">
    <div class="modal-header">
      <h3 id="modal-title">添加机车模型</h3>
      <button type="button" class="modal-close">&times;</button>
    </div>
    <div class="modal-body">
      <form id="locomotive-form">
        <!-- 表单字段 -->
      </form>
    </div>
    <div class="modal-form-actions">
      <button type="button" class="btn btn-secondary" onclick="ModalManager.close()">取消</button>
      <button type="button" class="btn btn-primary" onclick="submitForm()">保存</button>
    </div>
  </div>
</div>
```

### 7.2 模型详情模态框

50/50 布局显示图片和基本信息：

```html
<!-- 模型详情模态框 -->
<div id="model-detail-modal" class="modal-overlay" style="display: none;">
  <div class="modal-dialog modal-large">
    <div class="modal-body">
      <div class="model-detail-content">
        <!-- 左侧：图片和文件 -->
        <div class="model-left-section">
          <div class="model-image-section">...</div>
          <div class="model-file-section">...</div>
        </div>
        <!-- 右侧：属性 -->
        <div class="model-attributes-section">
          <table class="model-attributes-table">...</table>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 7.3 表格排序筛选

```javascript
// TableManager 实现
const TableManager = {
  init(tableId) {
    const table = document.getElementById(tableId);
    // 绑定排序事件
    table.querySelectorAll('th[data-sort]').forEach(th => {
      th.addEventListener('click', () => this.handleSort(table, th));
    });
    // 创建筛选下拉框
    table.querySelectorAll('th[data-filter]').forEach(th => {
      this.createFilter(table, th);
    });
  },

  handleSort(table, th) {
    const column = th.dataset.sort;
    const order = th.classList.contains('sort-asc') ? 'desc' : 'asc';
    // 排序逻辑...
  },

  handleFilter(table, select, column) {
    const value = select.value;
    // 筛选逻辑...
  }
};
```

### 7.4 文件管理模块

```javascript
// FileManager 实现
const FileManager = {
  currentModel: null,

  showModelDetail(modelType, modelId) {
    Api.get(`/api/files/model/${modelType}/${modelId}`).then(data => {
      this.currentModel = { type: modelType, id: modelId };
      this.renderDetail(data);
      ModalManager.open('model-detail-modal');
    });
  },

  triggerUpload(fileType) {
    const input = document.getElementById(`${fileType}-upload-input`);
    input.click();
  },

  downloadFile(fileId) {
    window.location.href = `/api/files/download/${fileId}`;
  },

  viewFile(fileId) {
    window.open(`/api/files/view/${fileId}`, '_blank');
  },

  deleteFile(fileId) {
    if (confirm('确定删除此文件？')) {
      Api.delete(`/api/files/delete/${fileId}`).then(() => {
        this.refreshFileList();
      });
    }
  }
};
```

---

## 八、测试

### 8.1 测试配置

```python
# tests/conftest.py

import pytest
from app import create_app
from models import db

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()
```

### 8.2 测试分类

| 测试文件 | 覆盖范围 |
|---------|---------|
| `test_models.py` | 数据模型测试 |
| `test_routes.py` | 路由测试 |
| `test_api.py` | API 测试 |
| `test_crud.py` | CRUD 操作测试 |
| `test_validation.py` | 验证逻辑测试 |
| `test_files.py` | 文件功能测试 |
| `test_integration.py` | 集成测试 |

### 8.3 运行测试

```bash
pytest                    # 运行所有测试
pytest -v                 # 详细输出
pytest tests/test_api.py  # 运行特定文件
pytest -k "locomotive"    # 运行名称匹配的测试
```

---

## 九、部署

### 9.1 环境变量

```bash
# 数据库配置
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=train_model_manager

# 文件存储
export DATA_DIR=/path/to/data

# 安全配置
export SECRET_KEY=your-secret-key
export FLASK_ENV=production
```

### 9.2 启动命令

```bash
# 开发环境
python app.py

# 生产环境（使用 gunicorn）
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## 十、版本历史

### v0.9.0
- 品牌缩写功能
  - Brand 表新增 abbreviation 字段（必填，唯一，最长 10 字符）
  - 文件命名改用品牌缩写替代品牌全名，保持路径简洁
  - 信息维护页面支持品牌缩写的增删改查
  - 新增品牌时自动生成拼音首字母缩写
  - 使用 pypinyin 库处理中文品牌名

### v0.8.0
- 模型文件管理功能（图片、说明书、数码功能表）
- 模态框表单（合并添加/编辑页面）
- 代码现代化（修复 deprecation warnings）

### v0.7.0
- 自定义 Excel 导入向导
- 导入模板管理

### v0.6.0
- JavaScript 函数提取
- CSS 变量统一

### v0.5.0
- 复制按钮功能
- Excel 导入导出增强

### v0.4.0
- 首页多维度统计
- 表格排序筛选

### v0.3.0
- Blueprint 模块化重构
- 公共辅助函数提取

### v0.2.0
- 基础 CRUD 功能
- 四种模型类型支持

### v0.1.0
- 项目初始化
- 基础架构搭建
