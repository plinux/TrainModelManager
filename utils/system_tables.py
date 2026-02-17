"""
系统表配置模块
定义所有系统信息表和模型数据表的字段配置，用于自定义导入功能
"""

# 系统表配置字典
SYSTEM_TABLES = {
  # ==================== 系统信息表 ====================
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

  # ==================== 模型数据表 ====================
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


def get_tables_by_category(category):
  """
  按类别获取表配置

  Args:
    category: 表类别，'system' 或 'model'

  Returns:
    dict: 符合类别的表配置字典
  """
  return {k: v for k, v in SYSTEM_TABLES.items() if v['category'] == category}


def get_table_display_info():
  """
  获取所有表的显示信息（用于前端下拉菜单）

  Returns:
    list: 表显示信息列表，系统表在前，模型表在后
    每项包含: name, display_name, category, tooltip(可选), has_set_detection(可选)
  """
  result = []

  # 系统信息表在前
  for name, config in SYSTEM_TABLES.items():
    if config['category'] == 'system':
      info = {
        'name': name,
        'display_name': config['display_name'],
        'category': config['category']
      }
      if 'tooltip' in config:
        info['tooltip'] = config['tooltip']
      result.append(info)

  # 模型数据表在后
  for name, config in SYSTEM_TABLES.items():
    if config['category'] == 'model':
      info = {
        'name': name,
        'display_name': config['display_name'],
        'category': config['category']
      }
      if 'has_set_detection' in config:
        info['has_set_detection'] = config['has_set_detection']
      result.append(info)

  return result
