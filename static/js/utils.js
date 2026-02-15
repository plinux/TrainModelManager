/**
 * 火车模型管理系统 - 公共 JavaScript 模块
 * 包含通用的工具函数和 AJAX 处理
 */

// 通用工具对象
const Utils = {
  /**
   * 过滤车型列表
   * @param {string} seriesId - 系列ID
   * @param {string} modelSelectId - 车型选择框ID
   * @param {Array} modelData - 车型数据数组
   */
  filterModelsBySeries(seriesId, modelSelectId, modelData) {
    const modelSelect = document.getElementById(modelSelectId);
    if (!modelSelect) return;

    modelSelect.innerHTML = '<option value="">请选择</option>';

    if (!seriesId || !modelData) return;

    const seriesIdNum = Number(seriesId);
    const filteredModels = modelData.filter(model => Number(model.series_id) === seriesIdNum);
    filteredModels.forEach(model => {
      const option = document.createElement('option');
      option.value = model.id;
      option.textContent = model.name;
      modelSelect.appendChild(option);
    });
  },

  /**
   * 自动填充表单字段
   * @param {string} apiPath - API 路径
   * @param {Object} fieldMappings - 字段映射 { apiField: 'elementId' }
   */
  autoFill(apiPath, fieldMappings) {
    fetch(apiPath)
      .then(response => response.json())
      .then(data => {
        Object.entries(fieldMappings).forEach(([apiKey, elementId]) => {
          const element = document.getElementById(elementId);
          if (element && data[apiKey] !== undefined) {
            element.value = data[apiKey];
          }
        });
      })
      .catch(error => console.error('Auto-fill error:', error));
  },

  /**
   * 标签页切换
   * @param {string} tabId - 要显示的标签内容ID
   * @param {Event} event - 点击事件
   */
  showTab(tabId, event) {
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
};

// AJAX 请求封装
const Api = {
  /**
   * 发送 JSON POST 请求
   * @param {string} url - 请求URL
   * @param {Object} data - 请求数据
   * @returns {Promise}
   */
  post(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(response => {
      if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
      }
      return response.json();
    });
  },

  /**
   * 发送 FormData POST 请求
   * @param {string} url - 请求URL
   * @param {FormData} formData - 表单数据
   * @returns {Promise}
   */
  postForm(url, formData) {
    return fetch(url, {
      method: 'POST',
      body: formData
    }).then(response => {
      if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
      }
      return response.json();
    });
  }
};

// 表单处理对象
const FormHelper = {
  /**
   * 清除表单错误状态
   * @param {HTMLFormElement} form - 表单元素
   */
  clearErrors(form) {
    form.querySelectorAll('.form-group.error').forEach(group => {
      group.classList.remove('error');
    });

    form.querySelectorAll('.error-bubble').forEach(bubble => bubble.remove());

    const successMessage = form.querySelector('.form-success.success-message');
    if (successMessage) {
      successMessage.style.display = 'none';
    }
  },

  /**
   * 显示字段错误
   * @param {HTMLFormElement} form - 表单元素
   * @param {Array} errors - 错误数组 [{field, message}]
   */
  showErrors(form, errors) {
    errors.forEach(error => {
      if (error.field) {
        const input = form.querySelector(`[name="${error.field}"]`);
        if (input) {
          const formGroup = input.closest('.form-group');
          const label = formGroup.querySelector('label');

          formGroup.classList.add('error');

          // 移除旧的错误气泡
          const oldBubble = label.querySelector('.error-bubble');
          if (oldBubble) oldBubble.remove();

          // 添加新的错误气泡
          const bubble = document.createElement('span');
          bubble.className = 'error-bubble';
          bubble.textContent = error.message;
          label.appendChild(bubble);
        }
      } else {
        alert(error.message);
      }
    });
  },

  /**
   * 显示成功消息
   * @param {HTMLFormElement} form - 表单元素
   * @param {string} message - 成功消息
   */
  showSuccess(form, message) {
    let successDiv = form.querySelector('.form-success.success-message');
    if (!successDiv) {
      successDiv = document.createElement('div');
      successDiv.className = 'form-success success-message';
      form.insertBefore(successDiv, form.firstChild);
    }
    successDiv.textContent = message;
    successDiv.style.display = 'block';
  },

  /**
   * AJAX 提交表单
   * @param {HTMLFormElement} form - 表单元素
   * @param {string} apiUrl - API URL
   * @returns {Promise}
   */
  submitAjax(form, apiUrl) {
    const formData = new FormData(form);
    const formDataObj = {};

    formData.forEach((value, key) => {
      formDataObj[key] = value;
    });

    this.clearErrors(form);

    return Api.post(apiUrl, formDataObj)
      .then(data => {
        if (data.success) {
          this.showSuccess(form, data.message || '添加成功');
          setTimeout(() => location.reload(), 1000);
        } else {
          if (data.errors) {
            this.showErrors(form, data.errors);
          }
          if (data.error) {
            alert(data.error);
          }
        }
        return data;
      })
      .catch(error => {
        console.error('Submit error:', error);
        alert('提交失败，请重试');
      });
  }
};

