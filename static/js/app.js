// Train Model Manager - Main JavaScript file

// 自动填充功能
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

function addCarriageRow() {
  const container = document.getElementById('carriage-items');
  const firstModelSelect = container.querySelector('select[name^="model_"]');
  const modelOptions = firstModelSelect ? firstModelSelect.innerHTML : '<option value="">请选择</option>';

  const newItem = document.createElement('div');
  newItem.className = 'carriage-item form-row';
  newItem.innerHTML = `
    <div class="form-group">
      <label>车型</label>
      <select name="model_${carriageItemCount}">
        ${modelOptions}
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
  carriageItemCount++;
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
