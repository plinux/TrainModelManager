// 选项维护页面行内编辑功能

// 存储原始值，用于取消编辑时恢复
let originalValues = {};

// 编辑行
function editRow(button) {
  const row = button.closest('tr');
  const fieldType = row.dataset.type;

  // 切换按钮显示
  button.style.display = 'none';
  const saveBtn = row.querySelector('.btn-save');
  const cancelBtn = row.querySelector('.btn-cancel');
  const deleteForm = row.querySelector('form');
  saveBtn.style.display = 'inline-block';
  cancelBtn.style.display = 'inline-block';
  deleteForm.style.display = 'none';

  // 存储原始值
  row.querySelectorAll('[data-field]').forEach(cell => {
    const fieldName = cell.dataset.field;
    originalValues[fieldName] = cell.innerHTML.trim();
  });

  // 获取字段列表
  const fields = row.dataset.fields.split(',');

  // 为每个字段创建编辑控件
  fields.forEach(field => {
    const cell = row.querySelector(`[data-field="${field}"]`);

    if (field === 'name') {
      // 名称字段使用文本输入
      const originalValue = originalValues[field];
      cell.innerHTML = `<input type="text" name="${field}" value="${originalValue}" style="width:100%; padding:0.25rem 0.5rem;">`;
    } else if (field === 'series_id') {
      // 系列字段使用下拉框
      const addFormSelect = row.closest('.tab-content').querySelector('select[name="series_id"]');
      let optionsHtml = '';
      if (addFormSelect) {
        const originalSeriesId = row.dataset.series || '';
        optionsHtml = addFormSelect.innerHTML.replace(new RegExp(`value="${originalSeriesId}"`, 'g'), `value="${originalSeriesId}" selected`);
      }
      cell.innerHTML = `<select name="series_id" style="width:100%; padding:0.25rem 0.5rem;">${optionsHtml}</select>`;
    } else if (field === 'power_type_id') {
      // 动力类型字段使用下拉框
      const addFormSelect = row.closest('.tab-content').querySelector('select[name="power_type_id"]');
      let optionsHtml = '';
      if (addFormSelect) {
        const originalPowerId = row.dataset.power || '';
        optionsHtml = addFormSelect.innerHTML.replace(new RegExp(`value="${originalPowerId}"`, 'g'), `value="${originalPowerId}" selected`);
      }
      cell.innerHTML = `<select name="power_type_id" style="width:100%; padding:0.25rem 0.5rem;">${optionsHtml}</select>`;
    } else if (field === 'type') {
      // 车厢类型字段使用下拉框
      const addFormSelect = row.closest('.tab-content').querySelector('select[name="type"]');
      let optionsHtml = '';
      if (addFormSelect) {
        const originalType = row.dataset.carriageType || '';
        optionsHtml = addFormSelect.innerHTML.replace(new RegExp(`value="${originalType}"`, 'g'), `value="${originalType}" selected`);
      }
      cell.innerHTML = `<select name="type" style="width:100%; padding:0.25rem 0.5rem;">${optionsHtml}</select>`;
    }
  });
}

// 保存行
function saveRow(button, type) {
  const row = button.closest('tr');
  const id = row.dataset.id;

  // 收集数据
  const formData = new FormData();
  formData.append('id', id);

  // 获取字段列表
  const fields = row.dataset.fields.split(',');

  fields.forEach(field => {
    const input = row.querySelector(`[name="${field}"]`);
    if (input) {
      const value = input.value;
      if (field === 'series_id') {
        formData.append('series_id', value);
      } else if (field === 'power_type_id') {
        formData.append('power_type_id', value);
      } else if (field === 'carriage_type') {
        formData.append('type', value);
      } else {
        formData.append(field, value);
      }
    }
  });

  // 发送 AJAX 请求
  const apiUrl = `/api/options/${type}/edit`;
  fetch(apiUrl, {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // 更新显示的值
      fields.forEach(field => {
        const cell = row.querySelector(`[data-field="${field}"]`);
        const input = row.querySelector(`[name="${field}"]`);
        if (input) {
          if (input.tagName === 'SELECT') {
            cell.innerHTML = input.options[input.selectedIndex].text;
          } else {
            cell.innerHTML = input.value;
          }
        }
      });

      // 恢复按钮状态
      cancelEdit(button);
    } else {
      alert('保存失败: ' + (data.error || '未知错误'));
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('保存失败，请重试');
  });
}

// 取消编辑
function cancelEdit(button) {
  const row = button.closest('tr');

  // 恢复原始值
  Object.keys(originalValues).forEach(field => {
    const cell = row.querySelector(`[data-field="${field}"]`);
    if (cell) {
      cell.innerHTML = originalValues[field];
    }
  });

  // 清空原始值存储
  originalValues = {};

  // 恢复按钮状态
  const editBtn = row.querySelector('.btn-edit');
  const saveBtn = row.querySelector('.btn-save');
  const cancelBtn = row.querySelector('.btn-cancel');
  const deleteForm = row.querySelector('form');

  editBtn.style.display = 'inline-block';
  saveBtn.style.display = 'none';
  cancelBtn.style.display = 'none';
  deleteForm.style.display = 'inline-block';
}

// 标签页切换
function showTab(tabId) {
  // 隐藏所有内容区
  document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');

  // 移除所有标签的激活状态
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  // 显示目标内容区
  const content = document.getElementById(tabId);
  if (content) {
    content.style.display = 'block';
  }

  // 添加当前点击标签的激活状态
  if (event && event.target) {
    event.target.classList.add('active');
  }
}

// 重新初始化数据库确认
function confirmReinit() {
  const confirmed = confirm('警告：此操作将删除所有数据并重新初始化数据库！\n\n此操作不可撤销，请确认是否继续？');

  if (confirmed) {
    // 二次确认
    const doubleConfirmed = confirm('再次确认：真的要删除所有数据吗？');

    if (doubleConfirmed) {
      // 创建隐藏的表单并提交
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/options/reinit';

      document.body.appendChild(form);
      form.submit();
      document.body.removeChild(form);
    }
  }
}
