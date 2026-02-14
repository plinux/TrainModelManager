# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
火车模型管理系统 - 用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型。

## 当前状态
项目处于早期开发阶段，核心功能已完成并持续优化。数据库初始化已完成，包含预置数据。

## 技术栈
- Python 3.10+
- Flask
- SQLAlchemy
- SQLite（开发环境）/ MySQL（生产环境）
- Jinja2（Flask 内置模板引擎）
- HTML5 + JavaScript（前端无需构建工具）
- AST（Abstract Syntax Tree）用于安全的价格表达式计算

## 架构设计
单体 Flask 应用架构，所有路由集中在 `app.py` 中管理。如后期代码增多，可平滑过渡到模块化结构（Blueprints）。

## 虚拟环境
```bash
# 激活虚拟环境
source myenv/bin/activate # Linux/macOS
myenv\Scripts\activate     # Windows

# 退出虚拟环境
deactivate
```

## 开发命令
```bash
# 激活虚拟环境后执行
python app.py              # 启动 Flask 开发服务器
python init_db.py          # 初始化数据库（添加预置数据）
```

## 核心数据模型（基于需求文档）

### 四种火车模型类型

1. **机车模型** (Locomotive):
   - 包含系列、动力类型、车型、品牌、机务段、挂牌、颜色、比例、机车号、编号、芯片接口、芯片型号、价格、总价、货号、购买日期、购买商家

2. **车厢模型** (Carriage):
   - 支持套装录入（CarriageSet + CarriageItem）
   - 包含品牌、系列、车型、类型（客车/货车/工程车）、车辆号、车辆段、车次、挂牌、货号、颜色、灯光、比例、总价、购买日期、购买商家
   - 类型字段固定为三种：客车、货车、工程车

3. **动车组模型** (Trainset):
   - 包含系列、动力类型、车型、品牌、动车段、挂牌、颜色、比例、编组、动车号、编号、头车灯、室内灯、芯片接口、芯片型号、价格、总价、货号、购买日期、购买商家

4. **先头车模型** (Locomotive Head):
   - 包含车型、品牌、动车段、特涂、比例、头车灯、室内灯、价格、总价、货号、购买日期、购买商家

### 参考数据表（12 个）

| 表名 | 字段 | 说明 |
|-----|------|------|
| power_type | id, name | 动力类型（蒸汽、电力、内燃、双源）|
| brand | id, name | 品牌（百万城、长鸣等）- 所有模型共享|
| chip_interface | id, name | 芯片接口（NEXT18、MTC21等）- 机车和动车组共享|
| chip_model | id, name | 芯片型号（动芯5323、MS350P22等）- 机车和动车组共享|
| merchant | id, name | 购买商家 - 所有模型共享|
| depot | id, name | 车辆段/机务段 - 机车、车厢、动车组共享|
| locomotive_series | id, name | 机车系列（东风、韶山等）|
| locomotive_model | id, name, series_id, power_type_id | 机车型号，关联系列和类型 |
| carriage_series | id, name | 车厢系列（25G、25B等）|
| carriage_model | id, name, series_id, type | 车厢型号，关联系列和类型（客车/货车/工程车）|
| carriage_set | id, brand_id, series_id, depot_id, train_number, plaque, item_number, scale, total_price, purchase_date, merchant_id | 车厢套装主表 |
| carriage_item | id, set_id, model_id, car_number, color, lighting | 车厢套装子表（每辆车的详细信息）|
| trainset_series | id, name | 动车组系列（ICE、TGV、新干线等）|
| trainset_model | id, name, series_id, power_type_id | 动车组车型，关联系列和类型|

## 核心业务逻辑

### 自动填充规则（通过 JavaScript 实现）
- 选择机车车型 → 自动填充机车系列和机车动力类型
- 选择车厢车型 → 自动填充车厢系列和类型
- 选择动车组车型 → 自动填充动车组系列和动力类型
- 系列筛选车型：选择系列后，车型下拉框自动过滤为该系列的车型

### 唯一性验证（提交时验证，后端处理）
- 同一比例内唯一：
  - 机车号：4-12 位数字，前导 0
  - 编号：1-4 位数字，无前导 0
  - 动车号：3-12 位数字，前导 0
- 重复时返回错误并显示红色边框和错误气泡

### 价格计算（安全表达式求值）
- 后端使用 Python AST（Abstract Syntax Tree）解析表达式
- SafeEval 类限制只允许特定节点类型：ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant
- 支持的操作符：+、-、*、/、()
- Python 3.8+ 使用 ast.Constant 替代已弃用的 ast.Num
- 前端显示表达式（如 `288+538`），后端计算总价并填充

### 日期处理
- SQLite Date 类型只接受 Python date 对象
- 前端传入字符串 'YYYY-MM-DD' 格式
- 后端使用 datetime.strptime() 转换为 date 对象
- 空值使用 date.today() 作为默认值

### 车厢套装
- 前端动态表单，支持一套多车厢录入
- 每个车厢独立：车型、车辆号、颜色、灯光
- 支持动态添加/删除车厢项
- 主表单选择系列后，新车厢项自动继承系列

### AJAX 表单提交（添加模型）
- 添加模型表单使用 AJAX 提交，不刷新页面
- API 路由返回 JSON 格式响应
- 验证失败时：
  - 保留已填写内容
  - 在对应字段标签上显示红色错误气泡
  - 输入框显示红色边框和淡红色背景
