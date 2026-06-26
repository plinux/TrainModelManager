/**
 * 火车模型管理系统 - 表单处理模块
 *
 * 提供：
 *   - FormHelper：表单错误清除/显示、AJAX 提交
 *   - CarriageManager：车厢项动态增删、系列联动
 *   - ModelForm：机车/动车组系列联动 + 自动填充
 *   - FormFiller：复制按钮（从表格行填充表单）
 *
 * 依赖（按加载顺序）：modal.js、api.js、dropdowns.js
 */
(function (global) {
  'use strict';

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
     * @param {string} modalId - 可选，模态框ID，成功后关闭模态框
     * @returns {Promise}
     */
    submitAjax(form, apiUrl, modalId) {
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
            setTimeout(() => {
              if (modalId) {
                ModalManager.close(modalId);
              }
              location.reload();
            }, 1000);
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

      // 转义 id/name，防止系列名含 HTML 字符导致 XSS
      const escapeAttr = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      return window.carriageSeriesData.map(series =>
        `<option value="${escapeAttr(series.id)}">${escapeAttr(series.name)}</option>`
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
      newItem.className = 'carriage-item-compact';
      newItem.innerHTML = `
      <select name="series_${this.itemCount}" id="series_${this.itemCount}" onchange="CarriageManager.handleSeriesChange(this)" title="系列">
        ${this.generateSeriesOptions()}
      </select>
      <select name="model_${this.itemCount}" id="model_${this.itemCount}" title="车型">
        <option value="">车型</option>
      </select>
      <input type="text" name="car_number_${this.itemCount}" placeholder="车辆号" title="车辆号">
      <input type="text" name="color_${this.itemCount}" placeholder="颜色" title="颜色">
      <div class="autocomplete-wrapper" style="position:relative;display:inline-block;">
        <input type="text" id="light_model_text_${this.itemCount}" placeholder="灯光" title="灯光" autocomplete="off" readonly style="width:80px;">
        <input type="hidden" name="light_model_id_${this.itemCount}" id="light_model_id_${this.itemCount}">
      </div>
      <button type="button" class="btn-delete-compact" onclick="CarriageManager.removeRow(this)" title="删除">×</button>
    `;
      container.appendChild(newItem);

      // 如果主表单已选择系列，设置新车厢项的系列并填充车型
      if (mainSeriesId) {
        const seriesSelect = newItem.querySelector(`select[name="series_${this.itemCount}"]`);
        seriesSelect.value = mainSeriesId;
        const modelSelect = newItem.querySelector(`select[name="model_${this.itemCount}"]`);
        Utils.filterModelsBySeries(mainSeriesId, modelSelect.id, window.carriageModelData);
      }

      // 初始化灯型号下拉
      const itemCount = this.itemCount;
      LightDropdownManager.init({
        textInputId: `light_model_text_${itemCount}`,
        hiddenInputId: `light_model_id_${itemCount}`,
        scaleSource: function() { return document.getElementById('scale')?.value || ''; },
        modelType: 'carriage',
        modelIdSource: function() {
          const modelSelect = document.getElementById(`model_${itemCount}`);
          return modelSelect?.value || '';
        },
        brandIdSource: function() { return document.getElementById('brand_id')?.value || ''; }
      });

      this.itemCount++;
    },

    /**
     * 处理系列选择变化
     * @param {HTMLSelectElement} seriesSelect - 系列选择框
     */
    handleSeriesChange(seriesSelect) {
      const row = seriesSelect.closest('.carriage-item-compact');
      const modelSelect = row.querySelector('select[name^="model_"]');
      Utils.filterModelsBySeries(seriesSelect.value, modelSelect.id, window.carriageModelData);
    },

    /**
     * 删除车厢行
     * @param {HTMLElement} button - 删除按钮
     */
    removeRow(button) {
      const container = document.getElementById('carriage-items');
      if (container && container.children.length > 0) {
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

  // 表单填充器（复制功能）
  const FormFiller = {
    /**
     * 从表格行复制数据到表单
     * @param {HTMLElement} button - 复制按钮
     * @param {Object} fieldMappings - 字段映射 { dataAttr: 'formFieldId' }
     *   对于自动完成字段，dataAttr 应该是存储 ID 的属性名（如 model_id）
     *   会自动查找对应的名称属性（如 data-model）来获取显示名称
     * @param {string} modalId - 可选，模态框ID，复制前先打开模态框
     */
    copyFromRow(button, fieldMappings, modalId) {
      // 如果指定了模态框ID，先打开模态框
      if (modalId) {
        ModalManager.open(modalId);
      }

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
          const textInput = wrapper.querySelector('input[type="text"]');
          const inputId = textInput?.id;
          if (inputId && AutocompleteManager.instances[inputId]) {
            // AutocompleteManager 管理的字段
            const nameAttr = dataAttr.replace('_id', '');
            const nameValue = row.dataset[nameAttr] || value;
            AutocompleteManager.setValue(inputId, value || '', nameValue || '');
          } else if (textInput) {
            // 非 AutocompleteManager 管理（如 LightDropdownManager），直接设置 DOM
            textInput.value = row.dataset[dataAttr.replace('_id', '_name')] || row.dataset[dataAttr + '_name'] || '';
            element.value = value || '';
          }
        } else {
          // 普通表单字段
          element.value = value || '';
        }
      });
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
      }, 'locomotive-add-modal');
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
        light_model_id: 'light_model_id',
        chip_interface_id: 'chip_interface_id',
        chip_model_id: 'chip_model_id',
        color: 'color',
        price: 'price',
        merchant_id: 'merchant_id',
        brand_id: 'brand_id',
        item_number: 'item_number',
        product_url: 'product_url',
        purchase_date: 'purchase_date'
      }, 'trainset-add-modal');
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
        light_model_id: 'light_model_id',
        price: 'price',
        merchant_id: 'merchant_id',
        brand_id: 'brand_id',
        item_number: 'item_number',
        product_url: 'product_url',
        purchase_date: 'purchase_date'
      }, 'locomotive-head-add-modal');
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
      }, 'carriage-add-modal');
    }
  };

  global.FormHelper = FormHelper;
  global.CarriageManager = CarriageManager;
  global.ModelForm = ModelForm;
  global.FormFiller = FormFiller;
})(window);
