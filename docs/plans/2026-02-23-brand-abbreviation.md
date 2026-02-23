# 品牌缩写字段实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为品牌表添加缩写字段，文件上传时使用缩写替代品牌名作为文件名前缀

**Architecture:** 在 Brand 模型新增 abbreviation 字段，创建缩写生成工具函数，修改文件命名相关代码使用缩写

**Tech Stack:** Python, Flask, SQLAlchemy, pypinyin, JavaScript

---

### Task 1: 添加 pypinyin 依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 添加依赖**

在 `requirements.txt` 中添加：
```
pypinyin>=0.49.0
```

**Step 2: 安装依赖**

Run: `source myenv/bin/activate && pip install pypinyin`

**Step 3: 验证安装**

Run: `python -c "from pypinyin import pinyin, Style; print(pinyin('百万城', style=Style.FIRST_LETTER))"`

Expected: `[['b'], ['w'], ['c']]`

---

### Task 2: 创建缩写生成工具函数

**Files:**
- Modify: `utils/helpers.py`
- Test: `tests/test_helpers.py` (新建)

**Step 1: 写测试用例**

```python
# tests/test_helpers.py
import pytest
from utils.helpers import generate_brand_abbreviation


class TestGenerateBrandAbbreviation:
    """测试品牌缩写生成规则"""

    def test_chinese_brand(self):
        """中文品牌：每个汉字拼音首字母大写"""
        assert generate_brand_abbreviation('百万城') == 'BWC'
        assert generate_brand_abbreviation('浩瀚') == 'HH'
        assert generate_brand_abbreviation('深东') == 'SD'

    def test_english_short_brand(self):
        """英文品牌≤6字母：直接使用原名称大写"""
        assert generate_brand_abbreviation('Kunter') == 'KUNTER'
        assert generate_brand_abbreviation('KATO') == 'KATO'
        assert generate_brand_abbreviation('BLI') == 'BLI'
        assert generate_brand_abbreviation('N27') == 'N27'

    def test_english_long_brand(self):
        """英文品牌>6字母：前3个字母大写"""
        assert generate_brand_abbreviation('Fleischmann') == 'FLE'
        assert generate_brand_abbreviation('MicroAce') == 'MIC'
        assert generate_brand_abbreviation('WALTHERS') == 'WAL'

    def test_multi_word_brand_camelcase(self):
        """多词英文(camelCase)：每个单词首字母"""
        assert generate_brand_abbreviation('KukePig') == 'KP'

    def test_english_with_numbers(self):
        """英文含数字：按短品牌处理"""
        assert generate_brand_abbreviation('1435') == '1435'
        assert generate_brand_abbreviation('HCMX') == 'HCMX'

    def test_empty_string(self):
        """空字符串返回空"""
        assert generate_brand_abbreviation('') == ''
```

**Step 2: 运行测试确认失败**

Run: `source myenv/bin/activate && pytest tests/test_helpers.py -v`

Expected: FAIL - ModuleNotFoundError

**Step 3: 实现缩写生成函数**

在 `utils/helpers.py` 末尾添加：

```python
def generate_brand_abbreviation(name: str) -> str:
    """
    根据品牌名称生成缩写

    Args:
        name: 品牌名称

    Returns:
        生成的缩写（大写英文字母和数字）

    Rules:
        - 中文名称：每个汉字的拼音首字母大写
        - 纯英文≤6字母：直接使用原名称大写
        - 纯英文>6字母：前3个字母大写
        - 多词英文(camelCase)：每个单词首字母
    """
    if not name:
        return ''

    # 检查是否包含中文字符
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in name)

    if has_chinese:
        # 中文品牌：拼音首字母
        from pypinyin import pinyin, Style
        result = ''.join([py[0].upper() for py in pinyin(name, style=Style.FIRST_LETTER)])
        return result

    # 检查是否是 camelCase 或 PascalCase 多词格式
    import re
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+', name)

    if len(words) > 1:
        # 多词：取每个词首字母
        result = ''.join([w[0].upper() for w in words if w])
        return result

    # 单词
    if len(name) <= 6:
        return name.upper()
    else:
        return name[:3].upper()
```

