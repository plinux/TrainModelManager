"""
前端代码质量测试

验证 JavaScript 文件语法正确性和模板渲染质量，
确保前端代码在服务端渲染层面没有结构性错误。
"""

import re
import subprocess
import json


class TestJavaScriptSyntax:
    """验证所有 JS 文件语法正确，防止因语法错误导致页面功能失效"""

    JS_FILES = [
        'static/js/app.js',
        'static/js/options.js',
        'static/js/system.js',
    ]

    # utils.js 已拆分为 7 个核心模块，按依赖顺序排列
    CORE_JS_FILES = [
        'static/js/core/modal.js',
        'static/js/core/api.js',
        'static/js/core/dropdowns.js',
        'static/js/core/tables.js',
        'static/js/core/forms.js',
        'static/js/core/file_manager.js',
        'static/js/core/compat.js',
    ]

    # custom-import.js 已拆分为 6 个模块，按依赖顺序加载
    IMPORT_JS_FILES = [
        'static/js/import/wizard_core.js',
        'static/js/import/utils.js',
        'static/js/import/file_step.js',
        'static/js/import/sheet_mapping.js',
        'static/js/import/column_mapping.js',
        'static/js/import/preview_step.js',
    ]

    def _validate_js_syntax(self, filepath):
        """使用 node --check 验证 JS 文件语法"""
        result = subprocess.run(
            ['node', '--check', filepath],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f'{filepath} 语法错误:\n{result.stderr}'
        )

    def test_app_js_syntax(self):
        """app.js 语法正确"""
        self._validate_js_syntax('static/js/app.js')

    def test_options_js_syntax(self):
        """options.js 语法正确"""
        self._validate_js_syntax('static/js/options.js')

    def test_system_js_syntax(self):
        """system.js 语法正确"""
        self._validate_js_syntax('static/js/system.js')

    def test_import_modules_syntax(self):
        """所有 import/* 模块语法正确"""
        for filepath in self.IMPORT_JS_FILES:
            self._validate_js_syntax(filepath)

    def test_core_modules_syntax(self):
        """所有 core/* 模块语法正确"""
        for filepath in self.CORE_JS_FILES:
            self._validate_js_syntax(filepath)


