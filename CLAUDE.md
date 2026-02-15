# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
火车模型管理系统 - 用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型。

## 当前状态
项目功能已完善，包含：
- 四种模型类型的 CRUD 操作
- 首页多维度统计（类型/比例/品牌/商家）支持表格和饼图展示
- 模型列表表格支持排序和筛选
- Excel 数据导入导出
- 选项维护功能

## 技术栈
- Python 3.10+
- Flask + Blueprints（模块化架构）
- SQLAlchemy
- SQLite（开发环境）/ MySQL（生产环境）
- Jinja2（Flask 内置模板引擎）
- HTML5 + JavaScript（前端无需构建工具）
- Chart.js 4.x（图表展示）
- AST（Abstract Syntax Tree）用于安全的价格表达式计算

## 架构设计

### 后端架构
采用 Flask Blueprint 模块化架构，路由按功能模块拆分：
- `routes/main.py` - 首页和统计 API
- `routes/locomotive.py` - 机车模型路由
- `routes/carriage.py` - 车厢模型路由
- `routes/trainset.py` - 动车组模型路由
- `routes/locomotive_head.py` - 先头车模型路由
- `routes/options.py` - 选项维护（使用工厂函数）
- `routes/api.py` - 自动填充 API 和 Excel 导入导出

### 前端架构
- `static/js/utils.js` - 核心工具模块（Utils、Api、FormHelper、CarriageManager、ModelForm、TableManager）
- `static/js/app.js` - 页面初始化（可进一步简化）
- `static/js/options.js` - 选项维护页面专用
- `static/css/style.css` - 主样式文件（使用 CSS 变量）
- Chart.js 通过 CDN 引入

### 模板结构
- `base.html` - 基础布局模板
- `index.html` - 首页统计（标签页切换 + 表格/饼图）
- `locomotive.html` 等 - 模型列表页（表格排序筛选）
- `locomotive_edit.html` 等 - 模型编辑页
- `options.html` - 选项维护（标签页 + 行内编辑）
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
```

## 核心数据模型

### 四种火车模型类型

1. **机车模型** (Locomotive): 系列、动力类型、车型、品牌、机务段、挂牌、颜色、比例、机车号、编号、芯片接口、芯片型号、价格、货号、购买日期、购买商家

2. **车厢模型** (Carriage): 套装录入（CarriageSet + CarriageItem），品牌、系列、车型、类型、车辆号、车辆段、车次、挂牌、货号、颜色、灯光、比例、总价、购买日期、购买商家

3. **动车组模型** (Trainset): 系列、动力类型、车型、品牌、动车段、挂牌、颜色、比例、编组、动车号、编号、头车灯、室内灯、芯片接口、芯片型号、价格、货号、购买日期、购买商家

4. **先头车模型** (Locomotive Head): 车型、品牌、动车段、特涂、比例、头车灯、室内灯、价格、货号、购买日期、购买商家

### 参考数据表
| 表名 | 说明 |
|-----|------|
| power_type | 动力类型（蒸汽、电力、内燃、双源）|
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

### 价格计算
- 后端使用 AST 安全解析表达式（如 `288+538`）
- SafeEval 类限制只允许数字和基本运算

### 日期处理
- 前端传入 'YYYY-MM-DD' 格式字符串
- 后端转换为 date 对象

### AJAX 表单提交
- 验证失败显示红色错误气泡
- 成功后显示绿色提示并刷新页面

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

### 选项维护页
- 标签页切换不同选项类型
- 行内编辑功能
- Excel 导入导出
- 数据库重新初始化

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

### Excel 导入导出
- `POST /api/import/<type>`
- `GET /api/export/<type>`

## 前端 JavaScript 模块

### utils.js 核心对象
```javascript
Utils           // 通用工具（filterModelsBySeries、autoFill、showTab）
Api             // API 封装（post、postForm）
FormHelper      // 表单处理（clearErrors、showErrors、showSuccess、submitAjax）
CarriageManager // 车厢项管理（addRow、removeRow、handleSeriesChange）
ModelForm       // 模型表单（handleLocomotiveSeriesChange、autoFillLocomotive）
TableManager    // 表格管理（init、handleSort、handleFilter、applySortAndFilter）
```

### 全局函数（兼容层）
为保持向后兼容，utils.js 导出全局函数：
- `filterLocomotiveModelsBySeries`、`handleLocomotiveSeriesChange`、`autoFillLocomotive`
- `filterTrainsetModelsBySeries`、`handleTrainsetSeriesChange`、`autoFillTrainset`
- `addCarriageRow`、`submitFormAjax`、`initTableSortFilter`

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
├── config.py           # 配置文件
├── init_db.py          # 数据库初始化
├── requirements.txt    # Python 依赖
├── routes/             # Blueprint 路由模块
│   ├── main.py         # 首页和统计
│   ├── locomotive.py   # 机车模型
│   ├── carriage.py     # 车厢模型
│   ├── trainset.py     # 动车组模型
│   ├── locomotive_head.py  # 先头车模型
│   ├── options.py      # 选项维护
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
│       └── options.js  # 选项维护专用
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
│   ├── options.html    # 选项维护
│   ├── macros/         # Jinja2 宏
│   ├── 404.html
│   └── 500.html
└── docs/               # 文档目录
```

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
| 内联样式外置 | options.html 内联样式移至 CSS 文件 |

## 开发注意事项
- 日期字段必须传入 date 对象，不能是字符串
- API 返回使用 snake_case（type_stats），前端需适配
- Chart.js 图表实例需在销毁后重建，避免内存泄漏
- 表格排序筛选使用 data-* 属性存储行数据

## 代码优化记录

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
3. **选项维护工厂函数**
4. **JavaScript 模块化**（utils.js）
5. **Jinja2 宏提取**（macros/ 目录）
6. **CSS 变量统一**

## 参考文档
- `docs/SystemDescription.txt` - 完整的功能需求
- `docs/DatabaseInitDescription.txt` - 预置数据清单
