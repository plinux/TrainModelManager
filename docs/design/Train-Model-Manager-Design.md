# 火车模型管理系统设计文档

**日期**: 2026-02-18
**状态**: 已批准
**版本**: v0.5.0

## 概述

火车模型管理系统是一个用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型。

## 架构决策

### 技术栈

#### 后端
- **Python 3.10+** - 主要编程语言
- **Flask 3.0+** - Web 框架（Blueprint 模块化架构）
- **SQLAlchemy 3.1+** - ORM 框架
- **SQLite** - 开发环境数据库
- **MySQL** - 生产环境数据库（可选）
- **Jinja2** - 模板引擎（Flask 内置）
- **openpyxl** - Excel 文件处理
- **pytest** - 测试框架
- **AST** - 安全的价格表达式计算

#### 前端
- **HTML5** - 页面结构
- **CSS3** - 样式（使用 CSS 变量）
- **JavaScript** - 交互逻辑（模块化设计，无构建工具）
- **Chart.js 4.x** - 图表展示（CDN 引入）

### 架构模式

采用 Flask Blueprint 模块化架构，路由按功能模块拆分。

## 项目结构

```
TrainModelManager/
├── app.py              # Flask 主应用（应用工厂模式）
├── models.py           # SQLAlchemy 数据模型定义
├── config.py           # 配置文件（含 TestConfig）
├── init_db.py         # 数据库初始化脚本
├── requirements.txt    # Python 依赖
├── routes/             # Blueprint 路由模块
│   ├── main.py         # 首页和统计
│   ├── locomotive.py   # 机车模型
│   ├── carriage.py     # 车厢模型
│   ├── trainset.py     # 动车组模型
│   ├── locomotive_head.py  # 先头车模型
│   ├── options.py      # 信息维护
│   └── api.py          # API 端点（导入导出、自动填充、统计）
├── utils/              # 公共辅助函数
│   ├── helpers.py      # 通用辅助函数
│   ├── validators.py   # 验证函数
│   └── price_calculator.py  # 价格计算
├── static/             # 静态资源
│   ├── css/
│   │   └── style.css    # 全局样式
│   └── js/
│       ├── utils.js     # 核心 JS 模块
│       ├── app.js       # 页面初始化
│       ├── options.js   # 信息维护页面
│       └── system.js    # 系统维护页面
├── templates/          # Jinja2 模板
│   ├── base.html         # 基础模板（包含导航栏）
│   ├── index.html        # 汇总页面
│   ├── locomotive.html   # 机车模型列表和添加
│   ├── locomotive_edit.html # 机车模型编辑
│   ├── carriage.html     # 车厢模型列表和添加
│   ├── carriage_edit.html  # 车厢模型编辑
│   ├── trainset.html     # 动车组模型列表和添加
│   ├── trainset_edit.html  # 动车组模型编辑
│   ├── locomotive_head.html # 先头车模型列表和添加
│   ├── locomotive_head_edit.html # 先头车模型编辑
│   ├── options.html      # 信息维护页面
│   ├── system.html       # 系统维护页面
│   └── macros/           # Jinja2 宏
├── tests/              # 测试文件
│   ├── conftest.py       # 测试配置和 fixtures
│   ├── test_api.py       # API 测试
│   ├── test_crud.py      # CRUD 测试
│   ├── test_integration.py # 集成测试
│   ├── test_labels.py    # 标签测试
│   ├── test_models.py    # 模型测试
│   ├── test_options.py   # 信息维护测试
│   ├── test_routes.py    # 路由测试
│   └── test_validation.py # 验证测试
└── docs/               # 文档目录
    ├── design/           # 设计文档
    └── plans/            # 需求文档
```

## 数据模型设计

### 核心实体关系

```
PowerType (动力)
  └─> LocomotiveModel (机车型号)
      └─> Locomotive (机车模型)

PowerType
  └─> TrainsetModel (动车组车型)
      └─> Trainset (动车组模型)

Brand (品牌) - 所有模型共享
  ├─> Locomotive
  ├─> CarriageSet (车厢套装主表)
  ├─> Trainset
  └─> LocomotiveHead (先头车模型)

Depot (车辆段/机务段) - 机车、车厢、动车组共享（先头车不使用）
  ├─> Locomotive
  ├─> CarriageSet (车厢套装主表)
  └─> Trainset

ChipInterface (芯片接口) - 机车和动车组共享
  └─> Locomotive / Trainset

ChipModel (芯片型号) - 机车和动车组共享
  └─> Locomotive / Trainset

Merchant (购买商家) - 所有模型共享
  ├─> Locomotive
  ├─> CarriageSet
  ├─> Trainset
  └─> LocomotiveHead

LocomotiveSeries (机车系列)
  └─> LocomotiveModel

CarriageSeries (车厢系列)
  └─> CarriageModel

TrainsetSeries (动车组系列)
  └─> TrainsetModel

CarriageModel (车厢型号)
  ├─> CarriageSeries (系列)
  └─> CarriageItem (关联)

CarriageSet (车厢套装主表)
  └─> CarriageItem (一对多)
```

