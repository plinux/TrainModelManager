# 品牌缩写字段设计文档

## 概述

为品牌表添加"缩写"字段，用于文件命名时替代完整的品牌名称，使文件名更简洁。

## 需求

1. 品牌表新增缩写字段，只允许填充英文字母
2. 缩写必须唯一
3. 文件上传时使用缩写替代品牌名作为前缀
4. 编辑品牌时自动生成缩写建议，但允许手动修改

## 缩写生成规则

| 品牌类型 | 规则 | 示例 |
|---------|------|------|
| 中文名称 | 每个汉字的拼音首字母大写 | 百万城 → BWC |
| 纯英文 ≤6字母 | 直接使用原名称（大写） | Kunter → KUNTER |
| 纯英文 >6字母 | 前3个字母大写 | Fleischmann → FLE |
| 多词英文 | 每个单词首字母 | KukePig → KP |

## 数据模型

```python
class Brand(db.Model):
    __tablename__ = 'brand'

    id = db.Column(Integer, primary_key=True, comment='主键')
    name = db.Column(String(100), nullable=False, unique=True, comment='品牌名称')
    abbreviation = db.Column(String(10), nullable=False, unique=True, comment='品牌缩写')
    website = db.Column(String(255), comment='官方网站')
    search_url = db.Column(String(255), comment='搜索URL模板')
```

## 文件命名变更

- 旧格式：`{品牌名}_{货号}.{扩展名}`
- 新格式：`{缩写}_{货号}.{扩展名}`

示例：
- 百万城_12345.jpg → BWC_12345.jpg
- Fleischmann_67890.jpg → FLE_67890.jpg

## 前端交互

- 新增/编辑品牌时，输入品牌名后自动生成缩写建议
- 用户可以手动修改缩写
- 保存时验证缩写的唯一性和格式（仅英文字母）

## 实现文件清单

| 文件 | 修改类型 | 说明 |
|-----|---------|------|
| models.py | 修改 | Brand 模型新增 abbreviation 字段 |
| init_db.py | 修改 | 预置品牌数据增加缩写 |
| requirements.txt | 修改 | 新增 pypinyin 依赖 |
| routes/options.py | 修改 | 品牌 CRUD 处理缩写字段 |
| routes/files.py | 修改 | 文件命名使用缩写 |
| utils/file_sync.py | 修改 | 文件夹和文件命名使用缩写 |
| utils/helpers.py | 修改 | 新增缩写生成函数 |
| templates/options.html | 修改 | 品牌表格新增缩写列 |
| static/js/options.js | 修改 | 缩写自动生成和验证 |
| tests/test_options.py | 修改 | 品牌测试增加缩写字段 |
| docs/design/Train-Model-Manager-Implementation.md | 修改 | 更新实现文档 |

## 注意事项

- 重新初始化数据库后，已上传的文件需要删除并重新上传
- 缩写字段设为 NOT NULL，所有品牌必须有缩写
