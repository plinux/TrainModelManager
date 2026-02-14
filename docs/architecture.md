# 火车模型管理系统 - 架构文档

## 项目概述
火车模型管理系统是一个基于 Flask 的 Web 应用，用于管理火车模型藏品、统计和展示。

## 技术栈

### 后端
- **Python 3.10+** - 主要编程语言
- **Flask** - Web 框架
- **SQLAlchemy** - ORM 框架
- **SQLite** - 开发环境数据库
- **MySQL** - 生产环境数据库（可选）
- **Jinja2** - 模板引擎（Flask 内置）

### 前端
- **HTML5** - 页面结构
- **CSS3** - 样式
- **JavaScript** - 交互逻辑（无构建工具）

## 项目结构

```
TrainModelManager/
├── app.py              # Flask 主应用（单文件架构）
├── models.py           # SQLAlchemy 数据模型定义
├── config.py           # 配置文件（数据库连接等）
├── init_db.py         # 数据库初始化脚本
├── requirements.txt    # Python 依赖
├── static/             # 静态资源
│   ├── css/
│   │   └── style.css    # 全局样式
│   └── js/
│       ├── app.js         # 主页 JavaScript
│       └── options.js    # 选项维护页面 JavaScript
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
│   └── options.html     # 选项维护页面
└── docs/               # 文档目录
```

## 数据模型设计

### 核心实体关系

```
PowerType (动力类型)
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

Depot (车辆段/机务段) - 机车、车厢、动车组共享
  ├─> Locomotive
  ├─> CarriageItem (车厢套装子表)
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

### 数据表详细说明

#### 参考数据表（12 个）

| 表名 | 用途 | 关联 |
|-----|------|------|
| power_type | 动力类型 | 机车、动车组 |
| brand | 品牌 | 所有模型 |
| chip_interface | 芯片接口 | 机车、动车组 |
| chip_model | 芯片型号 | 机车、动车组 |
| merchant | 购买商家 | 所有模型 |
| depot | 车辆段/机务段 | 机车、车厢、动车组 |
| locomotive_series | 机车系列 | 机车型号 |
| carriage_series | 车厢系列 | 车厢型号 |
| trainset_series | 动车组系列 | 动车组型号 |

#### 业务数据表（6 个）

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
| trainset_series | 动车组系列 | 动车组型号参考 |
| trainset_model | 动车组型号 | 关联系列和动力类型 |

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
| `/options` | GET | 选项维护页面 |
| `/options/reinit` | POST | 重新初始化数据库 |

### AJAX API 路由

| 路由 | 方法 | 功能 | 返回格式 |
|-----|------|------|---------|
| `/api/statistics` | GET | 获取汇总统计 | JSON |
| `/api/auto-fill/locomotive/<model_id>` | GET | 获取机车系列和动力类型 | JSON |
| `/api/auto-fill/carriage/<series_id>` | GET | 获取车厢类型 | JSON |
| `/api/auto-fill/trainset/<model_id>` | GET | 获取动车组系列和动力类型 | JSON |
| `/api/locomotive/add` | POST | AJAX 添加机车模型 | JSON |
| `/api/carriage/add` | POST | AJAX 添加车厢模型 | JSON |
| `/api/trainset/add` | POST | AJAX 添加动车组模型 | JSON |
| `/api/locomotive-head/add` | POST | AJAX 添加先头车模型 | JSON |
| `/api/options/<type>/edit` | POST | 行内编辑选项 | JSON |

### 选项维护路由

| 路由 | 方法 | 功能 |
|-----|------|------|
| `/options/power_type` | POST | 添加动力类型 |
| `/options/power_type/delete/<id>` | POST | 删除动力类型 |
| `/options/brand` | POST | 添加品牌 |
| `/options/brand/delete/<id>` | POST | 删除品牌 |
| `/options/merchant` | POST | 添加商家 |
| `/options/merchant/delete/<id>` | POST | 删除商家 |
| `/options/depot` | POST | 添加车辆段 |
| `/options/depot/delete/<id>` | POST | 删除车辆段 |
| `/options/chip_interface` | POST | 添加芯片接口 |
| `/options/chip_interface/delete/<id>` | POST | 删除芯片接口 |
| `/options/chip_model` | POST | 添加芯片型号 |
| `/options/chip_model/delete/<id>` | POST | 删除芯片型号 |
| `/options/locomotive_series` | POST | 添加机车系列 |
| `/options/locomotive_series/delete/<id>` | POST | 删除机车系列 |
| `/options/locomotive_model` | POST | 添加机车型号 |
| `/options/locomotive_model/delete/<id>` | POST | 删除机车型号 |
| `/options/carriage_series` | POST | 添加车厢系列 |
| `/options/carriage_series/delete/<id>` | POST | 删除车厢系列 |
| `/options/carriage_model` | POST | 添加车厢型号 |
| `/options/carriage_model/delete/<id>` | POST | 删除车厢型号 |
| `/options/trainset_series` | POST | 添加动车组系列 |
| `/options/trainset_series/delete/<id>` | POST | 删除动车组系列 |
| `/options/trainset_model` | POST | 添加动车组型号 |
| `/options/trainset_model/delete/<id>` | POST | 删除动车组型号 |

## 核心功能实现

### 1. 自动填充功能

**实现方式**: JavaScript + AJAX

**流程**:
1. 用户选择车型下拉框
2. 触发 `onchange` 事件
3. 发送 AJAX 请求到 `/api/auto-fill/...`
4. 后端查询关联的系列和类型
5. 返回 JSON 数据
6. 前端自动填充对应的下拉框

### 2. 系列筛选车型功能

**实现方式**: JavaScript

**流程**:
1. 用户选择系列下拉框
2. 触发 `onchange` 事件
3. 前端根据系列 ID 过滤车型数组
4. 更新车型下拉框选项

### 3. 唯一性验证

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

### 4. 价格表达式计算

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

### 5. 日期处理

**问题**: SQLite Date 类型只接受 Python date 对象

**解决方案**:
```python
purchase_date = request.form.get('purchase_date')
if purchase_date and purchase_date.strip():
    purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