// 车厢项管理
const CarriageManager = {
  itemCount: 0,

  /**
   * 根据系列ID过滤车型
   * @param {string} seriesId - 系列ID
   * @param {HTMLSelectElement} modelSelect - 车型选择框
   */
  filterModelsBySeries(seriesId, modelSelect) {
    Utils.filterModelsBySeries(seriesId, modelSelect.id, window.carriageModelData);
  },

  /**
   * 生成系列选项 HTML
   * @returns {string}
   */
  generateSeriesOptions() {
    if (!window.carriageSeriesData) return '<option value="">请选择</option>';

    return window.carriageSeriesData.map(series =>
      `<option value="${series.id}">${series.name}</option>`
    ).join('');
  },

  /**
   * 添加车厢行
   */
  addRow() {
    const container = document.getElementById('carriage-items');
    if (!container) return;

    const mainSeriesId = document.getElementById('series_id')?.value;

    const newItem = document.createElement('div');
    newItem.className = 'carriage-item form-row';
    newItem.innerHTML = `
      <div class="form-group">
        <label>系列</label>
        <select name="series_${this.itemCount}" id="series_${this.itemCount}" onchange="CarriageManager.handleSeriesChange(this)">
          ${this.generateSeriesOptions()}
        </select>
      </div>
      <div class="form-group">
        <label>车型</label>
        <select name="model_${this.itemCount}" id="model_${this.itemCount}">
          <option value="">请选择</option>
        </select>
      </div>
      <div class="form-group">
        <label>车辆号</label>
        <input type="text" name="car_number_${this.itemCount}">
      </div>
      <div class="form-group">
        <label>颜色</label>
        <input type="text" name="color_${this.itemCount}">
      </div>
      <div class="form-group">
        <label>灯光</label>
        <input type="text" name="lighting_${this.itemCount}">
      </div>
      <button type="button" onclick="CarriageManager.removeRow(this)">删除</button>
    `;
    container.appendChild(newItem);

    // 如果主表单已选择系列，设置新车厢项的系列并填充车型
    if (mainSeriesId) {
      const seriesSelect = newItem.querySelector(`select[name="series_${this.itemCount}"]`);
      seriesSelect.value = mainSeriesId;
      const modelSelect = newItem.querySelector(`select[name="model_${this.itemCount}"]`);
      Utils.filterModelsBySeries(mainSeriesId, modelSelect.id, window.carriageModelData);
    }

    this.itemCount++;
  },

  /**
   * 处理系列选择变化
   * @param {HTMLSelectElement} seriesSelect - 系列选择框
   */
  handleSeriesChange(seriesSelect) {
    const row = seriesSelect.closest('.carriage-item');
    const modelSelect = row.querySelector('select[name^="model_"]');
    Utils.filterModelsBySeries(seriesSelect.value, modelSelect.id, window.carriageModelData);
  },

  /**
   * 删除车厢行
   * @param {HTMLElement} button - 删除按钮
   */
  removeRow(button) {
    const container = document.getElementById('carriage-items');
    if (container && container.children.length > 1) {
      container.removeChild(button.parentElement);
    }
  }
};