**Step 4: 运行测试确认通过**

Run: `source myenv/bin/activate && pytest tests/test_helpers.py -v`

Expected: PASS

**Step 5: 提交**

```bash
git add requirements.txt utils/helpers.py tests/test_helpers.py
git commit -m "feat: add brand abbreviation generation function"
```

---

### Task 3: 修改 Brand 模型

**Files:**
- Modify: `models.py`

**Step 1: 添加 abbreviation 字段**

在 `models.py` 的 Brand 类中添加字段：

```python
class Brand(db.Model):
  """品牌（所有模型共享）"""
  __tablename__ = 'brand'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, unique=True, comment='品牌名称')
  abbreviation = db.Column(String(10), nullable=False, unique=True, comment='品牌缩写')
  website = db.Column(String(255), comment='官方网站')
  search_url = db.Column(String(255), comment='搜索URL模板，{query}为搜索词占位符')

  def __repr__(self):
    return f'<Brand {self.id}: {self.name}>'
```

**Step 2: 运行测试确认模型变更无误**

Run: `source myenv/bin/activate && pytest tests/test_models.py -v`

Expected: 可能有一些测试失败（因为数据库字段变更）

**Step 3: 提交**

```bash
git add models.py
git commit -m "feat: add abbreviation field to Brand model"
```

---

### Task 4: 更新数据库初始化脚本

**Files:**
- Modify: `init_db.py`

**Step 1: 导入缩写生成函数**

在 `init_db.py` 开头的导入部分添加：

```python
from utils.helpers import generate_brand_abbreviation
```

**Step 2: 更新品牌数据结构**

将品牌数据从 tuple 改为包含缩写的结构：

```python
  # 7. 品牌（带官网和搜索URL模板）
  # search_url 中 {query} 会被替换为货号
  brands = [
    ('1435', None, None),
    ('ATHEARN', 'https://www.athearn.com/', 'https://www.athearn.com/Search?term={query}'),
    ('BLI', 'https://broadway-limited.com/', 'https://broadway-limited.com/search?q={query}'),
    ('CMR', None, None),
    ('PIKO', 'https://www.piko-shop.de/en/', 'https://www.piko-shop.de/en/search?query={query}'),
    ('ROCO', 'https://www.roco.cc/ren/', 'https://www.roco.cc/ren/search?searchterm={query}'),
    ('TRIX', 'https://www.trix.de/en', 'https://www.trix.de/en/search?query={query}'),
    ('百万城', 'http://www.bachmannchina.com.cn/', None),
    ('浩瀚', None, None),
    ('深东', None, None),
    ('猩猩', 'http://www.lyxxmx.com/', None),
    ('长鸣', None, None),
    ('跨越', 'https://www.auroraminiature.com/', 'https://www.auroraminiature.com/search?q={query}'),
    ('Kunter', None, None),
    ('茂杉', None, None),
    ('KATO', 'https://www.katomodels.com/', 'https://www.katomodels.com/product/search?keyword={query}'),
    ('HCMX', None, None),
    ('HTMX', None, None),
    ('KukePig', None, None),
    ('N27', None, None),
    ('毫米制造', None, None),
    ('火车花园', None, None),
    ('曙光', None, None),
    ('WALTHERS', 'https://www.walthers.com/', 'https://www.walthers.com/search?w={query}'),
    ('Tomix', 'https://www.tomytec.co.jp/tomix/', None),
    ('微景', None, None),
    ('ARNOLD', 'https://www.arnoldmodel.com/', 'https://www.arnoldmodel.com/search?query={query}'),
    ('Fleischmann', 'https://www.fleischmann.de/fen', 'https://www.fleischmann.de/fen/search?query={query}'),
    ('MicroAce', 'http://www.microace-arii.co.jp/', None)
  ]
  for name, website, search_url in brands:
    if not Brand.query.filter_by(name=name).first():
      abbreviation = generate_brand_abbreviation(name)
      db.session.add(Brand(name=name, abbreviation=abbreviation, website=website, search_url=search_url))
```