### 参考数据表（12 个）

| 表名 | 用途 | 关联 |
|-----|------|------|
| power_type | 动力 | 机车、动车组 |
| brand | 品牌 | 所有模型 |
| chip_interface | 芯片接口 | 机车、动车组 |
| chip_model | 芯片型号 | 机车、动车组 |
| merchant | 购买商家 | 所有模型 |
| depot | 车辆段/机务段 | 机车、车厢、动车组 |
| locomotive_series | 机车系列 | 机车型号 |
| carriage_series | 车厢系列 | 车厢型号 |
| trainset_series | 动车组系列 | 动车组型号 |

#### brand（品牌）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| name | String(100) | 唯一 | 品牌名称 |
| website | String(255) | | 官方网站 |
| search_url | String(255) | | 搜索URL模板，{query}为搜索词占位符 |

### 核心数据表（6 个）

| 表名 | 用途 | 关键特性 |
|-----|------|---------|
| locomotive | 机车模型 | 唯一性验证（机车号、编号）|
| locomotive_model | 机车型号 | 关联系列和动力类型 |
| carriage_set | 车厢套装主表 | 支持多车厢 |
| carriage_item | 车厢套装子表 | 每辆车独立信息 |
| carriage_model | 车厢型号 | 关联系列和类型（客车/货车/工程车）|
| trainset | 动车组模型 | 唯一性验证（动车号、编号）|
| trainset_model | 动车组型号 | 关联系列和动力类型 |
| locomotive_head | 先头车模型 | 简化版本 |

### 详细表结构

#### locomotive（机车模型）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| series_id | Integer | FK | 关联 locomotive_series |
| power_type_id | Integer | FK | 关联 power_type |
| model_id | Integer | FK | 关联 locomotive_model |
| brand_id | Integer | FK | 关联 brand |
| depot_id | Integer | FK | 关联 depot（机务段）|
| plaque | String(50) | | 挂牌 |
| color | String(50) | | 颜色 |
| scale | String(2) | | 比例（HO/N）|
| locomotive_number | String(12) | 唯一性(同比例) | 机车号 |
| decoder_number | String(4) | 唯一性(同比例) | 编号 |
| chip_interface_id | Integer | FK | 关联 chip_interface |
| chip_model_id | Integer | FK | 关联 chip_model |
| price | String(50) | | 价格表达式 |
| total_price | Float | | 总价（自动计算）|
| item_number | String(50) | | 货号 |
| product_url | String(1024) | | 产品地址 |
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

#### carriage_set（车厢套装主表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| brand_id | Integer | FK | 关联 brand |
| series_id | Integer | FK | 关联 carriage_series |
| depot_id | Integer | FK | 关联 depot（车辆段）|
| train_number | String(20) | | 车次 |
| plaque | String(50) | | 挂牌 |
| item_number | String(50) | | 货号 |
| scale | String(2) | | 比例（HO/N）|
| total_price | Float | | 总价 |
| product_url | String(1024) | | 产品地址 |
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

#### carriage_item（车厢套装子表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| set_id | Integer | FK | 关联 carriage_set |
| model_id | Integer | FK | 关联 carriage_model |
| car_number | String(20) | | 车辆号（1-20位字母、数字或连字符）|
| color | String(50) | | 颜色 |
| lighting | String(50) | | 灯光 |

#### trainset（动车组模型）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| series_id | Integer | FK | 关联 trainset_series |
| power_type_id | Integer | FK | 关联 power_type |
| model_id | Integer | FK | 关联 trainset_model |
| brand_id | Integer | FK | 关联 brand |
| depot_id | Integer | FK | 关联 depot（动车段）|
| plaque | String(50) | | 挂牌 |
| color | String(50) | | 颜色 |
| scale | String(2) | | 比例（HO/N）|
| formation | Integer | | 编组数 |
| trainset_number | String(12) | 唯一性(同比例) | 动车号 |
| decoder_number | String(4) | 唯一性(同比例) | 编号 |
| head_light | Boolean | | 头车灯（有/无）|
| interior_light | String(50) | | 室内灯 |
| chip_interface_id | Integer | FK | 关联 chip_interface |
| chip_model_id | Integer | FK | 关联 chip_model |
| price | String(50) | | 价格表达式 |
| total_price | Float | | 总价（自动计算）|
| item_number | String(50) | | 货号 |
| product_url | String(1024) | | 产品地址 |
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