// 模型表单处理
const ModelForm = {
  /**
   * 处理机车系列变化
   */
  handleLocomotiveSeriesChange() {
    const seriesId = document.getElementById('series_id')?.value;
    Utils.filterModelsBySeries(seriesId, 'model_id', window.locomotiveModelData);
    const powerTypeElement = document.getElementById('power_type_id');
    if (powerTypeElement) powerTypeElement.value = '';
  },

  /**
   * 处理动车组系列变化
   */
  handleTrainsetSeriesChange() {
    const seriesId = document.getElementById('series_id')?.value;
    Utils.filterModelsBySeries(seriesId, 'model_id', window.trainsetModelData);
    const powerTypeElement = document.getElementById('power_type_id');
    if (powerTypeElement) powerTypeElement.value = '';
  },

  /**
   * 机车车型自动填充
   */
  autoFillLocomotive() {
    const modelId = document.getElementById('model_id')?.value;
    if (!modelId) return;

    Utils.autoFill(`/api/auto-fill/locomotive/${modelId}`, {
      series_id: 'series_id',
      power_type_id: 'power_type_id'
    });
  },

  /**
   * 动车组车型自动填充
   */
  autoFillTrainset() {
    const modelId = document.getElementById('model_id')?.value;
    if (!modelId) return;

    Utils.autoFill(`/api/auto-fill/trainset/${modelId}`, {
      series_id: 'series_id',
      power_type_id: 'power_type_id'
    });
  }
};

// 表格排序筛选管理器
const TableManager = {
  // 当前排序状态
  sortColumn: null,
  sortDirection: 'asc',  // 'asc' | 'desc' | null

  // 当前筛选状态
  filters: {},

  /**
   * 初始化表格
   * @param {string} tableId - 表格 ID
   */
  init(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    this.table = table;
    this.tbody = table.querySelector('tbody');
    this.originalRows = Array.from(this.tbody.querySelectorAll('tr'));

    this.setupSortHeaders();
    this.setupFilterHeaders();
  },

  /**
   * 设置排序表头
   */
  setupSortHeaders() {
    const headers = this.table.querySelectorAll('th[data-sort]');
    headers.forEach(th => {
      th.style.cursor = 'pointer';
      th.addEventListener('click', () => this.handleSort(th));

      // 添加排序指示器
      if (!th.querySelector('.sort-indicator')) {
        const indicator = document.createElement('span');
        indicator.className = 'sort-indicator';
        indicator.textContent = '⇅';
        th.appendChild(indicator);
      }
    });
  },

  /**
   * 设置筛选表头
   */
  setupFilterHeaders() {
    const headers = this.table.querySelectorAll('th[data-filter]');
    headers.forEach(th => {
      const filterKey = th.dataset.filter;
      const uniqueValues = this.getUniqueValues(filterKey);

      // 创建筛选下拉框
      const select = document.createElement('select');
      select.className = 'column-filter';

      // 添加"全部"选项
      const allOption = document.createElement('option');
      allOption.value = '';
      allOption.textContent = '全部';
      select.appendChild(allOption);

      // 添加唯一值选项
      uniqueValues.forEach(v => {
        const option = document.createElement('option');
        option.value = v;
        option.textContent = v;
        select.appendChild(option);
      });

      select.addEventListener('change', (e) => this.handleFilter(filterKey, e.target.value));

      // 包装表头内容
      const wrapper = document.createElement('div');
      wrapper.className = 'th-wrapper';
      while (th.firstChild) {
        wrapper.appendChild(th.firstChild);
      }
      th.appendChild(wrapper);
      th.appendChild(select);
    });
  },

  /**
   * 获取列的唯一值
   * @param {string} key - 列标识
   * @returns {string[]}
   */
  getUniqueValues(key) {
    const values = new Set();
    this.originalRows.forEach(row => {
      const value = row.dataset[key];
      if (value !== undefined && value !== '') {
        values.add(value);
      }
    });
    return Array.from(values).sort();
  },

  /**
   * 处理排序
   * @param {HTMLElement} th - 被点击的表头
   */
  handleSort(th) {
    const column = th.dataset.sort;

    // 切换排序方向
    if (this.sortColumn === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortDirection = 'asc';
    }

    // 更新排序指示器
    this.updateSortIndicators();

    // 执行排序
    this.applySortAndFilter();
  },

  /**
   * 更新排序指示器
   */
  updateSortIndicators() {
    const headers = this.table.querySelectorAll('th[data-sort]');
    headers.forEach(th => {
      const indicator = th.querySelector('.sort-indicator');
      if (th.dataset.sort === this.sortColumn) {
        indicator.textContent = this.sortDirection === 'asc' ? '▲' : '▼';
        indicator.className = 'sort-indicator active';
      } else {
        indicator.textContent = '⇅';
        indicator.className = 'sort-indicator';
      }
    });
  },

  /**
   * 处理筛选
   * @param {string} key - 列标识
   * @param {string} value - 筛选值
   */
  handleFilter(key, value) {
    if (value === '') {
      delete this.filters[key];
    } else {
      this.filters[key] = value;
    }
    this.applySortAndFilter();
  },

  /**
   * 执行排序和筛选
   */
  applySortAndFilter() {
    // 筛选
    let filteredRows = this.originalRows.filter(row => {
      return Object.entries(this.filters).every(([key, value]) => {
        return row.dataset[key] === value;
      });
    });

    // 排序
    if (this.sortColumn) {
      filteredRows.sort((a, b) => {
        const aVal = a.dataset[this.sortColumn] || '';
        const bVal = b.dataset[this.sortColumn] || '';

        // 尝试数字比较
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return this.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }

        // 字符串比较
        const compareResult = aVal.localeCompare(bVal, 'zh-CN');
        return this.sortDirection === 'asc' ? compareResult : -compareResult;
      });
    }

    // 重新渲染
    while (this.tbody.firstChild) {
      this.tbody.removeChild(this.tbody.firstChild);
    }
    filteredRows.forEach(row => this.tbody.appendChild(row.cloneNode(true)));
  },

  /**
   * 重置表格
   */
  reset() {
    this.sortColumn = null;
    this.sortDirection = 'asc';
    this.filters = {};
    this.updateSortIndicators();

    // 重置筛选下拉框
    this.table.querySelectorAll('.column-filter').forEach(select => {
      select.value = '';
    });

    // 恢复原始顺序
    while (this.tbody.firstChild) {
      this.tbody.removeChild(this.tbody.firstChild);
    }
    this.originalRows.forEach(row => this.tbody.appendChild(row.cloneNode(true)));
  }
};