class TestJsObjectIntPages:
    """验证关键 JS 全局对象在页面中可被正确引用

    通过检查模板中 inline script 引用的全局对象确实存在于对应的 JS 文件中。
    这确保模板不会引用不存在的函数或对象。
    """

    # utils.js 已拆分为 7 个 core/* 模块
    CORE_FILES = [
        'static/js/core/modal.js',
        'static/js/core/api.js',
        'static/js/core/dropdowns.js',
        'static/js/core/tables.js',
        'static/js/core/forms.js',
        'static/js/core/file_manager.js',
        'static/js/core/compat.js',
    ]

    def _read_js_file(self, filepath):
        """读取 JS 文件内容"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_template(self, filepath):
        """读取模板文件内容"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_all_core_js(self):
        """读取所有 core 模块拼接后的内容（用于跨模块断言）"""
        return '\n'.join(self._read_js_file(p) for p in self.CORE_FILES)

    def _assert_js_object_exists(self, js_content, object_name):
        """验证 JS 文件中定义了指定全局对象"""
        # 匹配 const XXX = { 或 function XXX( 或 var XXX =
        patterns = [
            f'const {object_name} = ',
            f'function {object_name}(',
            f'var {object_name} = ',
        ]
        found = any(p in js_content for p in patterns)
        assert found, f'JS 全局对象 "{object_name}" 未在 core 模块中找到定义'

    # --- core 模块中的全局对象 ---

    def test_modal_manager_exists(self):
        """ModalManager 对象存在于 core/modal.js"""
        js = self._read_js_file('static/js/core/modal.js')
        assert 'const ModalManager' in js

    def test_utils_object_exists(self):
        """Utils 对象存在于 core/api.js"""
        js = self._read_js_file('static/js/core/api.js')
        assert 'const Utils' in js

    def test_api_object_exists(self):
        """Api 对象存在于 core/api.js"""
        js = self._read_js_file('static/js/core/api.js')
        assert 'const Api' in js

    def test_form_helper_exists(self):
        """FormHelper 对象存在于 core/forms.js"""
        js = self._read_js_file('static/js/core/forms.js')
        assert 'const FormHelper' in js

    def test_carriage_manager_exists(self):
        """CarriageManager 对象存在于 core/forms.js"""
        js = self._read_js_file('static/js/core/forms.js')
        assert 'const CarriageManager' in js

    def test_light_dropdown_manager_exists(self):
        """LightDropdownManager 对象存在于 core/dropdowns.js"""
        js = self._read_js_file('static/js/core/dropdowns.js')
        assert 'const LightDropdownManager' in js

    def test_model_form_exists(self):
        """ModelForm 对象存在于 core/forms.js"""
        js = self._read_js_file('static/js/core/forms.js')
        assert 'const ModelForm' in js

    def test_table_manager_exists(self):
        """TableManager 对象存在于 core/tables.js"""
        js = self._read_js_file('static/js/core/tables.js')
        assert 'const TableManager' in js

    def test_autocomplete_manager_exists(self):
        """AutocompleteManager 对象存在于 core/dropdowns.js"""
        js = self._read_js_file('static/js/core/dropdowns.js')
        assert 'const AutocompleteManager' in js

    def test_form_filler_exists(self):
        """FormFiller 对象存在于 core/forms.js"""
        js = self._read_js_file('static/js/core/forms.js')
        assert 'const FormFiller' in js

    def test_file_manager_exists(self):
        """FileManager 对象存在于 core/file_manager.js"""
        js = self._read_js_file('static/js/core/file_manager.js')
        assert 'const FileManager' in js

    def test_core_objects_window_exposed(self):
        """所有 core 对象通过 global.XXX = XXX 暴露到 window"""
        # 每个对象都应在其所在模块的 IIFE 末尾被显式挂到 window
        object_to_module = [
            ('ModalManager', 'static/js/core/modal.js'),
            ('Utils', 'static/js/core/api.js'),
            ('Api', 'static/js/core/api.js'),
            ('FormHelper', 'static/js/core/forms.js'),
            ('CarriageManager', 'static/js/core/forms.js'),
            ('LightDropdownManager', 'static/js/core/dropdowns.js'),
            ('ModelForm', 'static/js/core/forms.js'),
            ('TableManager', 'static/js/core/tables.js'),
            ('AutocompleteManager', 'static/js/core/dropdowns.js'),
            ('FormFiller', 'static/js/core/forms.js'),
            ('FileManager', 'static/js/core/file_manager.js'),
        ]
        for obj, path in object_to_module:
            js = self._read_js_file(path)
            assert f'global.{obj} = {obj}' in js, (
                f'对象 "{obj}" 未在 {path} 中通过 global.{obj} = {obj} 暴露'
            )

    # --- 兼容函数 ---

    def test_global_compat_functions(self):
        """全局兼容函数存在于 core/compat.js"""
        js = self._read_js_file('static/js/core/compat.js')
        compat_functions = [
            'filterLocomotiveModelsBySeries',
            'filterTrainsetModelsBySeries',
            'handleLocomotiveSeriesChange',
            'handleTrainsetSeriesChange',
            'autoFillLocomotive',
            'autoFillTrainset',
            'addCarriageRow',
            'removeCarriageRow',
            'handleSeriesChange',
            'showTab',
            'submitFormAjax',
            'filterModelsBySeries',
            'generateSeriesOptions',
            'initTableSortFilter',
            'resetTable',
            'initAutocomplete',
            'setAutocompleteOptions',
            'setAutocompleteValue',
            'copyLocomotive',
            'copyTrainset',
            'copyLocomotiveHead',
            'copyCarriage',
            'searchProduct',
            'uploadModelFile',
        ]
        for func_name in compat_functions:
            assert f'function {func_name}' in js, (
                f'全局兼容函数 "{func_name}" 未在 core/compat.js 中找到'
            )

    def test_compat_functions_window_exposed(self):
        """所有兼容函数通过 global.XXX = XXX 显式挂到 window"""
        js = self._read_js_file('static/js/core/compat.js')
        compat_functions = [
            'filterLocomotiveModelsBySeries',
            'filterTrainsetModelsBySeries',
            'handleLocomotiveSeriesChange',
            'handleTrainsetSeriesChange',
            'autoFillLocomotive',
            'autoFillTrainset',
            'addCarriageRow',
            'removeCarriageRow',
            'handleSeriesChange',
            'showTab',
            'submitFormAjax',
            'filterModelsBySeries',
            'generateSeriesOptions',
            'initTableSortFilter',
            'resetTable',
            'initAutocomplete',
            'setAutocompleteOptions',
            'setAutocompleteValue',
            'copyLocomotive',
            'copyTrainset',
            'copyLocomotiveHead',
            'copyCarriage',
            'searchProduct',
            'uploadModelFile',
        ]
        for func_name in compat_functions:
            assert f'global.{func_name} = {func_name}' in js, (
                f'兼容函数 "{func_name}" 未显式挂到 window'
            )

    # --- 模板中引用的关键函数 ---

    def test_template_button_handlers(self):
        """模板中 onclick 引用的函数在 core 模块中都有定义"""
        js = self._read_all_core_js()
        templates = [
            'templates/locomotive.html',
            'templates/trainset.html',
            'templates/locomotive_head.html',
            'templates/carriage.html',
        ]
        for template_path in templates:
            template = self._read_template(template_path)
            # 找所有 onclick="functionName 引用
            import re
            onclick_funcs = re.findall(r'onclick="(\w+)"', template)
            onclick_funcs += re.findall(r"onclick='(\w+)'", template)
            for match in onclick_funcs:
                # 提取函数名
                func_match = re.search(r'(\w+)\(', match)
                if func_match:
                    # 处理带参数的调用如 searchProduct(this, ..., ...)
                    func_name = re.match(r'^(\w+)', func_match).group(1)
                    if func_name:
                        # 验证该函数或对象在 JS 中存在
                        assert func_name in js, (
                            f'模板 {template_path} 引用的函数 "{func_name}" '
                            f'在 core 模块中未找到定义'
                        )


