# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
火车模型管理系统 - 用于管理火车模型藏品、统计和展示的 Web 应用。支持四种模型类型：机车模型、车厢模型、动车组模型、先头车模型。

## 当前状态
项目处于早期开发阶段，已完成核心功能的开发。数据库初始化已完成，包含 44 种车厢型号。

## 技术栈
- Python 3.x
- Flask
- SQLAlchemy
- MySQL / SQLite
- Jinja2（Flask 内置模板引擎）
- HTML5 + JavaScript（前端无需构建工具）

## 已确认的设计方案
单体 Flask 应用架构，所有路由集中在 `app.py` 中管理。如后期代码增多，可平滑过渡到模块化结构。

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

## 核心数据模型（基于需求文档）

### 四种火车模型类型

1. **机车模型** (Locomotive):
   - 包含系列、动力类型、车型、品牌、机务段、挂牌、颜色、比例、机车号、编号、芯片接口、芯片型号、价格、总价、货号、购买日期、购买商家

2. **车厢模型** (Carriage):
   - 支持套装录入
   - 包含品牌、系列、车型、类型（客车/货车/工程车）、车辆号、车辆段、车次、挂牌、货号、颜色、灯光、比例、总价、购买日期、购买商家
   - 类型字段固定为三种：客车、货车、工程车

3. **动车组模型** (Trainset):
   - 包含系列、动力类型、车型、品牌、动车段、挂牌、颜色、比例、编组、动车号、编号、头车灯、室内灯、芯片接口、芯片型号、价格、总价、货号、购买日期、购买商家

4. **先头车模型** (Locomotive Head):
   - 包含车型、品牌、动车段、特涂、比例、头车灯、室内灯、价格、总价、货号、购买日期、购买商家

### 参考数据表（10 个）

| 表名 | 字段 | 说明 |
|-----|------|------|
| power_type | id, name | 动力类型（蒸汽、电力、内燃、双源）|
| brand | id, name | 品牌（百万城、长鸣等）- 所有模型共享|
| chip_interface | id, name | 芯片接口（NEXT18、MTC21等）- 机车和动车组共享|
| chip_model | id, name | 芯片型号（动芯5323、MS350P22等）- 机车和动车组共享|
| merchant | id, name | 洭买商家 - 所有模型共享|
| depot | id, name | 车辆段/机务段 - 机车、车厢、动车组共享|
| locomotive_series | id, name | 机车系列（东风、韶山等）|
| locomotive_model | id, name, series_id, power_type_id | 机车型号，关联系列和类型 |
| carriage_series | id, name | 车厢系列（25G、25B等）|
| carriage_model | id, name, series_id, type | 车厢型号，关联系列和类型（客车/货车/工程车）|
| trainset_series | id, name | 动车组系列（ICE、TGV、新干线等）|
| trainset_model | id, name, series_id, power_type_id | 动车组车型，关联系列和类型|

### 核心业务逻辑

#### 自动填充规则（通过 JavaScript 实现）
- 选择机车车型 → 自动填充机车系列和机车动力类型
- 选择车厢车型 → 自动填充车厢系列和类型
- 选择动车组车型 → 自动填充动车组系列和动力类型

#### 唯一性验证（提交时验证，后端处理）
- 同一比例内唯一：
  - 机车号：4-12 位数字，前导 0
  - 编号：1-4 位数字，无前导 0
  - 动车号：3-12 位数字，前导 0
- 重复时返回错误并标红

#### 价格计算
- 后端使用 Python 计算价格表达式
- 只允许数字、+、-、*、/、()
- 前端显示表达式，后端计算总价并填充

#### 车厢套装
- 前端动态表单，支持一套多车厢录入
- 每个车厢独立：车型、车辆号、颜色、灯光

#### 级联删除检查
- 删除系列/车型前检查是否被使用
- 防止删除正在使用的数据

### 页面规划

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
   - 动车组信息：动车组系列、动车组车型

### 价格表达式
后端使用 Python eval 配合正则表达式进行安全计算，只允许数字和基本算术运算符。
示例：`288+538` 或 `288*2 + 500`

### 数据库初始化
预置数据包含：
- 38 个机车型号（东风、韶山、和谐电、复兴内）
- 34 个动车组车型（ICE、TGV、新干线等）
- 44 个车厢型号（22、25B、25G、25T 等，分客车/货车/工程车三类）

### 开发注意事项
- 当前处于开发调试阶段，数据库可随时删除重建
- 所有表和列需要添加 `__tablename__` 注释和字段说明注释
- 车厢套装录入需要支持动态添加车厢

## 参考文档                                                                                                                                                                                                                                  
-项目根目录包含以下需求文档：
- `系统描述.txt` - 完整的功能需求
- `数据库初始化要求.txt` - 预置数据清单
 

### 文件结构
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
│       └── app.js
├── templates/         # Jinja2 模板
│   ├── base.html      # 基础模板
│   ├── index.html     # 汇总页面
│   ├── locomotive.html
│   ├── carriage.html
│   ├── trainset.html
│   ├── locomotive_head.html
│   └── options.html   # 选项维护（含标签页）
```