// 全局函数兼容（保持与旧代码的兼容性）
function filterLocomotiveModelsBySeries(seriesId) {
  Utils.filterModelsBySeries(seriesId, 'model_id', window.locomotiveModelData);
}

function filterTrainsetModelsBySeries(seriesId) {
  Utils.filterModelsBySeries(seriesId, 'model_id', window.trainsetModelData);
}

function handleLocomotiveSeriesChange() {
  ModelForm.handleLocomotiveSeriesChange();
}

function handleTrainsetSeriesChange() {
  ModelForm.handleTrainsetSeriesChange();
}

function autoFillLocomotive() {
  ModelForm.autoFillLocomotive();
}

function autoFillTrainset() {
  ModelForm.autoFillTrainset();
}

function addCarriageRow() {
  CarriageManager.addRow();
}

function removeCarriageRow(button) {
  CarriageManager.removeRow(button);
}

function handleSeriesChange(seriesSelect) {
  CarriageManager.handleSeriesChange(seriesSelect);
}

function showTab(tabId) {
  Utils.showTab(tabId, event);
}

function submitFormAjax(form, apiUrl) {
  return FormHelper.submitAjax(form, apiUrl);
}

function filterModelsBySeries(seriesId, modelSelect) {
  Utils.filterModelsBySeries(seriesId, modelSelect.id, window.carriageModelData);
}

function generateSeriesOptions() {
  return CarriageManager.generateSeriesOptions();
}

function initTableSortFilter(tableId) {
  TableManager.init(tableId);
}

function resetTable(tableId) {
  TableManager.reset();
}
