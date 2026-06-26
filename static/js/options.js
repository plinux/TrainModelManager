/**
 * 信息维护页面 JavaScript 模块
 */

/**
 * 生成品牌缩写（客户端预览）
 * @param {string} name - 品牌名称
 * @returns {string} - 生成的缩写建议
 */
function generateAbbreviation(name) {
  if (!name) return '';

  // 检查是否包含中文
  const hasChinese = /[\u4e00-\u9fff]/.test(name);

  if (hasChinese) {
    // 中文：提示用户后端会自动生成，返回占位符
    return name.length <= 6 ? name.toUpperCase() : name.substring(0, 3).toUpperCase();
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

// 选项编辑管理
const OptionEditor = {
  // 存储原始值，用于取消编辑时恢复
  originalValues: {},

  /**
   * 编辑行
   * @param {HTMLElement} button - 编辑按钮
   */
  editRow(button) {
    const row = button.closest('tr');
    const fieldType = row.dataset.type;

    // 切换按钮显示
    button.style.display = 'none';
    row.querySelector('.btn-save').style.display = 'inline-block';
    row.querySelector('.btn-cancel').style.display = 'inline-block';
    row.querySelector('.btn-danger').style.display = 'none';

    // 存储原始值
    row.querySelectorAll('[data-field]').forEach(cell => {
      const fieldName = cell.dataset.field;
      this.originalValues[fieldName] = cell.textContent.trim();
    });

    // 获取字段列表
    const fields = row.dataset.fields.split(',');

    // 为每个字段创建编辑控件
    fields.forEach(field => {
      this.createEditControl(row, field);
    });
  },

  /**
   * 创建编辑控件
   * @param {HTMLElement} row - 表格行
   * @param {string} field - 字段名
   */
  createEditControl(row, field) {
    const cell = row.querySelector(`[data-field="${field}"]`);

    if (field === 'name') {
      const originalValue = this.originalValues[field];
      const input = document.createElement('input');
      input.type = 'text';
      input.name = field;
      input.value = originalValue;
      input.style.cssText = 'width:100%; padding:0.25rem 0.5rem;';
      cell.textContent = '';
      cell.appendChild(input);
    } else if (field === 'series_id' || field === 'power_type_id' || field === 'type') {
      const addFormSelect = row.closest('.tab-content').querySelector(`select[name="${field}"]`);
      if (addFormSelect) {
        const select = document.createElement('select');
        select.name = field;
        select.style.cssText = 'width:100%; padding:0.25rem 0.5rem;';
        const dataAttr = field === 'type' ? 'carriageType' : field.replace('_id', '');
        const originalValue = row.dataset[dataAttr] || '';
        addFormSelect.querySelectorAll('option').forEach(opt => {
          const option = document.createElement('option');
          option.value = opt.value;
          option.textContent = opt.textContent;
          if (opt.value === originalValue) {
            option.selected = true;
          }
          select.appendChild(option);
        });
        cell.textContent = '';
        cell.appendChild(select);
      }
    } else if (field === 'website' || field === 'search_url') {
      const originalValue = this.originalValues[field] || '';
      const input = document.createElement('input');
      input.type = 'text';
      input.name = field;
      input.value = originalValue;
      input.style.cssText = 'width:100%; padding:0.25rem 0.5rem;';
      input.placeholder = '可选';
      cell.textContent = '';
      cell.appendChild(input);
    } else if (field === 'abbreviation') {
      const originalValue = this.originalValues[field] || '';
      const input = document.createElement('input');
      input.type = 'text';
      input.name = field;
      input.value = originalValue;
      input.style.cssText = 'width:100%; padding:0.25rem 0.5rem;';
      input.placeholder = '留空自动生成';
      input.maxLength = 20;
      cell.textContent = '';
      cell.appendChild(input);
    } else if (field === 'scale') {
      const originalValue = row.dataset.scale || 'HO';
      const select = document.createElement('select');
      select.name = field;
      select.style.cssText = 'width:100%; padding:0.25rem 0.5rem;';
      ['HO', 'N'].forEach(val => {
        const option = document.createElement('option');
        option.value = val;
        option.textContent = val;
        if (val === originalValue) option.selected = true;
        select.appendChild(option);
      });
      cell.textContent = '';
      cell.appendChild(select);
    } else if (field === 'interface_ids') {
      // 芯片型号-接口多对多：生成多选下拉菜单
      const selectedIds = (row.dataset.interface_ids || '').split(',').filter(Boolean).map(Number);
      const interfaces = window.chipInterfaces || [];
      const wrapper = document.createElement('div');
      wrapper.className = 'multi-select';
      wrapper.dataset.name = 'interface_ids';

      // 触发器
      const trigger = document.createElement('div');
      trigger.className = 'multi-select-trigger';
      trigger.onclick = function() { MultiSelect.toggle(this); };
      const tagsSpan = document.createElement('span');
      tagsSpan.className = 'multi-select-tags';
      const selected = interfaces.filter(i => selectedIds.includes(i.id));
      if (selected.length > 0) {
        selected.forEach(s => {
          const tag = document.createElement('span');
          tag.className = 'multi-select-tag';
          tag.textContent = s.name;
          tagsSpan.appendChild(tag);
        });
      } else {
        const ph = document.createElement('span');
        ph.className = 'multi-select-placeholder';
        ph.textContent = '选择接口';
        tagsSpan.appendChild(ph);
      }
      trigger.appendChild(tagsSpan);

      // 下拉面板
      const dropdown = document.createElement('div');
      dropdown.className = 'multi-select-dropdown';
      interfaces.forEach(iface => {
        const label = document.createElement('label');
        label.className = 'multi-select-option';
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.name = 'interface_ids';
        cb.value = iface.id;
        if (selectedIds.includes(iface.id)) cb.checked = true;
        cb.onchange = function() { MultiSelect.updateTrigger(this); };
        label.appendChild(cb);
        label.appendChild(document.createTextNode(iface.name));
        dropdown.appendChild(label);
      });

      wrapper.appendChild(trigger);
      wrapper.appendChild(dropdown);
      cell.textContent = '';
      cell.appendChild(wrapper);
    }
  },

  /**
   * 保存行
   * @param {HTMLElement} button - 保存按钮
   * @param {string} type - 选项类型
   */
  saveRow(button, type) {
    const row = button.closest('tr');
    const id = row.dataset.id;

    // 收集数据
    const formData = new FormData();
    formData.append('id', id);

    const fields = row.dataset.fields.split(',');
    fields.forEach(field => {
      if (field === 'interface_ids') {
        // checkbox 多选：收集所有选中的 checkbox
        const checkboxes = row.querySelectorAll('input[name="interface_ids"]:checked');
        checkboxes.forEach(cb => {
          formData.append('interface_ids', cb.value);
        });
      } else {
        const input = row.querySelector(`[name="${field}"]`);
        if (input) {
          const value = input.value;
          if (field === 'carriage_type') {
            formData.append('type', value);
          } else {
            formData.append(field, value);
          }
        }
      }
    });

    // 发送 AJAX 请求
    fetch(`/api/options/${type}/edit`, {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // 更新单元格显示
        this.updateCellDisplay(row, fields);
        // 清空原始值，避免被 cancelEdit 覆盖
        this.originalValues = {};
        // 恢复按钮状态
        this.restoreButtonState(row);
      } else {
        alert('保存失败: ' + (data.error || '未知错误'));
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('保存失败，请重试');
    });
  },

  /**
   * 更新单元格显示
   * @param {HTMLElement} row - 表格行
   * @param {Array} fields - 字段列表
   */
  updateCellDisplay(row, fields) {
    fields.forEach(field => {
      const cell = row.querySelector(`[data-field="${field}"]`);
      if (field === 'interface_ids') {
        // checkbox 组：收集选中项的名称
        const checkboxes = row.querySelectorAll('input[name="interface_ids"]:checked');
        const interfaces = window.chipInterfaces || [];
        const names = [];
        checkboxes.forEach(cb => {
          const iface = interfaces.find(i => i.id === Number(cb.value));
          if (iface) names.push(iface.name);
        });
        cell.textContent = names.join(', ') || '-';
        // 更新 data-interface_ids 属性（用于后续编辑）
        row.dataset.interface_ids = Array.from(checkboxes).map(cb => cb.value).join(',');
      } else {
        const input = row.querySelector(`[name="${field}"]`);
        if (input) {
          if (input.tagName === 'SELECT') {
            cell.textContent = input.options[input.selectedIndex].text;
          } else {
            cell.textContent = input.value;
          }
        }
      }
    });
  },

  /**
   * 恢复按钮状态
   * @param {HTMLElement} row - 表格行
   */
  restoreButtonState(row) {
    row.querySelector('.btn-edit').style.display = 'inline-block';
    row.querySelector('.btn-save').style.display = 'none';
    row.querySelector('.btn-cancel').style.display = 'none';
    row.querySelector('.btn-danger').style.display = 'inline-block';
  },

  /**
   * 取消编辑
   * @param {HTMLElement} button - 取消按钮
   */
  cancelEdit(button) {
    const row = button.closest('tr');

    // 恢复原始值
    Object.keys(this.originalValues).forEach(field => {
      const cell = row.querySelector(`[data-field="${field}"]`);
      if (cell) {
        cell.textContent = this.originalValues[field];
      }
    });

    // 清空原始值存储
    this.originalValues = {};

    // 恢复按钮状态
    this.restoreButtonState(row);
  }
};

// 删除操作
const DeleteHelper = {
  /**
   * 删除选项
   * @param {HTMLElement} button - 删除按钮
   * @param {string} type - 选项类型
   * @param {number} id - 选项ID
   * @param {string} deleteUrl - 删除URL
   */
  deleteItem(button, type, id, deleteUrl) {
    if (!confirm('确定要删除此项吗？')) {
      return;
    }

    fetch(deleteUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    })
    .then(response => {
      if (response.ok) {
        const row = button.closest('tr');
        row.remove();
      } else {
        alert('删除失败，请检查该项目是否正在使用');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('删除失败，请重试');
    });
  }
};

// 全局函数兼容
function editRow(button) {
  OptionEditor.editRow(button);
}

function saveRow(button, type) {
  OptionEditor.saveRow(button, type);
}

function cancelEdit(button) {
  OptionEditor.cancelEdit(button);
}

function deleteItem(button, type, id, deleteUrl) {
  DeleteHelper.deleteItem(button, type, id, deleteUrl);
}

// 品牌名称输入时自动生成缩写建议（在编辑模式下）
document.addEventListener('focusout', function(e) {
  if (e.target.matches('#brands .editable[data-field="name"] input, #brands [data-field="name"] input')) {
    const row = e.target.closest('tr');
    const abbrCell = row.querySelector('[data-field="abbreviation"] input');
    if (abbrCell && !abbrCell.value.trim()) {
      // 只有缩写为空时才自动填充建议
      abbrCell.value = generateAbbreviation(e.target.value.trim());
    }
  }
});

// 为所有可排序表格初始化排序功能
function initOptionsTableSort() {
  const tableIds = [
    'power_types-table',
    'brands-table',
    'merchants-table',
    'depots-table',
    'chip_interfaces-table',
    'chip_models-table',
    'locomotive_series-table',
    'locomotive_models-table',
    'carriage_series-table',
    'carriage_models-table',
    'trainset_series-table',
    'trainset_models-table',
    'light_brands-table',
    'light_models-table'
  ];

  tableIds.forEach(function(tableId) {
    if (typeof TableManager !== 'undefined') {
      TableManager.init(tableId);
    }
  });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  initOptionsTableSort();
  // 初始化页面中已有的多选下拉
  document.querySelectorAll('.multi-select-trigger').forEach(function(trigger) {
    var dropdown = trigger.nextElementSibling;
    if (dropdown) {
      dropdown.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
        cb.addEventListener('change', function() { MultiSelect.updateTrigger(this); });
      });
    }
  });
});

