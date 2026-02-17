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
    let hasUnmatchedErrors = false;
    let unmatchedMessages = [];

    errors.forEach(error => {
      if (error.field) {
        const input = form.querySelector(`[name="${error.field}"]`);
        if (input) {
          const formGroup = input.closest('.form-group');
          if (formGroup) {
            formGroup.classList.add('error');

            // 移除旧的错误气泡
            const oldBubble = formGroup.querySelector('.error-bubble');
            if (oldBubble) oldBubble.remove();

            // 添加新的悬浮错误气泡到 form-group
            const bubble = document.createElement('span');
            bubble.className = 'error-bubble';
            bubble.textContent = error.message;
            formGroup.appendChild(bubble);
          } else {
            // 找不到 form-group，记录未匹配的错误
            hasUnmatchedErrors = true;
            unmatchedMessages.push(`${error.field}: ${error.message}`);
          }
        } else {
          // 找不到输入框，记录未匹配的错误
          hasUnmatchedErrors = true;
          unmatchedMessages.push(`${error.field}: ${error.message}`);
        }
      } else {
        hasUnmatchedErrors = true;
        if (error.message) {
          unmatchedMessages.push(error.message);
        }
      }
    });

    // 只有没有任何字段错误被成功显示时，才显示汇总错误
    if (hasUnmatchedErrors && unmatchedMessages.length > 0) {
      this.showErrorSummary(form, unmatchedMessages.join('\n'));
    }
  },

  /**
   * 显示错误汇总
   * @param {HTMLFormElement} form - 表单元素
   * @param {string} message - 错误消息
   */
  showErrorSummary(form, message) {
    let errorDiv = form.querySelector('.form-error.error-summary');
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'form-error error-summary';
      errorDiv.style.cssText = 'background: #fee; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 4px; margin-bottom: 10px; white-space: pre-line;';
      form.insertBefore(errorDiv, form.firstChild);
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  },

  /**
   * 清除错误汇总
   * @param {HTMLFormElement} form - 表单元素
   */
  clearErrorSummary(form) {
    const errorDiv = form.querySelector('.form-error.error-summary');
    if (errorDiv) {
      errorDiv.remove();
    }
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
    this.clearErrorSummary(form);

    return Api.post(apiUrl, formDataObj)
      .then(data => {
        if (data.success) {
          this.showSuccess(form, data.message || '添加成功');
          setTimeout(() => location.reload(), 1000);
        } else {
          if (data.errors && data.errors.length > 0) {
            this.showErrors(form, data.errors);
          } else if (data.error) {
            // 单个错误消息，显示为汇总
            this.showErrorSummary(form, data.error);
          }
        }
        return data;
      })
      .catch(error => {
        console.error('Submit error:', error);
        // 检查是否是验证错误（包含 errors 数组）
        if (error.errors && error.errors.length > 0) {
          this.showErrors(form, error.errors);
        } else {
          const errorMsg = error.error || error.message || '提交失败，请重试';
          this.showErrorSummary(form, errorMsg);
        }
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

// 可搜索下拉框管理器
const AutocompleteManager = {
  // 存储所有自动完成的实例
  instances: {},

  /**
   * 初始化自动完成组件
   * @param {string} inputId - 输入框ID
   * @param {string} hiddenId - 隐藏域ID（存储实际值）
   * @param {Array} options - 选项数组 [{id, name}]
   * @param {Object} config - 配置项 { onchange }
   */
  init(inputId, hiddenId, options, config = {}) {
    const input = document.getElementById(inputId);
    const hidden = document.getElementById(hiddenId);
    const wrapper = input?.closest('.autocomplete-wrapper');

    if (!input || !hidden) return;

    const instance = {
      input,
      hidden,
      wrapper,
      options: options || [],
      config,
      selectedIndex: -1,
      filteredOptions: []
    };

    this.instances[inputId] = instance;

    // 创建下拉列表
    let dropdown = wrapper?.querySelector('.autocomplete-dropdown');
    if (!dropdown && wrapper) {
      dropdown = document.createElement('div');
      dropdown.className = 'autocomplete-dropdown';
      wrapper.appendChild(dropdown);
    }
    instance.dropdown = dropdown;

    // 创建提示文字
    let hint = wrapper?.querySelector('.autocomplete-hint');
    if (!hint && wrapper) {
      hint = document.createElement('div');
      hint.className = 'autocomplete-hint';
      hint.textContent = '该选项不存在，请先到信息维护页面添加';
      wrapper.appendChild(hint);
    }
    instance.hint = hint;

    // 绑定事件
    this.bindEvents(instance);
  },

  /**
   * 绑定事件
   */
  bindEvents(instance) {
    const { input, hidden, dropdown, wrapper, config } = instance;

    // 输入事件
    input.addEventListener('input', (e) => {
      this.handleInput(instance, e.target.value);
    });

    // 聚焦事件
    input.addEventListener('focus', (e) => {
      if (e.target.value) {
        this.handleInput(instance, e.target.value);
      } else {
        this.showAllOptions(instance);
      }
    });

    // 失焦事件（延迟处理，让点击事件先执行）
    input.addEventListener('blur', () => {
      setTimeout(() => {
        this.handleBlur(instance);
      }, 200);
    });

    // 键盘事件
    input.addEventListener('keydown', (e) => {
      this.handleKeydown(instance, e);
    });
  },

  /**
   * 处理输入
   */
  handleInput(instance, value) {
    const { options, dropdown } = instance;
    instance.selectedIndex = -1;

    if (!value) {
      this.showAllOptions(instance);
      return;
    }

    // 过滤选项
    const lowerValue = value.toLowerCase();
    instance.filteredOptions = options.filter(opt =>
      opt.name.toLowerCase().includes(lowerValue)
    );

    // 渲染下拉列表
    this.renderDropdown(instance, value);

    if (instance.filteredOptions.length > 0) {
      dropdown.classList.add('show');
    } else {
      dropdown.classList.remove('show');
    }
  },

  /**
   * 显示所有选项
   */
  showAllOptions(instance) {
    const { options, dropdown } = instance;
    instance.filteredOptions = options;
    instance.selectedIndex = -1;

    this.renderDropdown(instance, '');
    dropdown.classList.add('show');
  },

  /**
   * 渲染下拉列表（使用安全的 DOM 方法）
   */
  renderDropdown(instance, searchValue) {
    const { dropdown, filteredOptions } = instance;

    // 清空下拉列表
    while (dropdown.firstChild) {
      dropdown.removeChild(dropdown.firstChild);
    }

    if (filteredOptions.length === 0) {
      const noMatch = document.createElement('div');
      noMatch.className = 'autocomplete-option no-match';
      noMatch.textContent = '无匹配选项';
      dropdown.appendChild(noMatch);
      return;
    }

    const lowerSearch = searchValue.toLowerCase();
    filteredOptions.forEach((opt, index) => {
      const optionEl = document.createElement('div');
      optionEl.className = 'autocomplete-option';
      optionEl.dataset.index = index;
      optionEl.dataset.id = opt.id;
      optionEl.dataset.name = opt.name;

      // 高亮匹配部分
      if (searchValue) {
        const displayName = opt.name;
        const pos = displayName.toLowerCase().indexOf(lowerSearch);
        if (pos !== -1) {
          const before = document.createTextNode(displayName.substring(0, pos));
          const highlight = document.createElement('span');
          highlight.className = 'highlight';
          highlight.textContent = displayName.substring(pos, pos + searchValue.length);
          const after = document.createTextNode(displayName.substring(pos + searchValue.length));
          optionEl.appendChild(before);
          optionEl.appendChild(highlight);
          optionEl.appendChild(after);
        } else {
          optionEl.textContent = displayName;
        }
      } else {
        optionEl.textContent = opt.name;
      }

      // 点击事件
      optionEl.addEventListener('click', () => {
        this.selectOption(instance, opt.id, opt.name);
      });

      dropdown.appendChild(optionEl);
    });
  },

  /**
   * 选择选项
   */
  selectOption(instance, id, name) {
    const { input, hidden, dropdown, wrapper, config } = instance;

    input.value = name;
    hidden.value = id;
    dropdown.classList.remove('show');
    wrapper?.classList.remove('no-match');

    // 触发回调
    if (config.onchange && typeof config.onchange === 'function') {
      config.onchange(id, name);
    }

    // 触发原生 change 事件
    const event = new Event('change', { bubbles: true });
    hidden.dispatchEvent(event);
  },

  /**
   * 处理失焦
   */
  handleBlur(instance) {
    const { input, hidden, wrapper, options, config } = instance;
    instance.dropdown.classList.remove('show');

    const value = input.value.trim();

    if (!value) {
      hidden.value = '';
      wrapper?.classList.remove('no-match');
      return;
    }

    // 检查输入值是否在选项中
    const matchedOption = options.find(opt =>
      opt.name.toLowerCase() === value.toLowerCase()
    );

    if (matchedOption) {
      hidden.value = matchedOption.id;
      input.value = matchedOption.name; // 使用标准化的名称
      wrapper?.classList.remove('no-match');
    } else {
      hidden.value = '';
      wrapper?.classList.add('no-match');
    }
  },

  /**
   * 处理键盘事件
   */
  handleKeydown(instance, e) {
    const { dropdown, filteredOptions, selectedIndex } = instance;

    if (!dropdown.classList.contains('show')) return;

    const options = dropdown.querySelectorAll('.autocomplete-option:not(.no-match)');

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        instance.selectedIndex = Math.min(selectedIndex + 1, options.length - 1);
        this.updateSelection(instance, options);
        break;

      case 'ArrowUp':
        e.preventDefault();
        instance.selectedIndex = Math.max(selectedIndex - 1, 0);
        this.updateSelection(instance, options);
        break;

      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && options[selectedIndex]) {
          const opt = options[selectedIndex];
          this.selectOption(instance, opt.dataset.id, opt.dataset.name);
        }
        break;

      case 'Escape':
        dropdown.classList.remove('show');
        break;
    }
  },

  /**
   * 更新选中状态
   */
  updateSelection(instance, options) {
    options.forEach((opt, i) => {
      opt.classList.toggle('selected', i === instance.selectedIndex);
    });

    // 滚动到可见
    if (instance.selectedIndex >= 0 && options[instance.selectedIndex]) {
      options[instance.selectedIndex].scrollIntoView({ block: 'nearest' });
    }
  },

  /**
   * 设置选项（用于动态更新）
   */
  setOptions(inputId, options) {
    const instance = this.instances[inputId];
    if (instance) {
      instance.options = options || [];
    }
  },

  /**
   * 获取当前值
   */
  getValue(inputId) {
    const instance = this.instances[inputId];
    if (instance) {
      return {
        id: instance.hidden.value,
        name: instance.input.value
      };
    }
    return null;
  },

  /**
   * 设置当前值
   */
  setValue(inputId, id, name) {
    const instance = this.instances[inputId];
    if (instance) {
      instance.hidden.value = id;
      instance.input.value = name;
      instance.wrapper?.classList.remove('no-match');
    }
  }
};

// 表单填充器（复制功能）
const FormFiller = {
  /**
   * 从表格行复制数据到表单
   * @param {HTMLElement} button - 复制按钮
   * @param {Object} fieldMappings - 字段映射 { dataAttr: 'formFieldId' }
   *   对于自动完成字段，dataAttr 应该是存储 ID 的属性名（如 model_id）
   *   会自动查找对应的名称属性（如 data-model）来获取显示名称
   */
  copyFromRow(button, fieldMappings) {
    const row = button.closest('tr');
    if (!row) return;

    // 遍历字段映射，填充表单
    Object.entries(fieldMappings).forEach(([dataAttr, fieldId]) => {
      const value = row.dataset[dataAttr];
      const element = document.getElementById(fieldId);

      if (!element) return;

      // 检查是否是自动完成组件（隐藏域在 autocomplete-wrapper 内）
      const wrapper = element.closest('.autocomplete-wrapper');
      if (wrapper) {
        // 使用 AutocompleteManager 设置值
        const inputId = wrapper.querySelector('input[type="text"]')?.id;
        if (inputId) {
          // 对于自动完成字段，dataAttr 存储的是 ID（如 model_id）
          // 需要查找对应的名称属性（去掉 _id 后缀）
          const nameAttr = dataAttr.replace('_id', '');
          const nameValue = row.dataset[nameAttr] || value;
          AutocompleteManager.setValue(inputId, value || '', nameValue || '');
        }
      } else {
        // 普通表单字段
        element.value = value || '';
      }
    });

    // 滚动到表单顶部
    const form = document.querySelector('form');
    if (form) {
      form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  },

  /**
   * 复制机车数据
   */
  copyLocomotive(button) {
    this.copyFromRow(button, {
      model_id: 'model_id',
      series_id: 'series_id',
      power_type_id: 'power_type_id',
      depot_id: 'depot_id',
      scale: 'scale',
      locomotive_number: 'locomotive_number',
      decoder_number: 'decoder_number',
      plaque: 'plaque',
      chip_interface_id: 'chip_interface_id',
      chip_model_id: 'chip_model_id',
      color: 'color',
      price: 'price',
      merchant_id: 'merchant_id',
      brand_id: 'brand_id',
      item_number: 'item_number',
      product_url: 'product_url',
      purchase_date: 'purchase_date'
    });
  },

  /**
   * 复制动车组数据
   */
  copyTrainset(button) {
    this.copyFromRow(button, {
      model_id: 'model_id',
      series_id: 'series_id',
      power_type_id: 'power_type_id',
      depot_id: 'depot_id',
      scale: 'scale',
      trainset_number: 'trainset_number',
      decoder_number: 'decoder_number',
      formation: 'formation',
      head_light: 'head_light',
      interior_light: 'interior_light',
      chip_interface_id: 'chip_interface_id',
      chip_model_id: 'chip_model_id',
      color: 'color',
      price: 'price',
      merchant_id: 'merchant_id',
      brand_id: 'brand_id',
      item_number: 'item_number',
      product_url: 'product_url',
      purchase_date: 'purchase_date'
    });
  },

  /**
   * 复制先头车数据
   */
  copyLocomotiveHead(button) {
    this.copyFromRow(button, {
      model_id: 'model_id',
      special_color: 'special_color',
      scale: 'scale',
      head_light: 'head_light',
      interior_light: 'interior_light',
      price: 'price',
      merchant_id: 'merchant_id',
      brand_id: 'brand_id',
      item_number: 'item_number',
      product_url: 'product_url',
      purchase_date: 'purchase_date'
    });
  },

  /**
   * 复制车厢数据
   */
  copyCarriage(button) {
    this.copyFromRow(button, {
      series_id: 'series_id',
      depot_id: 'depot_id',
      scale: 'scale',
      train_number: 'train_number',
      plaque: 'plaque',
      item_number: 'item_number',
      total_price: 'total_price',
      merchant_id: 'merchant_id',
      brand_id: 'brand_id',
      product_url: 'product_url',
      purchase_date: 'purchase_date'
    });
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

function initAutocomplete(inputId, hiddenId, options, config) {
  AutocompleteManager.init(inputId, hiddenId, options, config);
}

function setAutocompleteOptions(inputId, options) {
  AutocompleteManager.setOptions(inputId, options);
}

function setAutocompleteValue(inputId, id, name) {
  AutocompleteManager.setValue(inputId, id, name);
}

function copyLocomotive(button) {
  FormFiller.copyLocomotive(button);
}

function copyTrainset(button) {
  FormFiller.copyTrainset(button);
}

function copyLocomotiveHead(button) {
  FormFiller.copyLocomotiveHead(button);
}

function copyCarriage(button) {
  FormFiller.copyCarriage(button);
}
