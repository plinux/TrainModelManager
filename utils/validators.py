"""
验证函数模块
包含各种格式验证函数
"""
import re
from typing import Tuple


def validate_locomotive_number(number: str) -> bool:
  """
  验证机车号格式：4-12位数字，允许前导0

  Args:
    number: 机车号字符串

  Returns:
    bool: 是否符合格式要求
  """
  if not number:
    return False
  return bool(re.match(r'^\d{4,12}$', number))


def validate_decoder_number(number: str) -> bool:
  """
  验证编号格式：1-4位数字，无前导0

  Args:
    number: 编号字符串

  Returns:
    bool: 是否符合格式要求
  """
  if not number:
    return False
  return bool(re.match(r'^[1-9]\d{0,3}$', number))


def validate_trainset_number(number: str) -> bool:
  """
  验证动车号格式：3-12位数字，允许前导0

  Args:
    number: 动车号字符串

  Returns:
    bool: 是否符合格式要求
  """
  if not number:
    return False
  return bool(re.match(r'^\d{3,12}$', number))


def validate_car_number(number: str) -> bool:
  """
  验证车辆号格式：1-20位字母、数字、连字符组合

  Args:
    number: 车辆号字符串

  Returns:
    bool: 是否符合格式要求
  """
  if not number:
    return False
  # 允许字母、数字、连字符，长度1-20位
  return bool(re.match(r'^[A-Za-z0-9\-]{1,20}$', number))


# 验证规则配置，用于前端和后端统一
VALIDATION_RULES = {
  'locomotive_number': {
    'pattern': r'^\d{4,12}$',
    'message': '机车号格式错误：应为4-12位数字，允许前导0',
    'min_length': 4,
    'max_length': 12
  },
  'decoder_number': {
    'pattern': r'^[1-9]\d{0,3}$',
    'message': '编号格式错误：应为1-4位数字，无前导0',
    'min_length': 1,
    'max_length': 4
  },
  'trainset_number': {
    'pattern': r'^\d{3,12}$',
    'message': '动车号格式错误：应为3-12位数字，允许前导0',
    'min_length': 3,
    'max_length': 12
  },
  'car_number': {
    'pattern': r'^[A-Za-z0-9\-]{1,20}$',
    'message': '车辆号格式错误：应为1-20位字母、数字或连字符',
    'min_length': 1,
    'max_length': 20
  }
}


def validate_field(field_name: str, value: str) -> Tuple[bool, str]:
  """
  通用字段验证函数

  Args:
    field_name: 字段名
    value: 字段值

  Returns:
    Tuple[bool, str]: (是否验证通过, 错误消息)
  """
  if field_name not in VALIDATION_RULES:
    return True, ''

  rule = VALIDATION_RULES[field_name]
  if not value:
    return True, ''  # 空值不验证格式

  if not re.match(rule['pattern'], value):
    return False, rule['message']

  return True, ''