#### locomotive_head（先头车模型）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| model_id | Integer | FK | 关联 trainset_model |
| brand_id | Integer | FK | 关联 brand |
| special_color | String(32) | | 特涂 |
| scale | String(2) | | 比例（HO/N）|
| head_light | Boolean | | 头车灯（有/无）|
| interior_light | String(50) | | 室内灯 |
| price | String(50) | | 价格表达式 |
| total_price | Float | | 总价（自动计算）|
| item_number | String(50) | | 货号 |
| product_url | String(1024) | | 产品地址 |
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

**注意**：先头车模型没有 depot_id（动车段）字段，与其他模型不同。

## 路由设计

### 页面路由（传统表单提交）

| 路由 | 方法 | 功能 |
|-----|------|------|
| `/` | GET | 汇总页面 |
| `/locomotive` | GET, POST | 机车模型列表和添加 |
| `/locomotive/edit/<id>` | GET, POST | 编辑机车模型 |
| `/locomotive/delete/<id>` | POST | 删除机车模型 |
| `/carriage` | GET, POST | 车厢套装列表和添加 |
| `/carriage/edit/<id>` | GET, POST | 编辑车厢套装 |
| `/carriage/delete/<id>` | POST | 删除车厢套装 |
| `/trainset` | GET, POST | 动车组列表和添加 |
| `/trainset/edit/<id>` | GET, POST | 编辑动车组 |
| `/trainset/delete/<id>` | POST | 删除动车组 |
| `/locomotive-head` | GET, POST | 先头车列表和添加 |
| `/locomotive-head/edit/<id>` | GET, POST | 编辑先头车 |
| `/locomotive-head/delete/<id>` | POST | 删除先头车 |
| `/options` | GET | 信息维护页面 |
| `/system` | GET | 系统维护页面 |
| `/system/reinit` | POST | 重新初始化数据库 |

### AJAX API 路由

| 路由 | 方法 | 功能 | 返回格式 |
|-----|------|------|---------|
| `/api/statistics` | GET | 获取汇总统计 | JSON |
| `/api/auto-fill/locomotive/<model_id>` | GET | 获取机车系列和动力类型 | JSON |
| `/api/auto-fill/trainset/<model_id>` | GET | 获取动车组系列和动力类型 | JSON |
| `/api/locomotive/add` | POST | AJAX 添加机车模型 | JSON |
| `/api/carriage/add` | POST | AJAX 添加车厢模型 | JSON |
| `/api/trainset/add` | POST | AJAX 添加动车组模型 | JSON |
| `/api/locomotive-head/add` | POST | AJAX 添加先头车模型 | JSON |
| `/api/options/<type>/edit` | POST | 行内编辑选项 | JSON |
| `/api/export/excel` | GET | 导出 Excel | File |
| `/api/import/excel` | POST | 导入 Excel | JSON |

### 信息维护路由

| 路由 | 方法 | 功能 |
|-----|------|------|
| `/options/power_type` | POST | 添加动力类型 |
| `/options/power_type/delete/<id>` | POST | 删除动力类型 |
| `/options/brand` | POST | 添加品牌 |
| `/options/brand/delete/<id>` | POST | 删除品牌 |
| ... | ... | （其他选项类型类似）|

## 核心功能设计

### 自动填充功能

**实现方式**: JavaScript + AJAX

**流程**:
1. 用户选择车型下拉框
2. 触发 `onchange` 事件
3. 发送 AJAX 请求到 `/api/auto-fill/...`
4. 后端查询关联的系列和类型
5. 返回 JSON 数据
6. 前端自动填充对应的下拉框

### 系列筛选车型功能

**实现方式**: JavaScript

**流程**:
1. 用户选择系列下拉框
2. 触发 `onchange` 事件
3. 前端根据系列 ID 过滤车型数组
4. 更新车型下拉框选项

### 唯一性验证

**实现方式**: 后端验证

**验证规则**:
- 机车号：4-12 位数字，允许前导 0
- 编号：1-4 位数字，无前导 0
- 动车号：3-12 位数字，允许前导 0
- 验证时排除当前记录（编辑场景）

**错误处理**:
- 返回 JSON 错误信息
- 前端在对应字段标签显示红色错误气泡
- 输入框显示红色边框和淡红色背景

### 价格表达式计算

