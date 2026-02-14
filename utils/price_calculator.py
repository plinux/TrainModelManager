"""
价格计算模块
包含安全表达式求值器
"""
import ast
import operator
import re
import logging

logger = logging.getLogger(__name__)


class SafeEval(ast.NodeVisitor):
  """
  安全的表达式求值器，只允许数字和基本运算

  支持的操作符：+、-、*、/、()
  """

  def __init__(self):
    self._operators = {
      ast.Add: operator.add,
      ast.Sub: operator.sub,
      ast.Mult: operator.mul,
      ast.Div: operator.truediv,
      ast.USub: operator.neg
    }

  def visit(self, node):
    if not self._allowed_nodes(node):
      raise ValueError(f"不安全的表达式节点: {type(node).__name__}")
    return super().visit(node)

  def _allowed_nodes(self, node):
    return isinstance(node, (
      ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant
    ))

  def generic_visit(self, node):
    if isinstance(node, ast.BinOp):
      left = self.visit(node.left)
      right = self.visit(node.right)
      return self._operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
      operand = self.visit(node.operand)
      return self._operators[type(node.op)](operand)
    elif isinstance(node, ast.Constant):
      if isinstance(node.value, (int, float)):
        return node.value
      raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
    return super().generic_visit(node)


def calculate_price(price_expr) -> float:
  """
  安全计算价格表达式

  Args:
    price_expr: 价格表达式（如 "288+538"）或数字

  Returns:
    float: 计算结果，无效表达式返回 0
  """
  if not price_expr or not str(price_expr).strip():
    return 0

  price_str = str(price_expr)

  # 只允许数字、+、-、*、/、()、小数点
  if not re.match(r'^[\d+\-*/().\s]+$', price_str):
    logger.debug(f"Price expression '{price_str}' does not match pattern")
    return 0

  try:
    expr = ast.parse(price_str, mode='eval')
    evaluator = SafeEval()
    result = evaluator.visit(expr.body)

    if isinstance(result, (int, float)):
      return result
    return 0
  except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as e:
    logger.debug(f"Error calculating price '{price_str}': {e}")
    return 0
