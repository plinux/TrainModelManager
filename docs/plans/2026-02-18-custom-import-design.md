# 自定义导入功能设计文档

## 概述

为火车模型管理系统添加自定义 Excel 导入功能，允许用户将自己的 Excel 文件格式映射到系统数据表，无需按照系统固定格式准备数据。

## 业务场景

用户已有自己的 Excel 表格维护模型数据，修改成系统导入格式比较困难。通过引导式配置，让用户在界面上选择 Excel 文件和系统字段的对应关系，然后根据这个对应关系导入数据。

## 功能设计

### 整体架构

#### 前端架构

**新增文件：**
- `static/js/custom-import.js` - 自定义导入向导模块
- 模态框模板内嵌在 `templates/system.html` 或新建组件文件

**向导步骤流程：**

```
有模板时（5 步骤）：
[1.选择文件] → [2.选择模板] → [3.Sheet映射] → [4.列映射] → [5.确认导入]

无模板时（4 步骤，首次使用）：
[1.选择文件] → [2.Sheet映射] → [3.列映射] → [4.确认导入]
```

步骤指示器动态显示当前步骤，选择文件后检查模板数量决定是否显示"选择模板"步骤。

#### 后端架构

**新增 API 路由：**

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/import-templates` | GET | 获取所有模板列表 |
| `/api/import-templates` | POST | 创建新模板 |
| `/api/import-templates/<id>` | PUT | 更新模板（重命名/内容） |
| `/api/import-templates/<id>` | DELETE | 删除模板 |
| `/api/custom-import/parse` | POST | 解析 Excel 文件，返回 Sheet 和列名 |
| `/api/custom-import/preview` | POST | 预检查单表数据，返回冲突列表 |
| `/api/custom-import/execute` | POST | 执行导入 |

### 各步骤详细设计

#### 步骤 1：选择文件

- 支持拖拽或点击选择文件
- 支持 .xlsx, .xls 格式
- 显示已选择的文件名

#### 步骤 2：选择模板（仅当有模板时显示）

- 选项："不使用模板，手动配置" 或 "使用模板"
- 模板列表显示：模板名称、重命名按钮、删除按钮
- 最后使用的模板标记为默认（用图标标识）

#### 步骤 3：Sheet 映射

**交互设计：**
- 一开始显示一行空白的下拉菜单对
- 左侧：用户的 Sheet 列表（已选的从列表移除）
- 右侧：系统数据表列表（已选的从列表移除）
- 选择一对映射后自动添加新行
- 每行右侧有 ✕ 按钮可删除
- 当所有 Sheet 都已配置，不再添加新行
- 显示进度："您的文件包含 X 个工作表，已配置 Y 个"

**系统数据表分组：**

系统信息（建议先导入）：
- 品牌、配属（hover 提示"即机务段/车辆段/动车段"）、商家、动力类型
- 芯片接口、芯片型号
- 机车系列、机车车型、车厢系列、车厢车型、动车组系列、动车组车型

模型数据（依赖系统信息）：
- 机车模型、车厢模型、动车组模型、先头车模型

#### 步骤 4：列映射（逐表配置）

**基本交互：**
- 按 Sheet 映射顺序，依次处理每张表
- 显示处理进度条
- 动态添加行列映射（与 Sheet 映射相同交互）
- 点击"下一步"时自动预检查
- 显示预检查结果（成功/警告/错误）
- 有冲突时必须选择处理方式：跳过或覆盖

**车厢模型特殊处理：**
- 套装识别方式选择：
  - 按合并单元格识别套装（推荐）
  - 每行作为一个独立套装
- 未合并公共字段取值方式：第一行（默认）或最后一行
- 检测并报告合并单元格异常

#### 步骤 5：确认导入

- 显示导入配置预览（各表数据量、冲突处理方式）
- 保存模板选项：
  - 不保存
  - 保存为新模板（输入名称）
  - 更新现有模板（下拉选择）
- 导入完成后显示结果统计

### 断点续传与取消保存

**取消时的保存提醒：**

当用户在任何步骤点击取消/关闭时：
1. 检查是否有已配置的内容
2. 如有，弹出保存提醒对话框
3. 选项："不保存，直接退出" 或 "保存并退出"
4. 保存时记录当前步骤，下次从断点继续

**断点恢复交互：**
- 加载模板后从上次中断的步骤继续
- 用户可以点击"上一步"修改之前的所有配置（支持回退）

### 模板管理功能

| 功能 | 说明 |
|-----|------|
| 保存 | 导入完成后可选择保存为新模板或更新现有模板 |
| 加载 | 从模板列表选择加载，自动填充所有配置 |
| 删除 | 删除不需要的模板 |
| 重命名 | 修改模板名称 |
| 默认模板 | 最后使用的模板自动成为默认模板 |

## 数据模型

### ImportTemplate 表

```python
class ImportTemplate(db.Model):
    """自定义导入模板"""
    __tablename__ = 'import_template'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, comment='模板名称')
    config = db.Column(JSON, nullable=False, comment='映射配置')
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### config 字段结构

