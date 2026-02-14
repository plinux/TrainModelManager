// Train Model Manager - Main JavaScript file

// 机车系列过滤车型
function filterLocomotiveModelsBySeries(seriesId) {
  const modelSelect = document.getElementById('model_id');
  modelSelect.innerHTML = '<option value="">请选择</option>';

  if (!seriesId || !window.locomotiveModelData) return;

  const filteredModels = window.locomotiveModelData.filter(model => model.series_id === parseInt(seriesId));
  filteredModels.forEach(model => {
    const option = document.createElement('option');
    option.value = model.id;
    option.textContent = model.name;
    modelSelect.appendChild(option);
  });
}

// 机车系列选择变化
function handleLocomotiveSeriesChange() {
  const seriesId = document.getElementById('series_id').value;
  filterLocomotiveModelsBySeries(seriesId);
  document.getElementById('power_type_id').value = '';
}

// 动车组系列过滤车型
function filterTrainsetModelsBySeries(seriesId) {
  const modelSelect = document.getElementById('model_id');
  modelSelect.innerHTML = '<option value="">请选择</option>';

  if (!seriesId || !window.trainsetModelData) return;

  const filteredModels = window.trainsetModelData.filter(model => model.series_id === parseInt(seriesId));
  filteredModels.forEach(model => {
    const option = document.createElement('option');
    option.value = model.id;
    option.textContent = model.name;
    modelSelect.appendChild(option);
  });
}

// 动车组系列选择变化
function handleTrainsetSeriesChange() {
  const seriesId = document.getElementById('series_id').value;
  filterTrainsetModelsBySeries(seriesId);
  document.getElementById('power_type_id').value = '';
}

// 自动填充功能（保留原功能，用于选择车型后填充系列和动力类型）
function autoFillLocomotive() {
  const modelId = document.getElementById('model_id').value;
  if (!modelId) return;

  fetch(`/api/auto-fill/locomotive/${modelId}`)
    .then(response => response.json())
    .then(data => {
      document.getElementById('series_id').value = data.series_id;
      document.getElementById('power_type_id').value = data.power_type_id;
    });
}

function autoFillCarriage() {
  const modelId = document.getElementById('series_id').value;
  if (!modelId) return;

  fetch(`/api/auto-fill/carriage/${modelId}`)
    .then(response => response.json())
    .then(data => {
      // 系列ID已自动填充，类型需要额外字段
      document.getElementById('series_id').value = data.series_id;
      if (data.type) {
        // 如果需要显示类型，可以添加一个隐藏字段
        console.log('Carriage type:', data.type);
      }
    });
}

function autoFillTrainset() {
  const modelId = document.getElementById('model_id').value;
  if (!modelId) return;

  fetch(`/api/auto-fill/trainset/${modelId}`)
    .then(response => response.json())
    .then(data => {
      document.getElementById('series_id').value = data.series_id;
      document.getElementById('power_type_id').value = data.power_type_id;
    });
}

// 车厢项管理
let carriageItemCount = 0;

// 根据系列ID过滤车型
function filterModelsBySeries(seriesId, modelSelect) {
  modelSelect.innerHTML = '<option value="">请选择</option>';

  if (!seriesId || !window.carriageModelData) return;

  const filteredModels = window.carriageModelData.filter(model => model.series_id === parseInt(seriesId));
  filteredModels.forEach(model => {
    const option = document.createElement('option');
    option.value = model.id;
    option.textContent = model.name;
    modelSelect.appendChild(option);
  });
}

// 为系列选择框生成选项
function generateSeriesOptions() {
  if (!window.carriageSeriesData) return '<option value="">请选择</option>';

  return window.carriageSeriesData.map(series =>
    `<option value="${series.id}">${series.name}</option>`
  ).join('');
}