**Step 3: 提交**

```bash
git add init_db.py
git commit -m "feat: update init_db with brand abbreviations"
```

---

### Task 5: 删除现有数据目录并重新初始化数据库

**Step 1: 删除 data 目录**

Run: `rm -rf data/`

**Step 2: 重新初始化数据库**

Run: `source myenv/bin/activate && python init_db.py`

Expected: 输出 "数据库表结构已重建" 和 "数据库初始化完成！"

---

### Task 6: 修改文件命名相关代码

**Files:**
- Modify: `routes/files.py`
- Modify: `utils/file_sync.py`

**Step 1: 修改 routes/files.py 的 get_model_info 函数**

找到 `get_model_info` 函数（约第63行），修改返回值：

```python
def get_model_info(model_type: str, model_id: int) -> dict:
    """
    获取模型的基本信息用于文件命名

    Args:
        model_type: 模型类型
        model_id: 模型ID

    Returns:
        包含 brand_abbreviation 和 item_number 的字典
    """
    model = get_model_by_type(model_type, model_id)
    if not model:
        return None

    brand = db.session.get(Brand, model.brand_id)
    if not brand:
        return None

    return {
        'brand_abbreviation': brand.abbreviation,
        'item_number': model.item_number
    }
```

**Step 2: 修改 routes/files.py 的 generate_filename 函数**

找到 `generate_filename` 函数（约第83行），更新参数名和逻辑：

```python
def generate_filename(file_type: str, brand_abbreviation: str, item_number: str,
                      original_filename: str = None) -> str:
    """
    生成标准化的文件名

    Args:
        file_type: 文件类型 (image/function_table/manual)
        brand_abbreviation: 品牌缩写
        item_number: 货号
        original_filename: 原始文件名（用于说明书）

    Returns:
        生成的文件名
    """
    safe_brand = secure_filename(brand_abbreviation)
    safe_item = secure_filename(item_number)
    base_name = f"{safe_brand}_{safe_item}"

    if file_type == 'image':
        # 图片：品牌_货号.扩展名
        ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'jpg'
        return f"{base_name}.{ext}"

    elif file_type == 'function_table':
        # 功能表：品牌_货号_FunctionKey.扩展名
        ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'pdf'
        return f"{base_name}_FunctionKey.{ext}"

    elif file_type == 'manual':
        # 说明书：品牌_货号_Manual_原文件名.扩展名
        safe_original = secure_filename(original_filename)
        return f"{base_name}_Manual_{safe_original}"

    return original_filename
```

**Step 3: 修改 routes/files.py 的 upload_file 函数调用部分**

找到 `upload_file` 函数中调用 `generate_filename` 和 `get_model_folder_path` 的地方（约第166-175行），更新变量名：

```python
    brand_abbreviation = model_info['brand_abbreviation']
    item_number = model_info['item_number']

    # 检查是否需要覆盖旧文件
    if file_type in ['image', 'function_table']:
        existing_file = ModelFile.query.filter_by(
            model_type=model_type,
            model_id=model_id,
            file_type=file_type
        ).first()

    new_filename = generate_filename(file_type, brand_abbreviation, item_number, file.filename)

    # 确保文件夹存在
    folder_path = get_model_folder_path(model_type, brand_abbreviation, item_number)
```

**Step 4: 修改 routes/files.py 的 ModelFile 创建部分**

找到创建 ModelFile 的地方（约第217行），更新：

```python
    relative_path = os.path.join(model_type, f"{brand_abbreviation}_{item_number}", new_filename)
```

**Step 5: 修改 utils/file_sync.py 的 get_model_folder_path 函数**

找到 `get_model_folder_path` 函数（约第280行），修改参数：

