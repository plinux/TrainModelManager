# 火车模型管理系统

用于管理火车模型藏品、统计和展示的 Web 应用。

## 功能特性

### 核心功能
- **四种模型类型支持**：机车模型、车厢模型、动车组模型、先头车模型
- **CRUD 操作**：完整的增删改查功能
- **自动填充**：选择车型后自动填充系列和类型
- **系列筛选**：选择系列后自动过滤对应车型
- **唯一性验证**：同一比例内的机车号、编号、动车号唯一性检查
- **价格表达式计算**：支持 "288+538" 形式的价格自动计算
- **车厢套装管理**：支持动态添加/删除车厢项
- **统计汇总**：展示各类型和维度的花费统计（支持表格和饼图）
- **信息维护**：集中管理所有下拉选项（品牌、商家、系列、车型等）

### 数据导入导出
- **多模式导出**：
  - 模型数据：机车、车厢、动车组、先头车等模型记录
  - 系统信息：品牌、系列、车型等选项数据
  - 全部数据：导出系统中的所有数据
- **智能导入**：
  - 自动识别 Excel 工作表类型
  - 冲突检测：预检查导入数据是否违反唯一性约束
  - 冲突处理：可选择跳过冲突数据或覆盖现有数据
- **自定义导入向导**（v0.7.0 新增）：
  - 5 步向导流程：选择文件 → 管理模板 → 配置映射 → 预览确认 → 执行导入
  - 导入模板管理：保存常用映射配置，支持加载、更新、重命名、删除
  - 灵活的列映射：Excel 列与系统表字段自由映射
  - 车厢合并单元格检测：智能识别车厢套装的合并单元格结构
  - 冲突预览：导入前预览所有数据冲突
- **导出格式**：Excel 文件，标题行加粗，文件名包含日期时间

### 用户体验优化
- **快速复制**：模型列表页支持复制按钮，快速填充表单
- **表格排序筛选**：点击列头排序，下拉框筛选
- **AJAX 表单提交**：添加模型时不刷新页面，验证失败保留已填写内容
- **行内编辑**：信息维护页面支持行内编辑，无需跳转
- **错误提示**：输入框标签显示红色错误气泡
- **响应式设计**：支持 PC 和移动端

## 技术栈

### 后端
- **Python 3.10+** - 主要编程语言
- **Flask 3.0+** - Web 框架（Blueprint 模块化架构）
- **SQLAlchemy 3.1+** - ORM 框架
- **SQLite** - 开发环境数据库
- **MySQL** - 生产环境数据库（可选）
- **Jinja2** - 模板引擎（Flask 内置）
- **openpyxl** - Excel 文件处理
- **AST** - Abstract Syntax Tree 用于安全的价格表达式计算

### 前端
- **HTML5** - 页面结构
- **CSS3** - 样式（使用 CSS 变量，无预处理器）
- **JavaScript** - 交互逻辑（模块化设计，无构建工具）
- **Chart.js 4.x** - 图表展示（CDN 引入）

## 快速开始

### 环境要求
- Python 3.10 或更高版本
- pip（Python 包管理器）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd TrainModelManager
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv myenv
   ```

3. **激活虚拟环境**
   ```bash
   # Linux/macOS
   source myenv/bin/activate

   # Windows
   myenv\Scripts\activate
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **初始化数据库**
   ```bash
   python init_db.py
   ```

6. **启动应用**
   ```bash
   python app.py
   ```

7. **访问系统**
   ```
   浏览器打开：http://localhost:5000
   ```

### 退出虚拟环境
```bash
deactivate
```

## 数据库配置

### 默认配置（SQLite）
无需额外配置，直接使用即可。数据库文件为 `train_model.db`。

### MySQL 配置

要使用 MySQL 数据库，设置环境变量：

```bash
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=train_model_manager
```

## 项目结构

