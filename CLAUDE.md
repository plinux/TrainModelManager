# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
火车模型管理系统 - 用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型。

## 当前状态
项目功能已完善，包含：
- 四种模型类型的 CRUD 操作
- 首页多维度统计（类型/比例/品牌/商家）支持表格和饼图展示
- 模型列表表格支持排序和筛选
- 模型列表复制按钮（快速填充表单）
- Excel 数据导入导出（多模式导出、智能导入、冲突检测）
- 信息维护功能（原名"选项维护"）

## 技术栈
- Python 3.10+
- Flask + Blueprints（模块化架构）
- SQLAlchemy
- SQLite（开发环境）/ MySQL（生产环境）
- Jinja2（Flask 内置模板引擎）
- HTML5 + JavaScript（前端无需构建工具）
- Chart.js 4.x（图表展示，CDN 引入）
- openpyxl（Excel 处理）
- pytest（测试框架）
- AST（Abstract Syntax Tree）用于安全的价格表达式计算

## 架构设计

### 后端架构
采用 Flask Blueprint 模块化架构，路由按功能模块拆分：
- `routes/main.py` - 首页和统计 API
- `routes/locomotive.py` - 机车模型路由
- `routes/carriage.py` - 车厢模型路由
- `routes/trainset.py` - 动车组模型路由
- `routes/locomotive_head.py` - 先头车模型路由
- `routes/options.py` - 信息维护（使用工厂函数）
- `routes/api.py` - 自动填充 API、Excel 导入导出、统计 API

### 前端架构
- `static/js/utils.js` - 核心工具模块（Utils、Api、FormHelper、CarriageManager、ModelForm、TableManager、FormFiller）
- `static/js/app.js` - 页面初始化
- `static/js/options.js` - 信息维护页面专用
- `static/js/system.js` - 系统维护页面专用
- `static/css/style.css` - 主样式文件（使用 CSS 变量）
- Chart.js 通过 CDN 引入