```python
def get_model_folder_path(model_type: str, brand_abbreviation: str, item_number: str) -> str:
    """
    获取模型文件存储路径

    Args:
        model_type: 模型类型
        brand_abbreviation: 品牌缩写
        item_number: 货号

    Returns:
        文件夹绝对路径
    """
    data_dir = current_app.config.get('DATA_DIR', 'data')
    folder_name = f"{brand_abbreviation}_{item_number}"
    return os.path.join(data_dir, model_type, folder_name)
```

**Step 6: 修改 utils/file_sync.py 的 rename_model_folder 函数**

找到 `rename_model_folder` 函数（约第315行），修改参数：

```python
def rename_model_folder(model_type: str, old_brand_abbreviation: str, old_item_number: str,
                        new_brand_abbreviation: str, new_item_number: str) -> bool:
    """
    重命名模型文件夹（当品牌或货号变更时）

    Args:
        model_type: 模型类型
        old_brand_abbreviation: 旧品牌缩写
        old_item_number: 旧货号
        new_brand_abbreviation: 新品牌缩写
        new_item_number: 新货号

    Returns:
        是否成功重命名
    """
    from werkzeug.utils import secure_filename

    # 如果品牌和货号都没变，无需重命名
    if old_brand_abbreviation == new_brand_abbreviation and old_item_number == new_item_number:
        return True

    old_folder_path = get_model_folder_path(model_type, old_brand_abbreviation, old_item_number)

    # 如果旧目录不存在，无需重命名
    if not os.path.exists(old_folder_path):
        return True

    new_folder_path = get_model_folder_path(model_type, new_brand_abbreviation, new_item_number)

    # 如果新旧路径相同，无需重命名
    if old_folder_path == new_folder_path:
        return True

    try:
        # 确保父目录存在
        parent_dir = os.path.dirname(new_folder_path)
        os.makedirs(parent_dir, exist_ok=True)

        # 如果新目录已存在，先删除（这种情况不应该发生，但做保护）
        if os.path.exists(new_folder_path):
            import shutil
            shutil.rmtree(new_folder_path)

        # 重命名目录
        os.rename(old_folder_path, new_folder_path)

        # 重命名目录内的文件
        old_base = f"{secure_filename(old_brand_abbreviation)}_{secure_filename(old_item_number)}"
        new_base = f"{secure_filename(new_brand_abbreviation)}_{secure_filename(new_item_number)}"

        for filename in os.listdir(new_folder_path):
            old_file_path = os.path.join(new_folder_path, filename)
            if os.path.isfile(old_file_path):
                # 替换文件名中的基础部分
                new_filename = filename.replace(old_base, new_base, 1)
                if new_filename != filename:
                    new_file_path = os.path.join(new_folder_path, new_filename)
                    os.rename(old_file_path, new_file_path)

        current_app.logger.info(f"重命名文件夹: {old_folder_path} -> {new_folder_path}")
        return True
```

**Step 7: 修改 utils/file_sync.py 的 rename_model_files 函数**

找到 `rename_model_files` 函数（约第387行），修改参数：

```python
def rename_model_files(model_type: str,
                       old_brand_abbreviation: str, old_item_number: str,
                       new_brand_abbreviation: str, new_item_number: str) -> bool:
    """
    重命名数据库中的模型文件记录

    Args:
        model_type: 模型类型
        old_brand_abbreviation: 旧品牌缩写
        old_item_number: 旧货号
        new_brand_abbreviation: 新品牌缩写
        new_item_number: 新货号

    Returns:
        是否成功
    """
    from werkzeug.utils import secure_filename

    if old_brand_abbreviation == new_brand_abbreviation and old_item_number == new_item_number:
        return True

    # 获取该模型的所有文件
    files = ModelFile.query.filter_by(model_type=model_type).all()

    try:
        old_base = f"{secure_filename(old_brand_abbreviation)}_{secure_filename(old_item_number)}"
        new_base = f"{secure_filename(new_brand_abbreviation)}_{secure_filename(new_item_number)}"
```