```json
{
  "sheet_mappings": [
    {"sheet_name": "品牌列表", "table_name": "brand"},
    {"sheet_name": "机车", "table_name": "locomotive"}
  ],
  "column_mappings": {
    "brand": {
      "columns": [
        {"source": "品牌名称", "target": "name", "required": true},
        {"source": "官网", "target": "search_url", "required": false}
      ],
      "conflict_mode": "overwrite"
    },
    "locomotive": {
      "columns": [
        {"source": "牌子", "target": "brand_id", "required": true},
        {"source": "缩放比例", "target": "scale", "required": true}
      ],
      "conflict_mode": "skip"
    },
    "carriage": {
      "columns": [],
      "conflict_mode": "skip",
      "set_detection": "merged_cells",
      "unmerged_value_source": "first"
    }
  },
  "last_step": 4,
  "file_info": {
    "original_filename": "我的模型数据.xlsx"
  }
}
```

## 系统表字段定义

用于前端显示和验证的配置：

```python
SYSTEM_TABLES = {
    # 系统信息表
    'brand': {
        'display_name': '品牌',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True},
            {'name': 'search_url', 'display': '搜索地址', 'required': False}
        ]
    },
    'depot': {
        'display_name': '配属',
        'tooltip': '即机务段/车辆段/动车段',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'merchant': {
        'display_name': '商家',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'power_type': {
        'display_name': '动力类型',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'chip_interface': {
        'display_name': '芯片接口',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'chip_model': {
        'display_name': '芯片型号',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'locomotive_series': {
        'display_name': '机车系列',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'carriage_series': {
        'display_name': '车厢系列',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'trainset_series': {
        'display_name': '动车组系列',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True, 'unique': True}
        ]
    },
    'locomotive_model': {
        'display_name': '机车车型',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True},
            {'name': 'series_id', 'display': '系列', 'required': True, 'ref': 'locomotive_series'},
            {'name': 'power_type_id', 'display': '动力类型', 'required': True, 'ref': 'power_type'}
        ]
    },
    'carriage_model': {
        'display_name': '车厢车型',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True},
            {'name': 'series_id', 'display': '系列', 'required': True, 'ref': 'carriage_series'},
            {'name': 'type', 'display': '类型', 'required': True}
        ]
    },
    'trainset_model': {
        'display_name': '动车组车型',
        'category': 'system',
        'fields': [
            {'name': 'name', 'display': '名称', 'required': True},
            {'name': 'series_id', 'display': '系列', 'required': True, 'ref': 'trainset_series'},
            {'name': 'power_type_id', 'display': '动力类型', 'required': True, 'ref': 'power_type'}
        ]
    },

    # 模型数据表
    'locomotive': {
        'display_name': '机车模型',
        'category': 'model',
        'fields': [
            {'name': 'brand_id', 'display': '品牌', 'required': True, 'ref': 'brand'},
            {'name': 'scale', 'display': '比例', 'required': True},
            {'name': 'series_id', 'display': '系列', 'required': False, 'ref': 'locomotive_series'},
            {'name': 'power_type_id', 'display': '动力', 'required': False, 'ref': 'power_type'},
            {'name': 'model_id', 'display': '车型', 'required': False, 'ref': 'locomotive_model'},
            {'name': 'depot_id', 'display': '配属', 'required': False, 'ref': 'depot'},
            {'name': 'plaque', 'display': '挂牌', 'required': False},
            {'name': 'color', 'display': '颜色', 'required': False},
            {'name': 'locomotive_number', 'display': '机车号', 'required': False, 'unique_in_scale': True},
            {'name': 'decoder_number', 'display': '编号', 'required': False, 'unique_in_scale': True},
            {'name': 'chip_interface_id', 'display': '芯片接口', 'required': False, 'ref': 'chip_interface'},
            {'name': 'chip_model_id', 'display': '芯片型号', 'required': False, 'ref': 'chip_model'},
            {'name': 'price', 'display': '价格', 'required': False},
            {'name': 'item_number', 'display': '货号', 'required': False},
            {'name': 'purchase_date', 'display': '购买日期', 'required': False},
            {'name': 'merchant_id', 'display': '购买商家', 'required': False, 'ref': 'merchant'}
        ]
    },
    'carriage': {
        'display_name': '车厢模型',
        'category': 'model',
        'has_set_detection': True,
        'fields': [
            # 套装公共字段
            {'name': 'brand_id', 'display': '品牌', 'required': True, 'ref': 'brand', 'is_set_field': True},
            {'name': 'scale', 'display': '比例', 'required': True, 'is_set_field': True},
            {'name': 'series_id', 'display': '系列', 'required': False, 'ref': 'carriage_series', 'is_set_field': True},
            {'name': 'depot_id', 'display': '配属', 'required': False, 'ref': 'depot', 'is_set_field': True},
            {'name': 'train_number', 'display': '车次', 'required': False, 'is_set_field': True},
            {'name': 'plaque', 'display': '挂牌', 'required': False, 'is_set_field': True},
            {'name': 'item_number', 'display': '货号', 'required': False, 'is_set_field': True},
            {'name': 'total_price', 'display': '总价', 'required': False, 'is_set_field': True},
            {'name': 'purchase_date', 'display': '购买日期', 'required': False, 'is_set_field': True},
            {'name': 'merchant_id', 'display': '购买商家', 'required': False, 'ref': 'merchant', 'is_set_field': True},
            # 车厢项字段
            {'name': 'model_id', 'display': '车型', 'required': False, 'ref': 'carriage_model', 'is_item_field': True},
            {'name': 'car_number', 'display': '车辆号', 'required': False, 'is_item_field': True},
            {'name': 'color', 'display': '颜色', 'required': False, 'is_item_field': True},
            {'name': 'lighting', 'display': '灯光', 'required': False, 'is_item_field': True}
        ]
    },
    'trainset': {
        'display_name': '动车组模型',
        'category': 'model',
        'fields': [
            {'name': 'brand_id', 'display': '品牌', 'required': True, 'ref': 'brand'},
            {'name': 'scale', 'display': '比例', 'required': True},
            {'name': 'series_id', 'display': '系列', 'required': False, 'ref': 'trainset_series'},
            {'name': 'power_type_id', 'display': '动力', 'required': False, 'ref': 'power_type'},
            {'name': 'model_id', 'display': '车型', 'required': False, 'ref': 'trainset_model'},
            {'name': 'depot_id', 'display': '配属', 'required': False, 'ref': 'depot'},
            {'name': 'plaque', 'display': '挂牌', 'required': False},
            {'name': 'color', 'display': '颜色', 'required': False},
            {'name': 'formation', 'display': '编组', 'required': False},
            {'name': 'trainset_number', 'display': '动车号', 'required': False, 'unique_in_scale': True},
            {'name': 'decoder_number', 'display': '编号', 'required': False},
            {'name': 'head_light', 'display': '头车灯', 'required': False},
            {'name': 'interior_light', 'display': '室内灯', 'required': False},
            {'name': 'chip_interface_id', 'display': '芯片接口', 'required': False, 'ref': 'chip_interface'},
            {'name': 'chip_model_id', 'display': '芯片型号', 'required': False, 'ref': 'chip_model'},
            {'name': 'price', 'display': '价格', 'required': False},
            {'name': 'item_number', 'display': '货号', 'required': False},
            {'name': 'purchase_date', 'display': '购买日期', 'required': False},
            {'name': 'merchant_id', 'display': '购买商家', 'required': False, 'ref': 'merchant'}
        ]
    },
    'locomotive_head': {
        'display_name': '先头车模型',
        'category': 'model',
        'fields': [
            {'name': 'brand_id', 'display': '品牌', 'required': True, 'ref': 'brand'},
            {'name': 'scale', 'display': '比例', 'required': True},
            {'name': 'model_id', 'display': '车型', 'required': False, 'ref': 'trainset_model'},
            {'name': 'special_color', 'display': '涂装', 'required': False},
            {'name': 'head_light', 'display': '头车灯', 'required': False},
            {'name': 'interior_light', 'display': '室内灯', 'required': False},
            {'name': 'price', 'display': '价格', 'required': False},
            {'name': 'item_number', 'display': '货号', 'required': False},
            {'name': 'purchase_date', 'display': '购买日期', 'required': False},
            {'name': 'merchant_id', 'display': '购买商家', 'required': False, 'ref': 'merchant'}
        ]
    }
}
```