/**
 * 多选下拉组件
 */
var MultiSelect = {
  /**
   * 切换下拉面板的展开/收起
   * @param {HTMLElement} trigger - 触发器元素
   */
  toggle: function(trigger) {
    var wrapper = trigger.closest('.multi-select');
    var dropdown = wrapper.querySelector('.multi-select-dropdown');
    var isOpen = dropdown.classList.contains('show');

    // 先关闭所有已打开的多选下拉
    document.querySelectorAll('.multi-select-dropdown.show').forEach(function(d) {
      d.classList.remove('show');
      d.previousElementSibling.classList.remove('open');
    });

    if (!isOpen) {
      dropdown.classList.add('show');
      trigger.classList.add('open');
    }
  },

  /**
   * checkbox 状态变化后更新触发器显示
   * @param {HTMLElement} checkbox - 发生变化的 checkbox
   */
  updateTrigger: function(checkbox) {
    var wrapper = checkbox.closest('.multi-select');
    var trigger = wrapper.querySelector('.multi-select-trigger');
    var tagsSpan = trigger.querySelector('.multi-select-tags');
    var checkboxes = wrapper.querySelectorAll('input[type="checkbox"]');

    // 收集已选名称
    var selected = [];
    checkboxes.forEach(function(cb) {
      if (cb.checked) {
        var label = cb.closest('.multi-select-option');
        selected.push(label.textContent.trim());
      }
    });

    // 清空并重建
    while (tagsSpan.firstChild) tagsSpan.removeChild(tagsSpan.firstChild);
    if (selected.length > 0) {
      selected.forEach(function(name) {
        var tag = document.createElement('span');
        tag.className = 'multi-select-tag';
        tag.textContent = name;
        tagsSpan.appendChild(tag);
      });
    } else {
      var ph = document.createElement('span');
      ph.className = 'multi-select-placeholder';
      ph.textContent = '选择接口';
      tagsSpan.appendChild(ph);
    }
  }
};

// 点击外部关闭多选下拉
document.addEventListener('click', function(e) {
  if (!e.target.closest('.multi-select')) {
    document.querySelectorAll('.multi-select-dropdown.show').forEach(function(d) {
      d.classList.remove('show');
      d.previousElementSibling.classList.remove('open');
    });
  }
});