**实现方式**: Python AST 解析

**SafeEval 类**:
```python
class SafeEval(ast.NodeVisitor):
    def __init__(self):
        self._operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.USub: operator.neg
        }

    def _allowed_nodes(self, node):
        return isinstance(node, (
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant
        ))

    def visit(self, node):
        if not self._allowed_nodes(node):
            raise ValueError(f"不安全的表达式节点: {type(node).__name__}")
        return super().visit(node)
```

**支持的表达式**: `288+538`, `288*2 + 500`

### 复制按钮功能

**实现方式**: JavaScript + data 属性

**流程**:
1. 模型列表表格每行包含 `data-*` 属性存储数据
2. 点击"复制"按钮
3. `FormFiller.copyFromRow()` 函数：
   - 从 data 属性读取数据
   - 填充到下方表单
   - 使用 ID 填充下拉框，名称显示
4. 日期字段使用 `value` 属性填充

### Excel 导入导出

#### 导出功能
**三种模式**:
- `models`: 仅导出模型数据
- `system`: 仅导出系统信息
- `all`: 导出全部数据

**实现**:
```python
def export_to_excel(mode):
    wb = Workbook()
    # 根据模式选择导出的表
    # 使用 openpyxl.styles.Font 设置标题行加粗
    # 文件名格式：train_models_YYYYMMDD_HHMMSS_RANDOM.xlsx
```

#### 导入功能
**三种模式**:
- `preview`: 预检查模式，返回冲突信息
- `skip`: 跳过冲突数据
- `overwrite`: 覆盖现有数据

**冲突检测**:
```python
def check_import_conflicts(file):
    # 检测唯一性约束冲突
    # 返回冲突列表
    return {
        'has_conflicts': True/False,
        'conflicts': [...],
        'sheets': [...]
    }
```

**智能导入**:
- 根据工作表名称自动识别导入类型
- 支持模型数据和系统信息的混合导入

## 前端模块设计

### utils.js - 核心模块

```javascript
Utils           // 通用工具（filterModelsBySeries、autoFill、showTab）
Api             // API 封装（post、postForm）
FormHelper      // 表单处理（clearErrors、showErrors、showSuccess、submitAjax）
CarriageManager // 车厢项管理（addRow、removeRow、handleSeriesChange）
ModelForm       // 模型表单（handleLocomotiveSeriesChange、autoFillLocomotive）
TableManager    // 表格管理（init、handleSort、handleFilter、applySortAndFilter）
FormFiller      // 表单填充（copyFromRow、fillField）
searchProduct   // 产品搜索（在官网搜索指定货号）
```

### app.js - 页面初始化

- 页面加载完成后初始化表格排序筛选
- 初始化 Chart.js 图表

### options.js - 信息维护页面

- `editRow()` - 开始编辑行
- `saveRow()` - 保存编辑
- `cancelEdit()` - 取消编辑
- `showTab()` - 标签页切换

### system.js - 系统维护页面

- 导出按钮处理（三种模式）
- 导入文件选择和冲突对话框
- 数据库重新初始化确认

## CSS 样式规范

### CSS 变量

```css
/* 颜色 */
--color-primary: #007bff;
--color-primary-dark: #0056b3;
--color-success: #28a745;
--color-success-dark: #218838;
--color-danger: #dc3545;
--color-danger-dark: #c82333;
--color-warning: #ffc107;
--color-secondary: #6c757d;
--color-info: #0d6efd;

/* 边框和间距 */
--border-radius: 4px;
--spacing-md: 1rem;
```

### 布局

- **响应式设计**: 支持 PC 和移动端
- **Flexbox**: 表单行使用 flex 布局
- **标签页**: 信息维护使用标签页切换

### 按钮样式

| 类型 | 颜色 | 尺寸 |
|-----|------|------|
| 通用按钮 | 蓝色 `#007bff` | 0.5rem 1rem |
| 编辑按钮 | 绿色 `#28a745` | 0.25rem 0.5rem |
| 删除按钮 | 红色 `#dc3545` | 0.25rem 0.5rem |
| 取消按钮 | 灰色 `#6c757d` | 0.25rem 0.5rem |

### 表单样式

- **表单组** (`form-group`): 上下边距 1rem
- **表单行** (`form-row`): Flex 布局，间距 1rem
- **内联表单** (`inline-form`): 输入框和按钮同行
- **错误状态**: 红色边框、淡红色背景、标签显示错误气泡

## 测试架构

### 测试配置

```python
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
```

### 测试文件结构