```
TrainModelManager/
├── app.py                    # Flask 主应用（应用工厂模式）
├── models.py                 # SQLAlchemy 数据模型定义
├── config.py                 # 配置文件
├── init_db.py               # 数据库初始化脚本
├── requirements.txt          # Python 依赖
├── routes/                  # Blueprint 路由模块
│   ├── main.py              # 首页和统计
│   ├── locomotive.py        # 机车模型
│   ├── carriage.py          # 车厢模型
│   ├── trainset.py          # 动车组模型
│   ├── locomotive_head.py   # 先头车模型
│   ├── options.py           # 信息维护
│   └── api.py               # API 端点（导入导出、自动填充）
├── utils/                   # 公共辅助函数
│   ├── helpers.py           # 通用辅助函数
│   ├── validators.py        # 验证函数
│   ├── price_calculator.py  # 价格计算
│   └── system_tables.py     # 系统表配置（自定义导入）
├── static/                  # 静态资源
│   ├── css/
│   │   └── style.css       # 全局样式
│   └── js/
│       ├── utils.js         # 核心 JS 模块
│       ├── app.js           # 页面初始化
│       ├── options.js       # 信息维护页面
│       ├── system.js        # 系统维护页面
│       └── custom-import.js # 自定义导入向导
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础模板
│   ├── index.html          # 汇总页面
│   ├── locomotive.html     # 机车模型列表
│   ├── locomotive_edit.html
│   ├── carriage.html       # 车厢模型列表
│   ├── carriage_edit.html
│   ├── trainset.html       # 动车组模型列表
│   ├── trainset_edit.html
│   ├── locomotive_head.html # 先头车模型列表
│   ├── locomotive_head_edit.html
│   ├── options.html        # 信息维护页面
│   ├── system.html         # 系统维护页面
│   └── macros/             # Jinja2 宏
├── tests/                  # 测试文件
│   ├── conftest.py         # 测试配置和 fixtures
│   ├── test_api.py         # API 测试
│   ├── test_crud.py        # CRUD 测试
│   ├── test_integration.py # 集成测试
│   ├── test_labels.py      # 标签测试
│   ├── test_models.py      # 模型测试
│   ├── test_options.py     # 选项测试
│   ├── test_routes.py      # 路由测试
│   └── test_validation.py  # 验证测试
└── docs/                   # 文档目录
    ├── design/             # 设计文档
    │   ├── Train-Model-Manager-Design.md
    │   └── Train-Model-Manager-Implementation.md
    └── plans/              # 需求文档
        ├── SystemDescription.txt
        └── DatabaseInitDescription.txt
```

## 数据模型

### 核心实体

| 表名 | 说明 |
|-----|------|
| locomotive | 机车模型 |
| locomotive_model | 机车型号 |
| locomotive_series | 机车系列 |
| carriage_set | 车厢套装主表 |
| carriage_item | 车厢套装子表 |
| carriage_model | 车厢型号 |
| carriage_series | 车厢系列 |
| trainset | 动车组模型 |
| trainset_model | 动车组车型 |
| trainset_series | 动车组系列 |
| locomotive_head | 先头车模型 |
| power_type | 动力 |
| brand | 品牌 |
| depot | 车辆段/机务段 |
| chip_interface | 芯片接口 |
| chip_model | 芯片型号 |
| merchant | 购买商家 |

## API 文档

### 统计 API

**GET /api/statistics**

获取汇总统计数据。

**响应示例**：
```json
{
  "type_stats": {...},
  "scale_stats": {...},
  "brand_stats": {...},
  "merchant_stats": {...}
}
```

### 自动填充 API

**GET /api/auto-fill/locomotive/<int:model_id>**

获取机车系列的关联数据。

**响应示例**：
```json
{
  "series_id": 3,
  "power_type_id": 2
}
```

**GET /api/auto-fill/trainset/<int:model_id>**

获取动车组系列的关联数据。

### 添加模型 API

**POST /api/locomotive/add**

AJAX 添加机车模型。

