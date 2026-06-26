"""
数码功能表解析模块

支持 AI 视觉 API (Claude/OpenAI) 和本地 OCR 两种解析方案
根据配置自动选择: 有 API Key 用 AI, 否则回退到本地 OCR
"""

import os
import re
import json
import base64
import logging
from io import BytesIO
from PIL import Image
from flask import current_app
from models import db, FunctionKey

logger = logging.getLogger(__name__)

# F键表格识别正则: F0/F1/.../Function0/Function1.../Key0/Key1 等
F_KEY_PATTERN = re.compile(
  r'(?:F(?:unction)?\s*(\d+))',
  re.IGNORECASE
)

# F键提取数字的正则
KEY_NUMBER_PATTERN = re.compile(r'(\d+)')

# AI 解析提示词
AI_PARSE_PROMPT = """请分析这张数码功能表图片。找到其中包含 F0-F31（或 Function0-Function31) 功能键映射的表格（通常是2列或3列）。
忽略图片中的标题、说明文字等其他内容,只返回 JSON 格式的数组,不要包含其他文字。

格式: [{"key": 0, "name": "头尾灯", "description": ""}]
如果表格不存在,返回空数组。只返回表格中的行。"""


def parse_function_table(file_path, mime_type):
  """
  解析数码功能表文件,提取 F0~F31 功能键映射

  Args:
    file_path: 文件绝对路径
    mime_type: 文件 MIME 类型

  Returns:
    list[dict] | 功能键列表, 每项包含:
      - key_number: 功能键号(0-31)
      - function_name: 功能名称
      - description: 功能说明(可选)
    解析失败返回 None
  """
  parser_mode = current_app.config.get('FUNCTION_TABLE_PARSER', 'auto')
  api_key = current_app.config.get('AI_PARSER_API_KEY', '')

  # 决定解析方式
  use_ai = False
  if parser_mode == 'ai':
    use_ai = True
  elif parser_mode == 'local':
    use_ai = False
  else:  # auto
    use_ai = bool(api_key)

  try:
    if use_ai:
      result = _parse_with_ai(file_path, mime_type)
    else:
      result = _parse_with_local_ocr(file_path, mime_type)
    if result is not None and len(result) > 0:
      logger.info(f"Function table parsed: {len(result)} key(s) found")
      return result
    return None
  except Exception as e:
    logger.error(f"Function table parsing failed: {e}")
    return None


def save_function_keys(model_type, model_id, parsed_keys, source_file_id=None):
  """
  保存解析后的功能键到数据库

  Args:
    model_type: 模型类型 (locomotive/trainset)
    model_id: 模型ID
    parsed_keys: 解析结果列表
    source_file_id: 关联的 ModelFile ID

  Returns:
    list[FunctionKey]: 保存后的 FunctionKey 对象列表
  """
  # 删除旧数据
  FunctionKey.query.filter_by(
    model_type=model_type,
    model_id=model_id
  ).delete()

  # 批量写入新数据
  new_keys = []
  for item in parsed_keys:
    fk = FunctionKey(
      model_type=model_type,
      model_id=model_id,
      key_number=item.get('key_number', item.get('key', 0)),
      function_name=item.get('function_name', item.get('name', '')),
      description=item.get('description', ''),
      source_file_id=source_file_id
    )
    db.session.add(fk)
    new_keys.append(fk)

  db.session.commit()
  logger.info(f"Saved {len(new_keys)} function keys for {model_type}:{model_id}")
  return new_keys


def get_function_keys(model_type, model_id):
  """
  获取模型的功能键数据

  Args:
    model_type: 模型类型
    model_id: 模型ID

  Returns:
    list[dict]: 功能键字典列表
  """
  keys = FunctionKey.query.filter_by(
    model_type=model_type,
    model_id=model_id
  ).order_by(FunctionKey.key_number).all()
  return [k.to_dict() for k in keys]


def update_function_keys(model_type, model_id, keys_data):
  """
  更新模型的功能键数据(覆盖写入)

  Args:
    model_type: 模型类型
    model_id: 模型ID
    keys_data: 功能键数据列表

  Returns:
    list[FunctionKey]: 更新后的 FunctionKey 列表
  """
  # 删除旧数据
  FunctionKey.query.filter_by(
    model_type=model_type,
    model_id=model_id
  ).delete()

  # 写入新数据
  new_keys = []
  for item in keys_data:
    fk = FunctionKey(
      model_type=model_type,
      model_id=model_id,
      key_number=item.get('key_number', 0),
      function_name=item.get('function_name', ''),
      description=item.get('description', ''),
    )
    db.session.add(fk)
    new_keys.append(fk)

  db.session.commit()
  return new_keys


