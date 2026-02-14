# 火车模型管理系统设计文档

**日期**: 2025-02-14
**状态**: 已批准

## 概述

火车模型管理系统是一个用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型。

## 架构决策

### 技术栈

- **后端**: Python + Flask（单体应用）
- **数据库**: 默认 SQLite，通过配置文件切换到 MySQL
- **前端**: 纯 HTML5 + JavaScript（无需构建工具）
- **ORM**: SQLAlchemy
- **模板引擎**: Jinja2（Flask 内置）

### 架构模式

采用单体 Flask 应用架构（`app.py`），所有路由集中管理。如后期代码增多，可平滑过渡到模块化结构。

## 数据库设计

### 参考数据表（10 个）

#### 跨模型共享的表

| 表名 | 字段 | 说明 |
|-----|------|------|
| power_type | id, name | 动力类型（蒸汽、电力、内燃、双源）|
| brand | id, name | 品牌（百万城、长鸣等）|
| chip_interface | id, name | 芯片接口（NEXT18、MTC21等）|
| chip_model | id, name | 芯片型号（动芯5323、MS350P22等）|
| merchant | id, name | 购买商家 |
| depot | id, name | 车辆段/机务段（京局京段、上局沪段等）|

#### 模型专用表

| 表名 | 字段 | 说明 |
|-----|------|------|
| locomotive_series | id, name | 机车系列（东风、韶山等）|
| locomotive_model | id, name, series_id, power_type_id | 机车型号，关联系列和类型 |
| carriage_series | id, name | 车厢系列（25G、25B等）|
| carriage_model | id, name, series_id, type | 车厢型号，关联系列和类型（客车/货车/工程车）|
| trainset_series | id, name | 动车组系列（ICE、TGV、新干线等）|
| trainset_model | id, name, series_id, power_type_id | 动车组车型，关联系列和类型 |

### 核心数据表

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
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

#### carriage_item（车厢套装子表）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| set_id | Integer | FK | 关联 carriage_set |
| model_id | Integer | FK | 关联 carriage_model |
| car_number | String(10) | 唯一性(同比例) | 车辆号 |
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
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

#### locomotive_head（先头车模型）

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| id | Integer | PK | 主键 |
| model_id | Integer | FK | 关联 trainset_model |
| brand_id | Integer | FK | 关联 brand |
| depot_id | Integer | FK | 关联 depot（动车段）|
| special_color | String(32) | | 特涂 |
| scale | String(2) | | 比例（HO/N）|
| head_light | Boolean | | 头车灯（有/无）|
| interior_light | String(50) | | 室内灯 |
| price | String(50) | | 价格表达式 |
| total_price | Float | | 总价（自动计算）|
| item_number | String(50) | | 货号 |
| purchase_date | Date | | 购买日期 |
| merchant_id | Integer | FK | 关联 merchant |

### 数据库注释要求

所有表和列都需要添加 `__tablename__` 注释和字段说明注释。

## 后端设计

### 文件结构

```
TrainModelManager/
├── app.py              # Flask 主应用
├── models.py           # SQLAlchemy 模型定义
├── config.py           # 配置文件
├── init_db.py         # 数据库初始化脚本
├── requirements.txt    # Python 依赖
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── locomotive.html
    ├── carriage.html
    ├── trainset.html
    ├── locomotive_head.html
    └── options.html
```

### 路由设计

| 路由 | 方法 | 功能 |
|-----|------|------|
| / | GET | 汇总统计页面 |
| /locomotive | GET, POST | 机车模型列表和添加 |
| /locomotive/delete/<id> | POST | 删除机车模型 |
| /carriage | GET, POST | 车厢套装列表和添加 |
| /carriage/delete/<id> | POST | 删除车厢套装 |
| /trainset | GET, POST | 动车组列表和添加 |
| /trainset/delete/<id> | POST | 删除动车组 |
| /locomotive-head | GET, POST | 先头车列表和添加 |
| /locomotive-head/delete/<id> | POST | 删除先头车 |
| /api/auto-fill/<type>/<model_id> | GET | 自动填充 API（type: locomotive/carriage/trainset）|
| /api/check-duplicate/<table>/<field>/<value>/<scale> | GET | 唯一性检查 API |
| /options | GET, POST | 选项维护页面（标签页）|

### 价格表达式计算

后端使用 Python 计算价格表达式，使用正则表达式进行安全验证，只允许数字、+、-、*、/、()。

### 唯一性验证

在同一比例内检查唯一性：
- `locomotive`: locomotive_number, decoder_number
- `trainset`: trainset_number, decoder_number
- `carriage_item`: car_number（通过 scale 关联到 carriage_set）

## 前端设计

### 页面布局

所有页面继承 `base.html`，包含导航栏：
- 首页（汇总统计）
- 机车模型
- 车厢模型
- 动车组模型
- 先头车模型
- 选项维护

### JavaScript 功能

1. **自动填充**：
   - 监听车型 select 变化
   - 调用 `/api/auto-fill/<type>/<model_id>` 获取系列和类型
   - 填充对应的 select 和 input

2. **动态表单**（车厢套装）：
   - 点击"添加车厢"按钮动态添加一行
   - 每行包含：车型、车辆号、颜色、灯光、删除按钮

3. **表单验证**：
   - 提交前检查必填字段
   - 显示错误提示

4. **唯一性提示**：
   - 如果后端返回重复错误，标红对应字段

### 选项维护页面

使用标签页切换不同选项：
- 动力类型
- 机车系列
- 机车型号
- 车厢系列
- 车厢型号
- 动车组系列
- 动车组车型
- 品牌
- 商家
- 芯片接口
- 芯片型号
- 车辆段/机务段

## 数据初始化

### 预置数据清单

根据 `数据库初始化要求.txt`，需要在 `init_db.py` 中插入以下预置数据：

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
2. 当前处于开发调试阶段，数据库可随时删除重建
3. 车厢套装录入需要支持动态添加车厢
4. 价格表达式计算需要安全验证
5. 唯一性验证只在同一比例内进行