class TestTemplateRendering:
    """验证模板渲染的关键 HTML 结构"""

    def _get_page_html(self, client, url):
        """获取页面 HTML 内容"""
        response = client.get(url)
        assert response.status_code == 200
        return response.get_data(as_text=True)

    # --- 机车页面 ---

    def test_locomotive_page_structure(self, client, sample_data):
        """机车页面包含表格和模态框"""
        html = self._get_page_html(client, '/locomotive')
        assert 'id="locomotive-table"' in html
        assert 'id="locomotive-modal"' in html
        assert 'id="locomotive-form"' in html

    def test_locomotive_table_data_attributes(self):
        """机车模板行包含必要的 data 属性 Jinja2 语法"""
        with open('templates/locomotive.html', 'r', encoding='utf-8') as f:
            template = f.read()
        assert 'data-model_type="locomotive"' in template
        assert 'data-model_id=' in template

    def test_locomotive_modal_form_fields(self, client, sample_data):
        """机车模态框表单包含所有必填字段"""
        html = self._get_page_html(client, '/locomotive')
        required_fields = [
            'name="series_id"',
            'name="model_id"',
            'name="power_type_id"',
            'name="locomotive_number"',
            'name="brand_id"',
            'name="scale"',
        ]
        for field in required_fields:
            assert field in html, f'机车表单缺少字段: {field}'

    # --- 动车组页面 ---

    def test_trainset_page_structure(self, client, sample_data):
        """动车组页面包含表格、模态框和灯型号下拉"""
        html = self._get_page_html(client, '/trainset')
        assert 'id="trainset-table"' in html
        assert 'id="trainset-modal"' in html
        assert 'id="trainset-form"' in html

    def test_trainset_light_model_dropdown(self, client, sample_data):
        """动车组表单包含灯型号下拉组件"""
        html = self._get_page_html(client, '/trainset')
        assert 'id="light_model_id_text"' in html
        assert 'id="light_model_id"' in html
        assert 'name="light_model_id"' in html

    def test_trainset_table_light_model_data(self):
        """动车组模板行包含灯型号 data 属性 Jinja2 语法"""
        with open('templates/trainset.html', 'r', encoding='utf-8') as f:
            template = f.read()
        assert 'data-light_model_id=' in template
        assert 'data-light_model_name=' in template

    # --- 先头车页面 ---

    def test_locomotive_head_page_structure(self, client, sample_data):
        """先头车页面包含表格、模态框和灯型号下拉"""
        html = self._get_page_html(client, '/locomotive-head')
        assert 'id="locomotive-head-table"' in html
        assert 'id="locomotive-head-modal"' in html

    def test_locomotive_head_light_model_dropdown(self, client, sample_data):
        """先头车表单包含灯型号下拉组件"""
        html = self._get_page_html(client, '/locomotive-head')
        assert 'id="light_model_id_text"' in html
        assert 'id="light_model_id"' in html

    # --- 车厢页面 ---

    def test_carriage_page_structure(self, client, sample_data):
        """车厢页面包含表格和模态框"""
        html = self._get_page_html(client, '/carriage')
        assert 'id="carriage-table"' in html
        assert 'id="carriage-modal"' in html

    def test_carriage_add_button(self, client, sample_data):
        """车厢页面有添加车厢按钮"""
        html = self._get_page_html(client, '/carriage')
        assert 'addCarriageRow' in html

    # --- 信息维护页面 ---

    def test_options_page_structure(self, client, sample_data):
        """信息维护页面包含标签页和灯型号区域"""
        html = self._get_page_html(client, '/options')
        assert 'id="light_models"' in html

    def test_options_light_model_scale_field(self, client, sample_data):
        """信息维护页面灯型号表单包含 scale 选择框"""
        html = self._get_page_html(client, '/options')
        assert 'name="scale"' in html
        # 验证有 HO 和 N 选项
        assert '<option value="HO"' in html
        assert '<option value="N"' in html

    # --- 首页 ---

    def test_index_page_structure(self, client, sample_data):
        """首页包含统计区域"""
        html = self._get_page_html(client, '/')
        assert 'class="stats-tabs"' in html or 'class="stats-tab"' in html