def export_function_keys_excel(model_type, model_id, brand_abbr='', item_number=''):
  """
  导出功能键数据为 Excel

  Args:
    model_type: 模型类型
    model_id: 模型ID
    brand_abbr: 品牌缩写(用于文件名)
    item_number: 货号(用于文件名)

  Returns:
    BytesIO: Excel 文件的字节流
  """
  from openpyxl import Workbook
  from openpyxl.styles import Font

  keys = FunctionKey.query.filter_by(
    model_type=model_type,
    model_id=model_id
  ).order_by(FunctionKey.key_number).all()

  wb = Workbook()
  ws = wb.active
  ws.title = '功能键'

  # 写入表头
  headers = ['功能键', '功能名称', '说明']
  ws.append(headers)
  for cell in ws[1]:
    cell.font = Font(bold=True)

  # 写入数据行
  for fk in keys:
    ws.append([
      f'F{fk.key_number}',
      fk.function_name or '',
      fk.description or ''
    ])

  buf = BytesIO()
  wb.save(buf)
  filename = f"{brand_abbr}_{item_number}_FunctionKey.xlsx"
  buf.seek(0)
  buf.filename = filename
  buf.content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  return buf


# ==================== AI 视觉解析 ====================

def _parse_with_ai(file_path, mime_type):
  """
  使用 AI 视觉 API 解析功能表

  Args:
    file_path: 文件绝对路径
    mime_type: 文件 MIME 类型

  Returns:
    list[dict] | 功能键列表, 解析失败返回 None
  """
  provider = current_app.config.get('AI_PARSER_PROVIDER', 'claude')
  api_key = current_app.config.get('AI_PARSER_API_KEY', '')
  model = current_app.config.get('AI_PARSER_MODEL', 'claude-sonnet-4-20250514')

  if not api_key:
    logger.warning("AI Parser API key not configured")
    return None

  # 准备图片数据
  images = _prepare_images(file_path, mime_type)
  if not images:
    logger.error("No images prepared for AI parsing")
    return None

  try:
    if provider == 'claude':
      result = _parse_with_claude(images, api_key, model)
    else:
      result = _parse_with_openai(images, api_key, model)
    return result
  except Exception as e:
    logger.error(f"AI parsing failed: {e}")
    return None


def _prepare_images(file_path, mime_type):
  """
  将文件准备为 AI 可用的图片列表

  Args:
    file_path: 文件路径
    mime_type: MIME 类型

  Returns:
    list[dict]: [{'data': base64, 'mime_type': str}]
  """
  images = []

  if mime_type and mime_type.startswith('image/'):
    # 图片文件直接读取
    with open(file_path, 'rb') as f:
      img_data = f.read()
    b64_data = base64.b64encode(img_data).decode('utf-8')
    images.append({'data': b64_data, 'mime_type': mime_type})

  elif mime_type == 'application/pdf':
    # PDF 转图片
    pages = _convert_pdf_to_images(file_path)
    for page_img in pages:
      b64_data = base64.b64encode(page_img).decode('utf-8')
      images.append({'data': b64_data, 'mime_type': 'image/png'})

  else:
    # 其他格式尝试用 PIL 读取
    try:
      img = Image.open(file_path)
      buf = BytesIO()
      img.save(buf, format='PNG')
      b64_data = base64.b64encode(buf.getvalue()).decode('utf-8')
      images.append({'data': b64_data, 'mime_type': 'image/png'})
    except Exception:
      logger.error(f"Cannot prepare image from {file_path}")
      return None

  return images if images else None


def _convert_pdf_to_images(file_path, max_pages=3):
  """
  将 PDF 转为图片列表

  Args:
    file_path: PDF 文件路径
    max_pages: 最多转换页数

  Returns:
    list[bytes]: PNG 图片字节数据列表
  """
  try:
    from pdf2image import convert_from_path
    pages = convert_from_path(
      file_path, dpi=200,
      fmt='png',
      first_page=1,
      last_page=max_pages
    )
    return [page_to_bytes(p) for p in pages]
  except ImportError:
    # 回退到 pdfplumber
    return _convert_pdf_with_pdfplumber(file_path)


def page_to_bytes(page_img):
  """将 PIL Image 转为 bytes"""
  buf = BytesIO()
  page_img.save(buf, format='PNG')
  return buf.getvalue()


def _convert_pdf_with_pdfplumber(file_path):
  """使用 pdfplumber 将 PDF 页面转为图片"""
  try:
    import pdfplumber
    pages = []
    with pdfplumber.open(file_path) as pdf:
      for i in range(min(3, len(pdf.pages))):
        page = pdf.pages[i]
        img = page.to_image(resolution=200)
        if img:
          buf = BytesIO()
          img.save(buf, format='PNG')
          pages.append(buf.getvalue())
    return pages
  except ImportError:
    logger.error("Neither pdf2image nor pdfplumber available")
    return []


def _parse_with_claude(images, api_key, model):
  """使用 Claude API 解析"""
  import anthropic

  client = anthropic.Anthropic(api_key=api_key)

  message_content = []
  for img_data in images:
    b64_data = img_data['data']
    mime_type = img_data['mime_type']
    message_content.append({
      "type": "image",
      "source": {
        "type": "base64",
        "media_type": mime_type,
        "data": b64_data
      }
    })

  message_content.append({"type": "text", "text": AI_PARSE_PROMPT})

  response = client.messages.create(
    model=model,
    max_tokens=1024,
    messages=[{"role": "user", "content": message_content}]
  )

  return _extract_keys_from_response(response.content[0].text)