## 车厢模型合并单元格处理规则

### 套装识别

1. **按合并单元格识别（推荐）：**
   - 同一列中连续多行合并为一个单元格的，视为同一个套装
   - 未合并的列表示该字段每个车厢项不同

2. **异常处理：**
   - 如果某行的多个列被合并到不同的行范围（如 A 列合并 1-3 行，B 列合并 1-4 行），报错提示用户修复
   - 如果套装公共字段未合并单元格，使用该列第一行的值（或最后一行，用户可选）

### 数据解析逻辑

```
对于每个 Sheet：
1. 检测所有合并单元格区域
2. 识别套装边界：
   - 如果 "品牌" 列（套装字段）合并了 N 行，则这 N 行属于同一套装
3. 处理未合并的套装字段：
   - 取该套装第一行的值（默认）
4. 验证一致性：
   - 所有套装字段的合并范围必须一致
   - 不一致则报告异常
```

## 错误处理

### 预检查阶段

| 错误类型 | 处理方式 |
|---------|---------|
| 必填字段未映射 | 阻止下一步，提示必须映射 |
| 字段类型不匹配 | 警告，允许继续 |
| 唯一性冲突 | 显示冲突列表，要求选择处理方式 |
| 外键引用不存在 | 警告，提示可能导入失败 |
| 合并单元格异常 | 显示异常详情，要求解决或确认 |

### 导入阶段

| 错误类型 | 处理方式 |
|---------|---------|
| 数据验证失败 | 跳过该行，记录错误日志 |
| 外键查找失败 | 跳过该行，记录警告 |
| 数据库写入失败 | 回滚当前表，继续下一表 |

## 兼容性

- 支持浏览器：Chrome、Edge、Safari
- 响应式设计：适配桌面和平板设备
- Excel 格式：.xlsx（推荐）、.xls

## 实现优先级

1. **P0 - 核心功能**
   - 文件解析 API
   - Sheet 映射步骤
   - 列映射步骤
   - 基础导入执行

2. **P1 - 增强功能**
   - 模板保存/加载
   - 预检查和冲突处理
   - 车厢合并单元格识别

3. **P2 - 优化功能**
   - 断点续传
   - 模板重命名
   - 取消时保存提醒