- 成功后显示绿色成功提示并刷新页面

### 行内编辑（选项维护页面）
- 选项维护页面使用行内编辑，不跳转到编辑页面
- 点击"编辑"按钮，对应行的字段变为可编辑状态
- 保存/取消按钮切换显示
- 使用 AJAX 提交修改

### 级联删除检查
- 删除系列/车型前检查是否被使用
- 防止删除正在使用的数据

## 页面规划

1. **汇总页面** (`/`): 展示各类型和维度的花费统计
2. **机车模型页面** (`/locomotive`): 机车模型列表和添加
3. **车厢模型页面** (`/carriage`): 车厢套装列表和添加
4. **动车组模型页面** (`/trainset`): 动车组列表和添加
5. **先头车模型页面** (`/locomotive-head`): 先头车列表和添加
6. **选项维护页面** (`/options`): 使用标签页切换，包含以下内容：
   - 购买信息：品牌、商家
   - 铁路信息：动力类型、局段
   - 芯片信息：芯片接口、芯片型号
   - 机车信息：机车系列、机车型号
   - 车厢信息：车厢系列、车厢型号
   - 动车组信息：动车组系列、动车组型号
   - 重新初始化数据库按钮（页面右上角，position: absolute）

## API 路由

### 添加模型 API
- `POST /api/locomotive/add` - AJAX 添加机车模型
- `POST /api/carriage/add` - AJAX 添加车厢模型
- `POST /api/trainset/add` - AJAX 添加动车组模型
- `POST /api/locomotive-head/add` - AJAX 添加先头车模型

### 自动填充 API
- `GET /api/auto-fill/locomotive/<int:model_id>` - 获取机车系列和动力类型
- `GET /api/auto-fill/carriage/<int:series_id>` - 获取车厢类型
- `GET /api/auto-fill/trainset/<int:model_id>` - 获取动车组系列和动力类型

### 统计 API
- `GET /api/statistics` - 获取汇总统计数据

### 选项维护 API
- `POST /api/options/<string:type>/edit` - 行内编辑选项

### 重新初始化数据库
- `POST /options/reinit` - 重新初始化数据库（需要双重确认）

## 前端 JavaScript 模块

### static/js/app.js
- 表单自动填充函数
- 系列筛选车型功能
- 车厢项动态添加/删除
- AJAX 表单提交和错误处理
- 标签页切换

### static/js/options.js
- 选项维护页面行内编辑
- 重新初始化数据库对话框处理
- 标签页切换

## CSS 样式规范

### 按钮样式
- 通用按钮：`padding: 0.5rem 1rem`
- 表格中的操作按钮：`padding: 0.25rem 0.5rem; font-size: 0.875rem`
- 编辑按钮：绿色 `#28a745`
- 删除按钮：红色 `#dc3545`
- 取消按钮：灰色 `#6c757d`

### 表单样式
- 表单行使用 flexbox 布局
- 内联表单（.inline-form）使输入框和按钮在同一行
- 错误状态：红色边框、淡红色背景、标签显示错误气泡

### 布局
- 选项维护页面使用标签页布局
- 标签按钮紧凑样式：`padding: 0.05rem 0.2rem; font-size: 0.85rem`
- 选项组横向排列，组内标签纵向排列

## 验证函数

### 格式验证
- `validate_locomotive_number(number)`: 验证机车号（4-12位数字，前导0）
- `validate_decoder_number(number)`: 验证编号（1-4位数字，无前导0）
- `validate_trainset_number(number)`: 验证动车号（3-12位数字，前导0）
- `validate_car_number(number)`: 验证车辆号（3-10位数字，无前导0）

### 唯一性检查
- `check_duplicate(table, field, value, scale)`: 检查同一比例内的唯一性

## 价格计算实现

### SafeEval 类
```python
class SafeEval(ast.NodeVisitor):
    """安全的表达式求值器，只允许数字和基本运算"""

    # 允许的节点类型
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant

    # 支持的操作符
    ast.Add (+), ast.Sub (-), ast.Mult (*), ast.Div (/), ast.USub (-)
```

## 开发注意事项
- 当前处于开发调试阶段，数据库可随时删除重建
- 所有表和列需要添加 `__tablename__` 注释和字段说明注释
- 车厢套装录入需要支持动态添加车厢
- Python 3.8+ 使用 ast.Constant 替代已弃用的 ast.Num
- 日期字段必须传入 date 对象，不能是字符串

## 文件结构
```
TrainModelManager/
├── app.py              # Flask 主应用
├── models.py           # SQLAlchemy 数据模型定义
├── config.py           # 配置文件
├── init_db.py         # 数据库初始化脚本
├── requirements.txt    # Python 依赖
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── options.js
├── templates/         # Jinja2 模板
│   ├── base.html      # 基础模板
│   ├── index.html     # 汇总页面
│   ├── locomotive.html
│   ├── locomotive_edit.html
│   ├── carriage.html
│   ├── carriage_edit.html
│   ├── trainset.html
│   ├── trainset_edit.html
│   ├── locomotive_head.html
│   ├── locomotive_head_edit.html
│   └── options.html   # 选项维护（含标签页）
└── docs/             # 文档目录
```

## 参考文档
- 项目根目录包含以下需求文档：
  - `系统描述.txt` - 完整的功能需求
  - `数据库初始化要求.txt` - 预置数据清单