**Step 8: 运行测试**

Run: `source myenv/bin/activate && pytest tests/test_files.py -v`

Expected: PASS

**Step 9: 提交**

```bash
git add routes/files.py utils/file_sync.py
git commit -m "feat: update file naming to use brand abbreviation"
```

---

### Task 7: 修改品牌 CRUD 接口

**Files:**
- Modify: `routes/options.py`

**Step 1: 修改品牌添加接口**

找到品牌添加的工厂函数调用部分，确保 abbreviation 字段被处理：

在 `routes/options.py` 中找到品牌相关的路由，确保添加和编辑时处理 abbreviation 字段。

**Step 2: 运行测试**

Run: `source myenv/bin/activate && pytest tests/test_options.py -v`

Expected: 可能需要更新测试

**Step 3: 提交**

```bash
git add routes/options.py
git commit -m "feat: update brand CRUD to handle abbreviation field"
```

---

### Task 8: 更新前端页面

**Files:**
- Modify: `templates/options.html`
- Modify: `static/js/options.js`

**Step 1: 修改 options.html 品牌表格**

在品牌表格中添加缩写列：

找到品牌标签页的表格部分，添加缩写列头和数据显示：

```html
<th>名称</th>
<th>缩写</th>
<th>官网</th>
<th>搜索URL</th>
```

以及在数据行中：
```html
<td class="editable" data-field="name">{{ brand.name }}</td>
<td class="editable" data-field="abbreviation">{{ brand.abbreviation }}</td>
```

**Step 2: 修改 options.js 添加缩写自动生成逻辑**

在 `static/js/options.js` 中添加缩写生成函数和事件处理：

```javascript
/**
 * 生成品牌缩写
 * @param {string} name - 品牌名称
 * @returns {string} - 生成的缩写
 */
function generateAbbreviation(name) {
  if (!name) return '';

  // 检查是否包含中文
  const hasChinese = /[\u4e00-\u9fff]/.test(name);

  if (hasChinese) {
    // 中文：取拼音首字母（简化处理，实际需要后端支持）
    // 这里只做简单的客户端提示，实际生成由后端完成
    return name.split('').map(char => {
      if (/[\u4e00-\u9fff]/.test(char)) {
        return char; // 占位，后端会生成正确的缩写
      }
      return char;
    }).join('').toUpperCase().substring(0, 6);
  }

  // 检查是否是 camelCase 多词格式
  const words = name.match(/[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+/g) || [];

  if (words.length > 1) {
    // 多词：取每个词首字母
    return words.map(w => w[0]).join('').toUpperCase();
  }

  // 单词
  if (name.length <= 6) {
    return name.toUpperCase();
  } else {
    return name.substring(0, 3).toUpperCase();
  }
}

// 品牌名称输入时自动生成缩写建议
document.addEventListener('focusout', function(e) {
  if (e.target.matches('#brand-tab .editable[data-field="name"]')) {
    const row = e.target.closest('tr');
    const abbrCell = row.querySelector('.editable[data-field="abbreviation"]');
    if (abbrCell && !abbrCell.textContent.trim()) {
      // 只有缩写为空时才自动填充
      abbrCell.textContent = generateAbbreviation(e.target.textContent.trim());
    }
  }
});
```

**Step 3: 提交**

```bash
git add templates/options.html static/js/options.js
git commit -m "feat: add abbreviation field to brand management UI"
```

---

### Task 9: 更新测试用例

**Files:**
- Modify: `tests/test_options.py`

**Step 1: 更新品牌测试用例**

在品牌相关的测试中添加 abbreviation 字段的测试：

