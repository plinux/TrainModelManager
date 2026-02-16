/**
 * 选项维护页面 JavaScript 模块
 */

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
      const input = row.querySelector(`[name="${field}"]`);
      if (input) {
        const value = input.value;
        if (field === 'carriage_type') {
          formData.append('type', value);
        } else {
          formData.append(field, value);
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
      const input = row.querySelector(`[name="${field}"]`);
      if (input) {
        if (input.tagName === 'SELECT') {
          cell.textContent = input.options[input.selectedIndex].text;
        } else {
          cell.textContent = input.value;
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
