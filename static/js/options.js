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
  const deleteBtn = row.querySelector('.btn-danger');
  saveBtn.style.display = 'inline-block';
  cancelBtn.style.display = 'inline-block';
  deleteBtn.style.display = 'none';

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
  const deleteBtn = row.querySelector('.btn-danger');

  editBtn.style.display = 'inline-block';
  saveBtn.style.display = 'none';
  cancelBtn.style.display = 'none';
  deleteBtn.style.display = 'inline-block';
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

// 重新初始化数据库确认对话框
function openReinitDialog() {
  document.getElementById('reinit-modal').style.display = 'flex';
  document.getElementById('reinit-input').value = '';
  document.getElementById('reinit-confirm-btn').disabled = true;
}

function closeReinitDialog() {
  document.getElementById('reinit-modal').style.display = 'none';
}

function checkReinitInput() {
  const input = document.getElementById('reinit-input');
  const btn = document.getElementById('reinit-confirm-btn');
  btn.disabled = input.value.trim().toLowerCase() !== 'yes';
}

function proceedToFinalConfirmation() {
  closeReinitDialog();
  const confirmed = confirm('真的要删除所有数据并重新初始化数据库吗？此操作不可撤销！');
  if (confirmed) {
    submitReinit();
  }
}

function submitReinit() {
  // 创建隐藏的表单并提交
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/options/reinit';

  document.body.appendChild(form);
  form.submit();
  document.body.removeChild(form);
}

// 删除选项
function deleteItem(button, type, id, deleteUrl) {
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
      // 删除成功，移除行
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

// Excel导入对话框
function openImportDialog() {
  document.getElementById('import-modal').style.display = 'flex';
  document.getElementById('import-file').value = '';
  document.getElementById('import-result').style.display = 'none';
}

function closeImportDialog() {
  document.getElementById('import-modal').style.display = 'none';
}

function importFromExcel() {
  const fileInput = document.getElementById('import-file');
  const file = fileInput.files[0];

  if (!file) {
    alert('请选择要导入的Excel文件');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  const resultDiv = document.getElementById('import-result');
  const importBtn = document.getElementById('import-btn');

  resultDiv.style.display = 'block';
  resultDiv.className = 'import-result loading';
  resultDiv.innerHTML = '<p>正在导入中，请稍候...</p>';
  importBtn.disabled = true;

  fetch('/api/import/excel', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    importBtn.disabled = false;
    if (data.success) {
      resultDiv.className = 'import-result success';
      resultDiv.innerHTML = `
        <p>导入成功！</p>
        ${data.summary ? '<ul>' + Object.entries(data.summary).map(([key, value]) => `<li>${key}: ${value}条</li>`).join('') + '</ul>' : ''}
      `;
      setTimeout(() => location.reload(), 2000);
    } else {
      resultDiv.className = 'import-result error';
      resultDiv.innerHTML = `<p>导入失败: ${data.error || '未知错误'}</p>`;
    }
  })
  .catch(error => {
    console.error('Error:', error);
    importBtn.disabled = false;
    resultDiv.className = 'import-result error';
    resultDiv.innerHTML = '<p>导入失败，请重试</p>';
  });
}