class TestTemplateInlineScripts:
    """验证模板 inline script 中引用的关键函数和对象正确"""

    def _extract_inline_script(self, template_path):
        """提取模板中 <script> 块的内容"""
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 提取 {% block scripts %} 后的内容
        import re
        match = re.search(r'\{%\s*block\s+scripts\s+%\}(.*?)(?=\{%\s*endblock\s+%)', content, re.DOTALL)
        if match:
            return match.group(1)
        return ''

    def test_trainset_script_initializes_light_dropdown(self):
        """动车组模板初始化了 LightDropdownManager"""
        script = self._extract_inline_script('templates/trainset.html')
        assert 'LightDropdownManager.init' in script

    def test_locomotive_head_script_initializes_light_dropdown(self):
        """先头车模板初始化了 LightDropdownManager"""
        script = self._extract_inline_script('templates/locomotive_head.html')
        assert 'LightDropdownManager.init' in script

    def test_trainset_script_initializes_table_sort(self):
        """动车组模板初始化了表格排序"""
        script = self._extract_inline_script('templates/trainset.html')
        assert 'initTableSortFilter' in script

    def test_locomotive_head_script_initializes_table_sort(self):
        """先头车模板初始化了表格排序"""
        script = self._extract_inline_script('templates/locomotive_head.html')
        assert 'initTableSortFilter' in script

    def test_carriage_script_has_carriage_manager(self):
        """车厢模板引用了 CarriageManager"""
        script = self._extract_inline_script('templates/carriage.html')
        assert 'CarriageManager' in script


class TestFileManagerRenderAttributes:
    """验证 FileManager.renderAttributes 的 attributeNames 映射完整性

    确保 displayOrder 中的每个 key 在 attributeNames 中都有对应的中文显示名。
    这防止出现 key 不匹配导致属性显示为原始英文 key 的情况。
    """

    def _read_js_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_display_order(self, js_content):
        """从 JS 中提取 displayOrder 数组"""
        import re
        match = re.search(r"const displayOrder = \[(.*?)\]", js_content, re.DOTALL)
        assert match, 'displayOrder 未找到'
        raw = match.group(1)
        # 提取所有引号内的字符串
        keys = re.findall(r"'(\w+)'", raw)
        return keys

    def _extract_attribute_names(self, js_content):
        """从 JS 中提取 attributeNames 映射"""
        import re
        # 找到 attributeNames: { ... } 块
        match = re.search(r"attributeNames:\s*\{(.*?)\}", js_content, re.DOTALL)
        assert match, 'attributeNames 未找到'
        raw = match.group(1)
        # 提取所有 key: 'value' 对
        pairs = re.findall(r"'(\w+)':\s*'([^']*)'", raw)
        return dict(pairs)

    def test_all_display_order_keys_have_attribute_names(self):
        """displayOrder 中的每个 key 在 attributeNames 中都有映射"""
        js = self._read_js_file('static/js/core/file_manager.js')
        display_order = self._extract_display_order(js)
        attribute_names = self._extract_attribute_names(js)

        for key in display_order:
            assert key in attribute_names, (
                f'"{key}" 在 displayOrder 中但不在 attributeNames 中，'
                f'模型详情会显示原始 key 而非中文名'
            )

    def test_attribute_names_are_not_empty(self):
        """attributeNames 中的值都不为空"""
        js = self._read_js_file('static/js/core/file_manager.js')
        attribute_names = self._extract_attribute_names(js)

        for key, value in attribute_names.items():
            assert value.strip(), f'attributeNames["{key}"] 的值为空'

    def test_head_light_is_boolean_key(self):
        """head_light 在 displayOrder 中且为布尔处理"""
        js = self._read_js_file('static/js/core/file_manager.js')
        assert "'head_light'" in js
        # 验证布尔处理逻辑
        assert "key === 'head_light'" in js

    def test_light_model_is_name_key(self):
        """light_model（室内灯）在 displayOrder 中且为名称显示（非布尔）"""
        js = self._read_js_file('static/js/core/file_manager.js')
        display_order = self._extract_display_order(js)
        assert 'light_model' in display_order, (
            '"light_model" 不在 displayOrder 中'
        )
        # 确保没有被当作布尔值处理
        assert "key === 'interior_light'" not in js, (
            'interior_light 仍然出现在布尔处理逻辑中'
        )

    def test_purchase_date_handler_exists(self):
        """purchase_date 有专门的日期格式处理"""
        js = self._read_js_file('static/js/core/file_manager.js')
        assert "key === 'purchase_date'" in js

    def test_item_number_handler_exists(self):
        """item_number 有链接处理"""
        js = self._read_js_file('static/js/core/file_manager.js')
        assert "key === 'item_number'" in js
        # 确保没有重复的 item_number 分支
        count = js.count("key === 'item_number'")
        assert count == 1, (
            f'item_number 分支出现了 {count} 次，应该只出现 1 次'
        )

    def test_no_interior_light_references(self):
        """renderAttributes 中不应再引用 interior_light"""
        js = self._read_js_file('static/js/core/file_manager.js')
        # 在 attributeNames 和 displayOrder 区域检查
        attribute_names = self._extract_attribute_names(js)
        display_order = self._extract_display_order(js)
        assert 'interior_light' not in attribute_names, (
            'attributeNames 中仍包含 interior_light'
        )
        assert 'interior_light' not in display_order, (
            'displayOrder 中仍包含 interior_light'
        )


