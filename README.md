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
- **统计汇总**：展示各类型和维度的花费统计
- **选项维护**：集中管理所有下拉选项（品牌、商家、系列、车型等）

### 用户体验优化
- **AJAX 表单提交**：添加模型时不刷新页面，验证失败保留已填写内容
- **行内编辑**：选项维护页面支持行内编辑，无需跳转
- **错误提示**：输入框标签显示红色错误气泡
- **响应式设计**：支持 PC 和移动端

## 技术栈

### 后端
- **Python 3.10+** - 主要编程语言
- **Flask 3.0+** - Web 框架
- **SQLAlchemy 3.1+** - ORM 框架
- **SQLite** - 开发环境数据库
- **MySQL** - 生产环境数据库（可选）
- **Jinja2** - 模板引擎（Flask 内置）
- **AST** - Abstract Syntax Tree 用于安全的价格表达式计算

### 前端
- **HTML5** - 页面结构
- **CSS3** - 样式（无预处理器）
- **JavaScript** - 交互逻辑（无构建工具，如 Webpack/Vite）

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

## 数据库配置

### 默认配置（SQLite）
无需额外配置，直接使用即可。

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
├── app.py                    # Flask 主应用
├── models.py                 # SQLAlchemy 数据模型定义
├── config.py                 # 配置文件
├── init_db.py               # 数据库初始化脚本
├── requirements.txt          # Python 依赖
├── static/                  # 静态资源
│   ├── css/
│   │   └── style.css       # 全局样式
│   └── js/
│       ├── app.js           # 主页 JavaScript
│       └── options.js      # 选项维护页面 JavaScript
├── templates/              # Jinja2 模板
│   ├── base.html           # 基础模板
│   ├── index.html          # 汇总页面
│   ├── locomotive.html     # 机车模型
│   ├── locomotive_edit.html
│   ├── carriage.html       # 车厢模型
│   ├── carriage_edit.html
│   ├── trainset.html       # 动车组模型
│   ├── trainset_edit.html
│   ├── locomotive_head.html # 先头车模型
│   ├── locomotive_head_edit.html
│   └── options.html       # 选项维护页面
├── docs/                  # 文档目录
│   ├── architecture.md     # 架构文档
│   └── plans/            # 设计和实现计划
├── 系统描述.txt           # 功能需求文档
├── 数据库初始化要求.txt    # 预置数据清单
└── CLAUDE.md             # AI 助手指导文档
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
| power_type | 动力类型 |
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
  "locomotive": {
    "count": 10,
    "total": 15800.0,
    "by_scale": {"HO": 6, "N": 4},
    "by_brand": {"百万城": 7, "长鸣": 3}
  }
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
- 编辑时排除当前记录

### 价格表达式验证

- 只允许数字和基本运算符：`+ - * / ( )`
- 示例：`288+538`、`288*2 + 500`

## 开发规范

### 代码风格
- 使用 2 个空格作为缩进
- 变量命名使用 `camelCase`
- 函数和类命名使用 `snake_case`
- 常量使用 `UPPER_CASE`

### Git 提交规范
- 使用 rebase 而不是 merge
- Commit message 用英文
- 格式：`type: subject`
- 类型：`feat`（新功能）、`fix`（修复）、`style`（样式）、`refactor`（重构）、`docs`（文档）

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

## 文档

- [架构文档](docs/architecture.md) - 详细的系统架构说明
- [CLAUDE.md](CLAUDE.md) - AI 助手指导文档
- [系统描述.txt](系统描述.txt) - 功能需求文档
- [数据库初始化要求.txt](数据库初始化要求.txt) - 预置数据清单

## 版本历史

- **v0.4.0**
  - 添加 AJAX 表单提交
  - 添加行内编辑功能
  - 优化样式和布局
  - 修复价格计算和日期处理问题

- **v0.3.0**
  - 添加系列筛选车型功能
  - 优化选项维护页面布局

- **v0.2.0**
  - 添加自动填充功能
  - 添加唯一性验证

- **v0.1.0**
  - 初始版本
  - 核心 CRUD 功能

## 许可证

[待定]

## 联系方式

[待定]
