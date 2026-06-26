/**
 * 火车模型管理系统 - 全局函数兼容层
 *
 * 将所有原 utils.js 中的全局函数显式挂到 window，供模板 onclick 直接调用。
 * 模板的 onclick="copyLocomotive(this)" / onclick="addCarriageRow()" 等都依赖这些全局函数。
 *
 * 依赖（按加载顺序）：modal.js、api.js、dropdowns.js、tables.js、forms.js、file_manager.js
 */
(function (global) {
  'use strict';

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
    TableManager.reset(tableId);
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

  /**
   * 搜索产品（打开品牌搜索链接）
   * @param {HTMLElement} btn - 触发的按钮元素（未使用，但保留以便于调用）
   * @param {string} searchUrl - 搜索URL模板，{query}为占位符
   * @param {string} itemNumber - 货号/搜索关键词
   */
  function searchProduct(btn, searchUrl, itemNumber) {
    if (!searchUrl || !itemNumber) return;
    var url = searchUrl.replace('{query}', encodeURIComponent(itemNumber));
    window.open(url, '_blank');
  }

  /**
   * 通用文件上传函数
   * @param {string} modelType - 模型类型（locomotive/carriage/trainset/locomotive_head）
   * @param {number|string} modelId - 模型ID
   * @param {string} fileType - 文件类型（image/manual/function_table）
   * @param {File} file - 要上传的文件对象
   * @returns {Promise} 上传结果的 Promise
   */
  function uploadModelFile(modelType, modelId, fileType, file) {
    return new Promise(function(resolve, reject) {
      var formData = new FormData();
      formData.append('model_type', modelType);
      formData.append('model_id', modelId);
      formData.append('file_type', fileType);
      formData.append('file', file);

      fetch('/api/files/upload', {
        method: 'POST',
        body: formData
      }).then(function(response) {
        return response.json();
      }).then(function(data) {
        if (data.success) {
          resolve(data);
        } else {
          reject(new Error(data.error || '上传失败'));
        }
      }).catch(reject);
    });
  }

  // 显式挂到 window，保持全局函数兼容
  global.filterLocomotiveModelsBySeries = filterLocomotiveModelsBySeries;
  global.filterTrainsetModelsBySeries = filterTrainsetModelsBySeries;
  global.handleLocomotiveSeriesChange = handleLocomotiveSeriesChange;
  global.handleTrainsetSeriesChange = handleTrainsetSeriesChange;
  global.autoFillLocomotive = autoFillLocomotive;
  global.autoFillTrainset = autoFillTrainset;
  global.addCarriageRow = addCarriageRow;
  global.removeCarriageRow = removeCarriageRow;
  global.handleSeriesChange = handleSeriesChange;
  global.showTab = showTab;
  global.submitFormAjax = submitFormAjax;
  global.filterModelsBySeries = filterModelsBySeries;
  global.generateSeriesOptions = generateSeriesOptions;
  global.initTableSortFilter = initTableSortFilter;
  global.resetTable = resetTable;
  global.initAutocomplete = initAutocomplete;
  global.setAutocompleteOptions = setAutocompleteOptions;
  global.setAutocompleteValue = setAutocompleteValue;
  global.copyLocomotive = copyLocomotive;
  global.copyTrainset = copyTrainset;
  global.copyLocomotiveHead = copyLocomotiveHead;
  global.copyCarriage = copyCarriage;
  global.searchProduct = searchProduct;
  global.uploadModelFile = uploadModelFile;
})(window);
