"""
公共辅助函数模块
包含日期处理、类型转换、唯一性验证等通用函数
"""
from datetime import date, datetime
from typing import Optional, Any, Callable, List, Dict
from flask import jsonify


def parse_purchase_date(date_str: Any) -> date:
  """
  解析购买日期字符串，返回 date 对象或默认值

  Args:
    date_str: 日期字符串或 datetime 对象

  Returns:
    date: 解析后的日期对象，解析失败返回当天日期
  """
  if not date_str:
    return date.today()

  # 处理空字符串
  if isinstance(date_str, str) and not date_str.strip():
    return date.today()

  # 处理 datetime 对象
  if isinstance(date_str, datetime):
    return date_str.date()

  try:
    return datetime.strptime(str(date_str), '%Y-%m-%d').date()
  except (ValueError, TypeError):
    return date.today()


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
  """
  安全转换为整数

  Args:
    value: 待转换的值
    default: 转换失败时的默认值

  Returns:
    int or None: 转换后的整数或默认值
  """
  if value is None:
    return default

  try:
    return int(value)
  except (ValueError, TypeError):
    return default


def safe_float(value: Any, default: float = 0.0) -> float:
  """
  安全转换为浮点数

  Args:
    value: 待转换的值
    default: 转换失败时的默认值

  Returns:
    float: 转换后的浮点数或默认值
  """
  if value is None:
    return default

  try:
    return float(value)
  except (ValueError, TypeError):
    return default


def validate_unique(model_class, field_name: str, value: str, scale: str = None,
           exclude_id: int = None, db_session=None) -> bool:
  """
  统一的唯一性验证

  Args:
    model_class: SQLAlchemy 模型类
    field_name: 字段名
    value: 要验证的值
    scale: 比例（可选）
    exclude_id: 排除的记录 ID（用于编辑时排除自身）
    db_session: 数据库会话

  Returns:
    bool: True 表示不存在重复（可用），False 表示存在重复
  """
  if db_session is None:
    from models import db
    db_session = db.session

  filters = {field_name: value}
  if scale is not None:
    filters['scale'] = scale

  query = model_class.query.filter_by(**filters)

  if exclude_id:
    query = query.filter(model_class.id != exclude_id)

  return query.first() is None


def group_by_field(items: List[Any], get_field_func: Callable[[Any], str]) -> Dict[str, int]:
  """
  通用的分组统计函数

  Args:
    items: 待分组的对象列表
    get_field_func: 获取分组字段值的函数

  Returns:
    Dict[str, int]: 分组统计结果
  """
  result = {}
  for item in items:
    field_value = get_field_func(item)
    result[field_value] = result.get(field_value, 0) + 1
  return result


def api_success(message: str = '操作成功', data: dict = None) -> dict:
  """
  生成成功的 API 响应

  Args:
    message: 成功消息
    data: 额外数据

  Returns:
    dict: JSON 响应字典
  """
  response = {'success': True, 'message': message}
  if data:
    response.update(data)
  return response


def api_error(message: str, field: str = None, errors: List[dict] = None) -> dict:
  """
  生成错误的 API 响应

  Args:
    message: 错误消息
    field: 字段名（可选）
    errors: 错误列表（可选）

  Returns:
    dict: JSON 响应字典
  """
  if errors:
    return {'success': False, 'errors': errors}
  if field:
    return {'success': False, 'errors': [{'field': field, 'message': message}]}
  return {'success': False, 'error': message}


def parse_boolean(value: Any) -> Optional[bool]:
  """
  解析布尔值

  Args:
    value: 待解析的值

  Returns:
    bool or None: 解析后的布尔值
  """
  if not value:
    return None
  if isinstance(value, bool):
    return value
  return str(value).lower() in ('true', '1', '是', '有', 'yes')