else:
    purchase_date = date.today()
```

### 6. AJAX 表单提交

**流程**:
1. 用户填写表单并提交
2. `submitFormAjax()` 函数拦截默认提交
3. 收集表单数据并转换为 JSON
4. 发送 POST 请求到 API
5. 后端验证并处理
6. 返回 JSON 响应（成功/失败）
7. 成功：显示绿色提示，1秒后刷新页面
8. 失败：显示错误气泡

### 7. 行内编辑（选项维护）

**流程**:
1. 点击"编辑"按钮
2. `editRow()` 函数：
   - 切换按钮显示（隐藏编辑，显示保存/取消）
   - 存储原始值
   - 将文本内容替换为输入框/下拉框
3. 用户修改内容
4. 点击"保存"按钮
   - `saveRow()` 函数发送 AJAX 请求
   - 成功后恢复为文本显示
5. 点击"取消"按钮
   - `cancelEdit()` 函数恢复原始值

### 8. 车厢套装动态表单

**流程**:
1. 主表单包含套装基本信息
2. 点击"添加车厢"按钮
3. `addCarriageRow()` 函数：
   - 创建新的车厢项（div）
   - 包含系列、车型、车辆号、颜色、灯光字段
   - 如果主表单已选择系列，自动继承
4. 系列选择变化时，自动过滤车型

## 前端模块

### app.js - 主要功能

- `filterLocomotiveModelsBySeries()` - 机车系列筛选车型
- `filterTrainsetModelsBySeries()` - 动车组系列筛选车型
- `filterModelsBySeries()` - 车厢系列筛选车型
- `handleLocomotiveSeriesChange()` - 机车系列变化处理
- `handleTrainsetSeriesChange()` - 动车组系列变化处理
- `autoFillLocomotive()` - 机车车型自动填充
- `autoFillCarriage()` - 车厢系列自动填充
- `autoFillTrainset()` - 动车组车型自动填充
- `addCarriageRow()` - 动态添加车厢项
- `removeCarriageRow()` - 删除车厢项
- `showTab()` - 标签页切换
- `submitFormAjax()` - AJAX 表单提交
- `clearErrors()` - 清除错误显示
- `showErrors()` - 显示错误气泡
- `showSuccessMessage()` - 显示成功消息

### options.js - 选项维护功能

- `editRow()` - 开始编辑行
- `saveRow()` - 保存编辑
- `cancelEdit()` - 取消编辑
- `showTab()` - 标签页切换
- `openReinitDialog()` - 打开重置数据库对话框
- `closeReinitDialog()` - 关闭对话框
- `checkReinitInput()` - 验证输入
- `submitReinit()` - 提交重置

## CSS 样式规范

### 布局

- **响应式设计**: 支持 PC 和移动端
- **Flexbox**: 表单行使用 flex 布局
- **标签页**: 选项维护使用标签页切换

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

## 开发规范

### 代码风格
- 使用 2 个空格作为缩进
- 变量命名使用 `camelCase`
- 函数和类使用 `snake_case`
- 所有表和列需要添加 `__tablename__` 注释和字段说明注释

### 提交规范
- 使用 rebase 而不是 merge
- commit message 用英文
- 一个 commit 做一件事
- 格式：`type: subject`

### 错误处理
- 充分的错误处理，不吞掉异常
- 使用 logger 记录错误
- AJAX 返回 JSON 格式错误信息

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

### 4. CSRF 保护
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

## 已知问题

### 已修复
- ✅ 价格表达式计算（AST 节点类型问题）
- ✅ 日期类型转换（字符串转 date 对象）
- ✅ 车厢项字段名（set_id vs carriage_set_id）
- ✅ 编辑按钮样式不统一
- ✅ 标签页布局问题
- ✅ 重新初始化数据库按钮位置

### 待优化
- 添加分页功能
- 添加搜索功能
- 考虑模块化（Blueprints）

## 版本历史

- **v0.1.0**: 初始版本，核心功能
- **v0.2.0**: 添加 AJAX 表单提交
- **v0.3.0**: 添加行内编辑
- **v0.4.0**: 样式优化和bug修复