function addCarriageRow() {
  const container = document.getElementById('carriage-items');
  // 获取主表单中选择的系列ID
  const mainSeriesId = document.getElementById('series_id').value;

  const newItem = document.createElement('div');
  newItem.className = 'carriage-item form-row';
  newItem.innerHTML = `
    <div class="form-group">
      <label>系列</label>
      <select name="series_${carriageItemCount}" onchange="handleSeriesChange(this)">
        ${generateSeriesOptions()}
      </select>
    </div>
    <div class="form-group">
      <label>车型</label>
      <select name="model_${carriageItemCount}">
        <option value="">请选择</option>
      </select>
    </div>
    <div class="form-group">
      <label>车辆号</label>
      <input type="text" name="car_number_${carriageItemCount}">
    </div>
    <div class="form-group">
      <label>颜色</label>
      <input type="text" name="color_${carriageItemCount}">
    </div>
    <div class="form-group">
      <label>灯光</label>
      <input type="text" name="lighting_${carriageItemCount}">
    </div>
    <button type="button" onclick="removeCarriageRow(this)">删除</button>
  `;
  container.appendChild(newItem);

  // 如果主表单已选择系列，设置新车厢项的系列并填充车型
  if (mainSeriesId) {
    const seriesSelect = newItem.querySelector(`select[name="series_${carriageItemCount}"]`);
    seriesSelect.value = mainSeriesId;
    const modelSelect = newItem.querySelector(`select[name="model_${carriageItemCount}"]`);
    filterModelsBySeries(mainSeriesId, modelSelect);
  }

  carriageItemCount++;
}

// 处理系列选择变化
function handleSeriesChange(seriesSelect) {
  const row = seriesSelect.closest('.carriage-item');
  const modelSelect = row.querySelector('select[name^="model_"]');
  filterModelsBySeries(seriesSelect.value, modelSelect);
}

function removeCarriageRow(button) {
  const container = document.getElementById('carriage-items');
  if (container.children.length > 1) {
    container.removeChild(button.parentElement);
  }
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

// AJAX 表单提交和错误处理
function submitFormAjax(form, apiUrl) {
  const formData = new FormData(form);
  const formDataObj = {};

  // 将 FormData 转换为对象
  formData.forEach((value, key) => {
    formDataObj[key] = value;
  });

  // 清除之前的错误
  clearErrors(form);

  return fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formDataObj)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // 显示成功消息并刷新页面
      showSuccessMessage(form, data.message || '添加成功');
      setTimeout(() => {
        location.reload();
      }, 1000);
    } else {
      // 显示错误
      if (data.errors) {
        showErrors(form, data.errors);
      }
      if (data.error) {
        alert(data.error);
      }
    }
    return data;
  })
  .catch(error => {
    console.error('Error:', error);
    alert('提交失败，请重试');
  });
}

// 清除表单错误
function clearErrors(form) {
  form.querySelectorAll('.form-group.error').forEach(group => {
    group.classList.remove('error');
  });

  const errorBubbles = form.querySelectorAll('.error-bubble');
  errorBubbles.forEach(bubble => bubble.remove());

  const successMessage = form.querySelector('.form-success.success-message');
  if (successMessage) {
    successMessage.style.display = 'none';
  }
}

// 显示错误
function showErrors(form, errors) {
  errors.forEach(error => {
    if (error.field) {
      // 字段错误 - 在对应标签上显示气泡
      const input = form.querySelector(`[name="${error.field}"]`);
      if (input) {
        const formGroup = input.closest('.form-group');
        const label = formGroup.querySelector('label');

        // 添加错误类
        formGroup.classList.add('error');

        // 移除旧的错误气泡
        const oldBubble = label.querySelector('.error-bubble');
        if (oldBubble) {
          oldBubble.remove();
        }

        // 添加新的错误气泡
        const bubble = document.createElement('span');
        bubble.className = 'error-bubble';
        bubble.textContent = error.message;
        label.appendChild(bubble);
      }
    } else {
      // 全局错误 - 显示 alert
      alert(error.message);
    }
  });
}

// 显示成功消息
function showSuccessMessage(form, message) {
  let successDiv = form.querySelector('.form-success.success-message');
  if (!successDiv) {
    successDiv = document.createElement('div');
    successDiv.className = 'form-success success-message';
    form.insertBefore(successDiv, form.firstChild);
  }
  successDiv.textContent = message;
  successDiv.style.display = 'block';
}
