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
  document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(tabId).style.display = 'block';
  event.target.classList.add('active');
}