```python
class TestBrandOptions:
    """品牌选项测试"""

    def test_brand_list_page(self, client):
        """测试品牌列表页面"""
        response = client.get('/options/')
        assert response.status_code == 200

    def test_brand_add(self, client, app):
        """测试添加品牌"""
        response = client.post('/options/brand/add', data={
            'name': '测试品牌',
            'abbreviation': 'CSPP',  # 新增缩写
            'website': '',
            'search_url': ''
        }, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            brand = Brand.query.filter_by(name='测试品牌').first()
            assert brand is not None
            assert brand.abbreviation == 'CSPP'

    def test_brand_add_with_auto_abbreviation(self, client, app):
        """测试添加品牌时自动生成缩写"""
        response = client.post('/options/brand/add', data={
            'name': '新品牌',
            'abbreviation': '',  # 空缩写，后端应自动生成
            'website': '',
            'search_url': ''
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_brand_abbreviation_unique(self, client, app):
        """测试缩写唯一性"""
        # 先添加一个品牌
        client.post('/options/brand/add', data={
            'name': '品牌A',
            'abbreviation': 'PPA',
            'website': '',
            'search_url': ''
        }, follow_redirects=True)

        # 尝试添加另一个品牌但使用相同缩写
        response = client.post('/options/brand/add', data={
            'name': '品牌B',
            'abbreviation': 'PPA',  # 重复的缩写
            'website': '',
            'search_url': ''
        }, follow_redirects=True)
        # 应该返回错误
        assert b'\xe5\x94\xaf\xe4\xb8\x80' in response.data or response.status_code == 400
```

**Step 2: 运行所有测试**

Run: `source myenv/bin/activate && pytest -v`

Expected: PASS

**Step 3: 提交**

```bash
git add tests/test_options.py tests/test_helpers.py
git commit -m "test: add tests for brand abbreviation"
```

---

### Task 10: 更新文档

**Files:**
- Modify: `docs/design/Train-Model-Manager-Implementation.md`
- Modify: `CLAUDE.md`

**Step 1: 更新实现文档**

在 `docs/design/Train-Model-Manager-Implementation.md` 中更新数据模型部分，添加 Brand 的 abbreviation 字段说明。

**Step 2: 更新 CLAUDE.md**

在 `CLAUDE.md` 的核心数据模型部分更新 Brand 表说明：

```markdown
| 表名 | 说明 |
|-----|------|
| brand | 品牌 - 所有模型共享，包含缩写字段用于文件命名 |
```

**Step 3: 提交**

```bash
git add docs/design/Train-Model-Manager-Implementation.md CLAUDE.md
git commit -m "docs: update documentation for brand abbreviation"
```

---

### Task 11: 最终验证

**Step 1: 运行完整测试套件**

Run: `source myenv/bin/activate && pytest -v`

Expected: All tests PASS

**Step 2: 启动应用手动测试**

Run: `source myenv/bin/activate && python app.py`

测试项目：
1. 访问信息维护页面，查看品牌列表是否显示缩写
2. 添加新品牌，验证缩写自动生成
3. 上传模型文件，验证文件名使用缩写
4. 查看模型详情，验证文件正常显示

**Step 3: 最终提交（如果有遗漏的文件）**

```bash
git status
git add -A
git commit -m "feat: complete brand abbreviation feature"
```

---

## 预置品牌缩写对照表

| 品牌名 | 缩写 |
|-------|------|
| 1435 | 1435 |
| ATHEARN | ATH |
| BLI | BLI |
| CMR | CMR |
| PIKO | PIKO |
| ROCO | ROCO |
| TRIX | TRIX |
| 百万城 | BWC |
| 浩瀚 | HH |
| 深东 | SD |
| 猩猩 | XX |
| 长鸣 | CM |
| 跨越 | KY |
| Kunter | KUNTER |
| 茂杉 | MS |
| KATO | KATO |
| HCMX | HCMX |
| HTMX | HTMX |
| KukePig | KP |
| N27 | N27 |
| 毫米制造 | MMZZ |
| 火车花园 | HCHY |
| 曙光 | SG |
| WALTHERS | WAL |
| Tomix | TOM |
| 微景 | WJ |
| ARNOLD | ARN |
| Fleischmann | FLE |
| MicroAce | MIC |