### 模板结构
- `base.html` - 基础布局模板
- `index.html` - 首页统计（标签页切换 + 表格/饼图）
- `locomotive.html` 等 - 模型列表页（表格排序筛选 + 复制按钮）
- `locomotive_edit.html` 等 - 模型编辑页
- `options.html` - 信息维护（标签页 + 行内编辑）
- `system.html` - 系统维护（导入导出 + 数据库初始化）
- `macros/` - Jinja2 宏（已定义但部分未使用）

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
pytest                     # 运行测试
pytest -v                  # 运行测试（详细输出）
```

## 核心数据模型

### 四种火车模型类型

1. **机车模型** (Locomotive): 系列、动力、车型、品牌、机务段、挂牌、颜色、比例、机车号、编号、芯片接口、芯片型号、价格、货号、产品地址、购买日期、购买商家

2. **车厢模型** (Carriage): 套装录入（CarriageSet + CarriageItem），品牌、系列、车辆段、车次、挂牌、货号、比例、总价、产品地址、购买日期、购买商家；车厢项：车型、车辆号、颜色、灯光

3. **动车组模型** (Trainset): 系列、动力、车型、品牌、动车段、挂牌、颜色、比例、编组、动车号、编号、头车灯、室内灯、芯片接口、芯片型号、价格、货号、产品地址、购买日期、购买商家

4. **先头车模型** (Locomotive Head): 车型、品牌、特涂、比例、头车灯、室内灯、价格、货号、产品地址、购买日期、购买商家（无动车段）

### 参考数据表
| 表名 | 说明 |
|-----|------|
| power_type | 动力（蒸汽、电力、内燃、双源）|
| brand | 品牌 - 所有模型共享|
| chip_interface | 芯片接口 - 机车和动车组共享|
| chip_model | 芯片型号 - 机车和动车组共享|
| merchant | 购买商家 - 所有模型共享|
| depot | 车辆段/机务段 - 机车、车厢、动车组共享|
| locomotive_series/model | 机车系列和型号 |
| carriage_series/model | 车厢系列和型号 |
| trainset_series/model | 动车组系列和型号 |

## 核心业务逻辑

### 自动填充规则
- 选择车型 → 自动填充系列和动力类型
- 系列筛选车型：选择系列后，车型下拉框自动过滤

### 唯一性验证
- 同一比例内：机车号（4-12位数字）、编号（1-4位数字）、动车号（3-12位数字）
- 品牌名称必须唯一

### 价格计算
- 后端使用 AST 安全解析表达式（如 `288+538`）
- SafeEval 类限制只允许数字和基本运算

### 日期处理
- 前端传入 'YYYY-MM-DD' 格式字符串
- 后端转换为 date 对象

### AJAX 表单提交
- 验证失败显示红色错误气泡
- 成功后显示绿色提示并刷新页面

### 复制按钮功能
- 模型列表每行有 data-* 属性存储数据
- FormFiller.copyFromRow() 从 data 属性读取并填充表单
- 下拉框使用 ID 填充，日期使用 value 属性

### Excel 导入导出

#### 导出
- 三种模式：models（仅模型）、system（仅系统信息）、all（全部）
- 文件名格式：train_models_YYYYMMDD_HHMMSS_RANDOM.xlsx
- 标题行加粗（openpyxl.styles.Font）

#### 导入
- 智能识别：根据工作表名称自动判断导入类型
- 冲突检测：预检查模式检测唯一性约束冲突
- 冲突处理：skip（跳过）或 overwrite（覆盖）
- 支持工作表：机车、车厢、动车组、先头车、动力、品牌、机务段/车辆段、商家、芯片接口、芯片型号、机车系列、车厢系列、动车组系列、机车车型、车厢车型、动车组车型

## 页面功能

### 首页（汇总统计）
- 标签页切换：按类型、按比例、按品牌、按商家
- 每个统计支持表格/饼图切换
- 页面顶部显示全局汇总（模型总数、总价）
- 使用 Chart.js 绘制饼图

### 模型列表页
- 表格支持点击列头排序（升序/降序）
- 表格支持列筛选（下拉选择）
- 排序指示器和筛选下拉框
- 复制按钮：点击后填充下方表单

### 信息维护页（原"选项维护"）
- 标签页切换不同选项类型
- 行内编辑功能
- 打开时不默认选中任何标签

### 系统维护页
- 数据导出：三种模式按钮
- 数据导入：选择文件后自动预检查，有冲突时显示对话框
- 数据库重新初始化：确认对话框

## API 路由

### 统计 API
- `GET /api/statistics` - 返回 type_stats、scale_stats、brand_stats、merchant_stats

### 添加模型 API
- `POST /api/locomotive/add`
- `POST /api/carriage/add`
- `POST /api/trainset/add`
- `POST /api/locomotive-head/add`

### 自动填充 API
- `GET /api/auto-fill/locomotive/<model_id>`
- `GET /api/auto-fill/trainset/<model_id>`

### Excel 导入导出 API
- `GET /api/export/excel?mode=<models|system|all>` - 导出
- `POST /api/import/excel` - 导入（FormData: file, mode）

## 前端 JavaScript 模块

### utils.js 核心对象
```javascript
Utils           // 通用工具（filterModelsBySeries、autoFill、showTab）
Api             // API 封装（post、postForm）
FormHelper      // 表单处理（clearErrors、showErrors、showSuccess、submitAjax）
CarriageManager // 车厢项管理（addRow、removeRow、handleSeriesChange）
ModelForm       // 模型表单（handleLocomotiveSeriesChange、autoFillLocomotive）
TableManager    // 表格管理（init、handleSort、handleFilter、applySortAndFilter）
FormFiller      // 表单填充（copyFromRow、fillField）
```

### 全局函数（兼容层）
为保持向后兼容，utils.js 导出全局函数：
- `filterLocomotiveModelsBySeries`、`handleLocomotiveSeriesChange`、`autoFillLocomotive`
- `filterTrainsetModelsBySeries`、`handleTrainsetSeriesChange`、`autoFillTrainset`
- `addCarriageRow`、`submitFormAjax`、`initTableSortFilter`
- `searchProduct` - 在官网搜索指定货号

## CSS 样式规范

### CSS 变量
```css
--color-primary: #007bff;
--color-success: #28a745;
--color-danger: #dc3545;
--border-radius: 4px;
--spacing-md: 1rem;
```

### 关键类
- `.sortable-filterable` - 可排序筛选的表格
- `.stats-tabs` / `.stats-tab` - 统计标签页
- `.toggle-btn` - 视图切换按钮
- `.form-row` / `.form-group` - 表单布局

## 文件结构
```
TrainModelManager/
├── app.py              # Flask 主应用（应用工厂模式）
├── models.py           # SQLAlchemy 数据模型
├── config.py           # 配置文件（含 TestConfig）
├── init_db.py          # 数据库初始化
├── requirements.txt    # Python 依赖
├── routes/             # Blueprint 路由模块
│   ├── main.py         # 首页和统计
│   ├── locomotive.py   # 机车模型
│   ├── carriage.py     # 车厢模型
│   ├── trainset.py     # 动车组模型
│   ├── locomotive_head.py  # 先头车模型
│   ├── options.py      # 信息维护
│   └── api.py          # API 端点
├── utils/              # 公共辅助函数
│   ├── helpers.py      # 通用辅助函数
│   ├── validators.py   # 验证函数
│   └── price_calculator.py  # 价格计算
├── static/
│   ├── css/style.css   # 主样式文件
│   └── js/
│       ├── utils.js    # 核心 JS 模块
│       ├── app.js      # 页面初始化
│       ├── options.js  # 信息维护专用
│       └── system.js   # 系统维护专用
├── templates/          # Jinja2 模板
│   ├── base.html       # 基础模板
│   ├── index.html      # 首页统计
│   ├── locomotive.html # 机车列表
│   ├── locomotive_edit.html
│   ├── carriage.html
│   ├── carriage_edit.html
│   ├── trainset.html
│   ├── trainset_edit.html
│   ├── locomotive_head.html
│   ├── locomotive_head_edit.html
│   ├── options.html    # 信息维护
│   ├── system.html     # 系统维护
│   ├── macros/         # Jinja2 宏
│   ├── 404.html
│   └── 500.html
├── tests/              # 测试文件
│   ├── conftest.py     # 测试配置
│   ├── test_api.py     # API 测试
│   ├── test_crud.py    # CRUD 测试
│   ├── test_integration.py  # 集成测试
│   ├── test_labels.py  # 标签测试
│   ├── test_models.py  # 模型测试
│   ├── test_options.py # 选项测试
│   ├── test_routes.py  # 路由测试
│   └── test_validation.py  # 验证测试
└── docs/               # 文档目录
    ├── design/          # 设计文档
    │   ├── Train-Model-Manager-Design.md
    │   └── Train-Model-Manager-Implementation.md
    └── plans/           # 需求文档
        ├── SystemDescription.txt
        └── DatabaseInitDescription.txt
