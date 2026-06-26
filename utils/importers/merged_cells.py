"""
合并单元格检测工具（P3-1：从 routes/api.py 抽出）

纯 openpyxl 操作，无数据库依赖。供 custom_import 的车厢套装导入使用。
"""


def get_cell_value_with_merge(sheet, row, col):
  """获取单元格值，支持合并单元格。

  当单元格是合并单元格的一部分且值为 None 时，从合并范围左上角取值。

  Args:
    sheet: openpyxl worksheet 对象
    row: 行号（1-based）
    col: 列号（1-based）

  Returns:
    单元格值
  """
  cell = sheet.cell(row=row, column=col)
  if cell.value is not None:
    return cell.value

  for merged_range in sheet.merged_cells.ranges:
    if (merged_range.min_row <= row <= merged_range.max_row and
        merged_range.min_col <= col <= merged_range.max_col):
      return sheet.cell(row=merged_range.min_row, column=merged_range.min_col).value

  return None


def detect_merged_cell_sets(sheet, headers, set_field_indices):
  """检测 Excel 工作表中的合并单元格，识别套装边界。

  Args:
    sheet: openpyxl worksheet 对象
    headers: 列标题列表
    set_field_indices: 套装字段在 headers 中的索引列表

  Returns:
    list | None: 套装分组 [{'start_row', 'end_row'}]，None 表示无法检测
  """
  if not sheet.merged_cells.ranges:
    return None

  # 构建 (列索引 -> 合并范围列表) 的映射（openpyxl 行列从 1 开始）
  column_merge_map = {}
  for merged_range in sheet.merged_cells.ranges:
    start_col = merged_range.min_col
    end_col = merged_range.max_col
    start_row = merged_range.min_row
    end_row = merged_range.max_row

    # 只处理单列的合并单元格
    if start_col == end_col:
      if start_col not in column_merge_map:
        column_merge_map[start_col] = []
      column_merge_map[start_col].append({
        'start_row': start_row,
        'end_row': end_row
      })

  # 检查套装字段列是否有合并单元格
  set_field_cols = [idx + 1 for idx in set_field_indices]  # 转 1-based
  has_set_field_merges = any(col in column_merge_map for col in set_field_cols)
  if not has_set_field_merges:
    return None

  # 用第一个有合并单元格的套装字段列识别套装
  primary_col = None
  for col in set_field_cols:
    if col in column_merge_map:
      primary_col = col
      break
  if not primary_col:
    return None

  # 收集所有边界行
  boundary_rows = {2}  # 数据从第 2 行开始
  for merge_info in column_merge_map[primary_col]:
    boundary_rows.add(merge_info['start_row'])
    boundary_rows.add(merge_info['end_row'] + 1)  # 下一个套装开始行

  # 获取总数据行数
  max_data_row = 0
  for row in sheet.iter_rows(min_row=2, values_only=True):
    if any(cell is not None for cell in row):
      max_data_row += 1
    else:
      break
  boundary_rows.add(max_data_row + 2)  # 结束边界

  # 排序并构建套装分组
  sorted_boundaries = sorted(boundary_rows)
  set_groups = []
  for i in range(len(sorted_boundaries) - 1):
    start_row = sorted_boundaries[i]
    end_row = sorted_boundaries[i + 1] - 1
    if start_row <= end_row and start_row >= 2:
      set_groups.append({'start_row': start_row, 'end_row': end_row})

  return set_groups if set_groups else None


def validate_merged_cells_consistency(sheet, headers, set_field_indices, set_groups):
  """验证合并单元格的一致性。

  Args:
    sheet: openpyxl worksheet 对象
    headers: 列标题列表
    set_field_indices: 套装字段索引列表
    set_groups: 套装分组列表

  Returns:
    list: 警告消息列表
  """
  warnings = []
  if not sheet.merged_cells.ranges or not set_groups:
    return warnings

  for group in set_groups:
    start_row = group['start_row']
    end_row = group['end_row']

    for field_idx in set_field_indices:
      col = field_idx + 1  # 1-based
      values = []
      for row_idx in range(start_row, end_row + 1):
        value = sheet.cell(row=row_idx, column=col).value
        if value is not None:
          values.append(str(value).strip())

      if values and len(set(values)) > 1:
        field_name = headers[field_idx] if field_idx < len(headers) else f"列{col}"
        warnings.append(
          f"行 {start_row}-{end_row}，{field_name} 列值不一致: {', '.join(set(values))}"
        )

  return warnings