class TestJsDuplicateCodeCheck:
    """检查 JS 代码中的重复分支（正是导致此次 bug 的原因）

    如果 if/else if 链中出现连续两个完全相同的条件，说明有重复代码。
    """

    def _read_js_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _check_no_duplicate_else_if_branches(self, js_content):
        """检查所有 else if 链中没有重复条件"""
        import re
        # 找所有 else if (key === 'XXX') 或 if (key === 'XXX') 模式
        # 只检查包含比较运算符的分支（排除 if (variable) 这类真值检查）
        comparison_ops = ['===', '!==', '==', '!=', '>=', '<=', '>', '<']
        lines = js_content.split('\n')
        current_chain = []
        chains = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('if ') or stripped.startswith('else if '):
                current_chain.append(stripped)
            elif stripped.startswith('else ') or stripped == '}':
                if len(current_chain) > 1:
                    chains.append(current_chain[:])
                if stripped.startswith('else '):
                    current_chain = [stripped]
                else:
                    current_chain = []
            elif stripped == '' and current_chain:
                if len(current_chain) > 1:
                    chains.append(current_chain[:])
                current_chain = []

        for chain in chains:
            conditions = []
            for cond in chain:
                match = re.search(r"(?:else\s+)?if\s*\((.+)\)", cond)
                if match:
                    condition = match.group(1).strip()
                    # 只检查包含比较运算符的条件
                    if any(op in condition for op in comparison_ops):
                        conditions.append(condition)
            if len(conditions) != len(set(conditions)):
                dupes = [c for c in conditions if conditions.count(c) > 1]
                assert False, (
                    f'发现重复的条件分支: {set(dupes)}'
                )

    def test_core_modules_no_duplicate_branches(self):
        """core/* 模块中没有重复的 if/else if 条件"""
        # 检查所有 core 模块（utils.js 已拆分）
        core_files = [
            'static/js/core/modal.js',
            'static/js/core/api.js',
            'static/js/core/dropdowns.js',
            'static/js/core/tables.js',
            'static/js/core/forms.js',
            'static/js/core/file_manager.js',
            'static/js/core/compat.js',
        ]
        for path in core_files:
            js = self._read_js_file(path)
            self._check_no_duplicate_else_if_branches(js)

    def test_options_no_duplicate_branches(self):
        """options.js 中没有重复的 if/else if 条件"""
        js = self._read_js_file('static/js/options.js')
        self._check_no_duplicate_else_if_branches(js)

    def test_system_no_duplicate_branches(self):
        """system.js 中没有重复的 if/else if 条件"""
        js = self._read_js_file('static/js/system.js')
        self._check_no_duplicate_else_if_branches(js)

    def test_custom_import_no_duplicate_branches(self):
        """import/* 模块中没有重复的 if/else if 条件"""
        # custom-import.js 已拆分为 6 个模块，逐一检查
        for filepath in [
            'static/js/import/wizard_core.js',
            'static/js/import/utils.js',
            'static/js/import/file_step.js',
            'static/js/import/sheet_mapping.js',
            'static/js/import/column_mapping.js',
            'static/js/import/preview_step.js',
        ]:
            js = self._read_js_file(filepath)
            self._check_no_duplicate_else_if_branches(js)