**请求体**：
```json
{
  "model_id": 5,
  "brand_id": 2,
  "scale": "HO",
  "locomotive_number": "0001",
  "decoder_number": "1",
  "price": "288+538",
  ...
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "机车模型添加成功"
}
```

**失败响应**：
```json
{
  "success": false,
  "errors": [
    {"field": "locomotive_number", "message": "机车号格式错误：应为4-12位数字，允许前导0"}
  ]
}
```

### Excel 导入导出 API

**GET /api/export/excel?mode=\<mode\>**

导出数据到 Excel 文件。

| mode | 说明 |
|------|------|
| models | 仅导出模型数据（机车、车厢、动车组、先头车）|
| system | 仅导出系统信息（品牌、系列、车型等）|
| all | 导出全部数据 |

**POST /api/import/excel**

从 Excel 导入数据。支持预检查和冲突处理。

**请求参数**（FormData）：
- `file`: Excel 文件
- `mode`: 导入模式
  - `preview`: 预检查模式，返回冲突信息
  - `skip`: 跳过冲突数据
  - `overwrite`: 覆盖现有数据

**支持的工作表**：
- 模型数据：机车、车厢、动车组、先头车
- 系统信息：动力、品牌、机务段/车辆段、商家、动力类型、芯片接口、芯片型号、机车系列、车厢系列、动车组系列、机车车型、车厢车型、动车组车型

### 自定义导入 API（v0.7.0 新增）

**GET /api/import-templates**

获取所有导入模板列表。

**POST /api/import-templates**

创建新的导入模板。

**请求体**：
```json
{
  "name": "我的机车导入模板",
  "target_table": "locomotive",
  "column_mapping": {
    "A": "model_id",
    "B": "brand_id",
    "C": "scale"
  }
}
```

**GET /api/import-templates/\<id\>**

获取指定模板详情。

**PUT /api/import-templates/\<id\>**

更新模板配置。

**DELETE /api/import-templates/\<id\>**

删除模板。

**GET /api/custom-import/tables**

获取可导入的系统表配置（表名、字段、唯一键等）。

**响应示例**：
```json
{
  "tables": {
    "locomotive": {
      "display_name": "机车",
      "fields": [...],
      "unique_keys": [...],
      "foreign_keys": [...]
    },
    ...
  }
}
```

**POST /api/custom-import/parse**

解析 Excel 文件，获取工作表和列信息。

**请求参数**（FormData）：
- `file`: Excel 文件

**响应示例**：
```json
{
  "sheets": [
    {
      "name": "Sheet1",
      "columns": ["A", "B", "C", "D"],
      "headers": ["车型", "品牌", "比例", "价格"],
      "row_count": 100
    }
  ]
}
```

**POST /api/custom-import/preview**

预览导入数据，包含冲突检测。

**请求体**：
```json
{
  "file_path": "/tmp/xxx.xlsx",
  "sheet_name": "Sheet1",
  "target_table": "locomotive",
  "column_mapping": {"A": "model_id", "B": "brand_id"},
  "conflict_mode": "skip"
}
```

**响应示例**：
```json
{
  "total_rows": 100,
  "valid_rows": 95,
  "conflict_rows": 5,
  "conflicts": [
    {"row": 3, "message": "机车号已存在"}
  ],
  "preview_data": [...]
}
```

**POST /api/custom-import/execute**

执行导入操作。

**请求体**：
```json
{
  "file_path": "/tmp/xxx.xlsx",
  "sheet_name": "Sheet1",
  "target_table": "locomotive",
  "column_mapping": {"A": "model_id", "B": "brand_id"},
  "conflict_mode": "skip"
}
```

**响应示例**：
```json
{
  "success": true,
  "imported_count": 95,
  "skipped_count": 5,
  "message": "导入完成：成功 95 条，跳过 5 条"
}
```

## 验证规则

### 数字格式验证

| 字段 | 格式 | 说明 |
|-----|------|------|
| 机车号 | 4-12 位数字 | 允许前导 0 |
| 编号 | 1-4 位数字 | 无前导 0 |
| 动车号 | 3-12 位数字 | 允许前导 0 |
| 车辆号 | 3-10 位数字 | 无前导 0 |