| 文件 | 说明 |
|-----|------|
| conftest.py | 测试配置和 fixtures |
| test_api.py | API 测试（自动填充、导入导出）|
| test_crud.py | CRUD 测试 |
| test_integration.py | 集成测试（Excel 往返）|
| test_labels.py | 表单标签测试 |
| test_models.py | 数据模型测试 |
| test_options.py | 信息维护测试 |
| test_routes.py | 路由测试 |
| test_validation.py | 验证规则测试 |

### 测试数据库隔离

- 使用内存数据库 `sqlite:///:memory:`
- 每个测试函数独立数据库会话
- 测试数据不影响开发数据库

## 安全考虑

### 1. 价格表达式安全
- 使用 AST 解析而非 eval
- 限制允许的节点类型
- 白名单操作符

### 2. 输入验证
- 后端格式验证
- 唯一性检查
- 空值处理

### 3. SQL 注入防护
- 使用 SQLAlchemy ORM
- 参数化查询

### 4. XSS 防护
- 使用 textContent 而非 innerHTML
- Jinja2 自动转义

### 5. CSRF 保护
- 生产环境建议添加 CSRF 保护

## 性能优化

### 当前优化
- 数据库连接池（SQLAlchemy 默认）
- 静态资源缓存（Flask 默认）
- 前端数据缓存（系列、车型数据传递给 JS）

### 未来优化
- 添加分页（数据量大时）
- 添加索引（查询优化）
- 考虑使用 Redis 缓存

## 部署建议

### 开发环境
```bash
python app.py
```

### 生产环境
- 使用 Gunicorn/uWSGI 作为 WSGI 服务器
- 使用 Nginx 作为反向代理
- 配置 MySQL 数据库
- 环境变量配置敏感信息

## 开发规范

### 代码风格
- 使用 2 个空格作为缩进
- 变量命名使用 `camelCase`
- 函数和类使用 `snake_case`
- 所有表和列需要添加注释

### 提交规范
- 使用 rebase 而不是 merge
- commit message 用英文
- 一个 commit 做一件事
- 格式：`[Type] subject`

### 错误处理
- 充分的错误处理，不吞掉异常
- 使用 logger 记录错误
- AJAX 返回 JSON 格式错误信息

## 数据初始化

### 预置数据清单

根据 `docs/plans/DatabaseInitDescription.txt`，需要在 `init_db.py` 中插入以下预置数据：

1. 动力类型：蒸汽、电力、内燃、双源
2. 机车系列：内电、内集、东风、韶山、和谐电、和谐内、复兴电、复兴内、Vossloh、Vectron、EMD、TRAXX
3. 机车系列-车型映射（每个型号关联系列和类型）
4. 动车组系列：ICE、TGV、CRH、CRH380、CR400、CR450、DESIRO、RailJet、新干线、特急、旅游列车
5. 动车组系列-车型映射
6. 芯片接口和型号
7. 车厢系列和型号
8. 品牌
9. 商家
10. 车辆段/机务段

## 开发注意事项

1. 所有表和列需要添加数据库注释
2. 车厢套装录入需要支持动态添加车厢
3. 价格表达式计算需要安全验证
4. 唯一性验证只在同一比例内进行
5. 日期字段必须传入 date 对象，不能是字符串
6. API 返回使用 snake_case（type_stats），前端需适配
7. Chart.js 图表实例需在销毁后重建，避免内存泄漏
8. 表格排序筛选使用 data-* 属性存储行数据
9. 复制按钮使用 data-* 属性存储模型数据
10. 使用 textContent 而非 innerHTML 防止 XSS
11. 页面名称"信息维护"而非"选项维护"

## 版本历史

- **v0.5.0**: 复制按钮、导入冲突检测、多模式导出
- **v0.4.0**: AJAX 表单提交、行内编辑
- **v0.3.0**: 系列筛选、Blueprint 重构
- **v0.2.0**: 自动填充、唯一性验证
- **v0.1.0**: 初始版本

## 参考文档

- `docs/plans/SystemDescription.txt` - 完整的功能需求
- `docs/plans/DatabaseInitDescription.txt` - 预置数据清单
- `docs/design/Train-Model-Manager-Implementation.md` - 详细实现计划
- `README.md` - 用户指南
- `CLAUDE.md` - AI 助手指导文档

## 文档结构

```
docs/
├── design/                          # 设计文档
│   ├── Train-Model-Manager-Design.md        # 整体架构设计（本文档）
│   └── Train-Model-Manager-Implementation.md # 详细实现计划
└── plans/                           # 需求文档
    ├── SystemDescription.txt        # 功能需求描述
    └── DatabaseInitDescription.txt  # 预置数据清单
```