def _parse_with_openai(images, api_key, model):
  """使用 OpenAI API 解析"""
  from openai import OpenAI

  client = OpenAI(api_key=api_key)

  content = []
  for img_data in images:
    b64_data = img_data['data']
    mime_type = img_data['mime_type']
    content.append({
      "type": "image_url",
      "image_url": f"data:{mime_type};base64,{b64_data}"
    })

  content.append({"type": "text", "text": AI_PARSE_PROMPT})

  response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": content}]
  )

  return _extract_keys_from_response(response.choices[0].message.content)


def _extract_keys_from_response(text):
  """从 AI 返回的文本中提取功能键列表"""
  # 尝试直接解析 JSON
  try:
    data = json.loads(text)
    if isinstance(data, list):
      return _normalize_parsed_keys(data)
  except (json.JSONDecodeError, ValueError):
    pass

  # 尝试提取 JSON 块（贪婪匹配，确保捕获完整数组）
  match = re.search(r'\[.*\]', text, re.DOTALL | re.MULTILINE)
  if match:
    json_str = match.group(0)
    try:
      data = json.loads(json_str)
      if isinstance(data, list):
        return _normalize_parsed_keys(data)
    except (json.JSONDecodeError, ValueError):
      pass

  logger.warning(f"Failed to extract JSON from AI response: {text[:200]}")
  return None


def _normalize_parsed_keys(keys):
  """标准化解析结果"""
  normalized = []
  for item in keys:
    if isinstance(item, dict):
      key_num = item.get('key', item.get('key_number', 0))
      name = item.get('name', item.get('function_name', ''))
      desc = item.get('description', '')
      if isinstance(key_num, int) and 0 <= key_num <= 31:
        normalized.append({
          'key_number': key_num,
          'function_name': str(name).strip(),
          'description': str(desc).strip() if desc else ''
        })
  return normalized


# ==================== 本地 OCR 解析 ====================

def _parse_with_local_ocr(file_path, mime_type):
  """
  使用本地 OCR 解析功能表

  Args:
    file_path: 文件路径
    mime_type: MIME 类型

  Returns:
    list[dict] | 功能键列表
  """
  # PDF 文件先尝试用 pdfplumber 提取文本
  if mime_type == 'application/pdf':
    text = _extract_text_from_pdf(file_path)
    if text:
      result = _extract_keys_from_text(text)
      if result:
        return result

  # PDF 或图片用 OCR
  images = _prepare_images(file_path, mime_type)
  if not images:
    return None

  # 对每张图片进行 OCR
  all_text = ""
  for img_data in images:
    img_bytes = base64.b64decode(img_data['data'])
    img = Image.open(BytesIO(img_bytes))
    text = _ocr_image(img)
    if text:
      all_text += text + "\n"

  return _extract_keys_from_text(all_text)


def _extract_text_from_pdf(file_path):
  """从 PDF 中提取文本"""
  try:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
      for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
          text_parts.append(page_text)
        # 尝试提取表格
        tables = page.extract_tables()
        for table in tables:
          for row in table:
            row_text = " ".join([str(cell) for cell in row if cell])
            text_parts.append(row_text)
    return "\n".join(text_parts)
  except ImportError:
    return None


def _ocr_image(img):
  """
  对图片进行 OCR

  Args:
    img: PIL Image 对象

  Returns:
    str: 识别的文本
  """
  try:
    import pytesseract
    # 预处理: 转灰度
    if img.mode != 'L':
      img = img.convert('L')
    # 放大图片以提高识别准确度
    width, height = img.size
    if width < 1000:
      ratio = 1000 / width
      img = img.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
    return text
  except ImportError:
    logger.error("pytesseract not installed")
    return None


def _extract_keys_from_text(text):
  """
  从 OCR 文本中提取功能键映射

  Args:
    text: OCR 识别的文本

  Returns:
    list[dict] | 功能键列表
  """
  result = []
  lines = text.split('\n')
  for line in lines:
    line = line.strip()
    if not line:
      continue
    # 匹配 F0/F1/.../F31 或 Function0/Function1 等
    match = F_KEY_PATTERN.search(line)
    if not match:
      continue
    # 提取键号
    key_match = KEY_NUMBER_PATTERN.search(match.group(1))
    if not key_match:
      continue
    key_number = int(key_match.group(1))
    if key_number > 31:
      continue
    # 提取功能名称(键号后面的文字)
    remainder = line[match.end():].strip()
    # 清理分隔符和多余字符
    remainder = re.sub(r'^[\s：:|｜\-\s]+', '', remainder).strip()
    # 拆分功能名称和描述
    parts = re.split(r'[\s]{2,}', remainder)
    function_name = parts[0].strip() if parts else remainder
    description = parts[1].strip() if len(parts) > 1 else ''
    if function_name:
      result.append({
        'key_number': key_number,
        'function_name': function_name,
        'description': description
      })

  return result if result else None