### 唯一性验证

- 同一比例内，机车号、编号、动车号必须唯一
- 品牌名称必须唯一
- 编辑时排除当前记录

### 价格表达式验证

- 只允许数字和基本运算符：`+ - * / ( )`
- 示例：`288+538`、`288*2 + 500`

## 测试

### 运行测试

```bash
# 激活虚拟环境后执行
pytest                           # 运行所有测试
pytest -v                        # 详细输出
pytest tests/test_api.py         # 运行特定测试文件
pytest -k "locomotive"           # 运行名称包含 locomotive 的测试
```

### 测试数据库隔离

测试使用独立的数据库配置（TestConfig），不会影响开发数据库。

## 开发规范

### 代码风格
- 使用 2 个空格作为缩进
- 变量命名使用 `camelCase`
- 函数和类命名使用 `snake_case`
- 常量使用 `UPPER_CASE`

### Git 提交规范
- 使用 rebase 而不是 merge
- Commit message 用英文
- 格式：`[Type] subject`
- 类型：`Feature`（新功能）、`Bugfix`（修复）、`Style`（样式）、`Refactor`（重构）、`Docs`（文档）

### 错误处理
- 充分的错误处理，不吞掉异常
- 使用 logger 记录错误信息
- 用户友好的错误提示

## 依赖组件

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.0
cryptography==41.0.7
openpyxl==3.1.5
pytest==8.0.0
```

## 部署建议

### 开发环境
```bash
python app.py
```

### 生产环境

推荐使用 Gunicorn 作为 WSGI 服务器：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 常见问题

### 1. 数据库初始化失败
确保已删除旧数据库文件（SQLite）或已正确配置 MySQL 连接。

### 2. 价格计算错误
确保价格表达式格式正确，只包含数字和基本运算符。

### 3. 页面刷新数据丢失
添加模型时使用 AJAX 提交，数据不会丢失。

### 4. 导入数据冲突
导入时系统会检测唯一性约束冲突，可选择跳过冲突数据或覆盖现有数据。

### 5. 测试失败
确保使用独立的测试数据库配置，测试不会影响开发数据。

## 文档

- [设计文档](docs/design/Train-Model-Manager-Design.md) - 系统架构和整体设计
- [实现计划](docs/design/Train-Model-Manager-Implementation.md) - 详细实现计划
- [CLAUDE.md](CLAUDE.md) - AI 助手指导文档
- [系统描述](docs/plans/SystemDescription.txt) - 功能需求文档
- [数据库初始化要求](docs/plans/DatabaseInitDescription.txt) - 预置数据清单

## 版本历史

- **v0.7.0**
  - 自定义 Excel 导入向导（5 步向导流程）
  - 导入模板管理（保存、加载、更新、重命名、删除）
  - 灵活的列映射配置
  - 车厢合并单元格检测
  - 导入预览和冲突检测
  - ImportTemplate 数据模型

- **v0.5.0**
  - 添加模型列表复制按钮功能
  - Excel 导入冲突检测和处理（预检查、跳过、覆盖）
  - 多模式导出（模型数据、系统信息、全部）
  - 智能导入（自动识别工作表类型）
  - 导出文件标题行加粗
  - "选项维护"更名为"信息维护"
  - 修复测试数据库隔离问题

- **v0.4.0**
  - 添加 AJAX 表单提交
  - 添加行内编辑功能
  - 优化样式和布局
  - 修复价格计算和日期处理问题

- **v0.3.0**
  - 添加系列筛选车型功能
  - 优化信息维护页面布局
  - Blueprint 模块化重构

- **v0.2.0**
  - 添加自动填充功能
  - 添加唯一性验证
  - 首页多维度统计

- **v0.1.0**
  - 初始版本
  - 核心 CRUD 功能

## 许可证

[Apache License 2.0](LICENSE)

## 联系方式

penglixun@gmail.com