```

## 测试

### 测试数据库隔离
- 使用 TestConfig 配置（内存数据库）
- 每个测试函数独立数据库会话
- 不会影响开发数据库

### 运行测试
```bash
pytest                    # 运行所有测试
pytest -v                 # 详细输出
pytest tests/test_api.py  # 运行特定文件
pytest -k "locomotive"    # 运行名称匹配的测试
```

## 开发注意事项
- 日期字段必须传入 date 对象，不能是字符串
- API 返回使用 snake_case（type_stats），前端需适配
- Chart.js 图表实例需在销毁后重建，避免内存泄漏
- 表格排序筛选使用 data-* 属性存储行数据
- 复制按钮使用 data-* 属性存储模型数据
- 使用 textContent 而非 innerHTML 防止 XSS
- 页面名称"信息维护"而非"选项维护"

## 优化机会（待执行）

### 高优先级
| 优化项 | 说明 | 预计减少 |
|-------|------|---------|
| 使用 Jinja2 宏 | 模板中存在重复的表单字段 HTML | ~500 行 |
| 合并添加/编辑页面 | 编辑页与添加页结构相同 | ~300 行 |
| 删除未使用 CSS | `.stat-card`、`.empty-state`、`.tooltip` 等 | ~80 行 |
| 提取后端 CRUD 公共逻辑 | 路由文件结构高度重复 | ~200 行 |

### 中优先级
| 优化项 | 说明 |
|-------|------|
| 简化 app.js | 页面初始化逻辑可合并到 utils.js |
| 清理兼容函数 | utils.js 全局函数层可精简 |

## 代码优化记录

### 第四次优化内容（v0.6.0）
1. **JavaScript 函数提取**
   - `searchProduct` 函数从 4 个模板文件提取到 utils.js
   - 减少约 28 行重复代码

2. **CSS 变量统一**
   - `btn-search` 使用 `--color-info` 替代硬编码颜色
   - `btn-copy` 使用 `--color-secondary` 替代硬编码颜色

3. **内联样式外置**
   - options.html 内联样式移至 style.css
   - system.html 内联样式移至 style.css
   - 统一页面样式管理

### 第三次优化内容（v0.5.0）
1. **复制按钮功能**
   - 模型列表页添加复制按钮
   - FormFiller 模块处理表单填充
   - 使用 data-* 属性存储行数据

2. **Excel 导入导出增强**
   - 三种导出模式（模型/系统/全部）
   - 智能导入（自动识别工作表类型）
   - 冲突检测和处理（预检查/跳过/覆盖）
   - 导出文件标题行加粗
   - 文件名包含日期时间随机数

3. **页面重命名**
   - "选项维护"更名为"信息维护"
   - 移除默认标签选中

4. **测试改进**
   - 添加 TestConfig 实现数据库隔离
   - 101 个测试全部通过

### 第二次优化内容
1. **首页统计增强**
   - 添加比例、品牌、商家多维度统计
   - 标签页切换布局
   - Chart.js 饼图展示
   - 全局汇总信息

2. **表格排序筛选**
   - 纯前端实现（TableManager 模块）
   - 点击列头排序，下拉框筛选
   - 支持数字和中文排序

### 第一次优化内容
1. **Blueprint 模块化重构**
2. **公共辅助函数提取**（utils/ 目录）
3. **信息维护工厂函数**
4. **JavaScript 模块化**（utils.js）
5. **Jinja2 宏提取**（macros/ 目录）
6. **CSS 变量统一**

## 参考文档
- `docs/plans/SystemDescription.txt` - 完整的功能需求
- `docs/plans/DatabaseInitDescription.txt` - 预置数据清单
- `docs/design/Train-Model-Manager-Design.md` - 详细架构文档
- `docs/design/Train-Model-Manager-Implementation.md` - 详细实现计划
- `README.md` - 用户指南
