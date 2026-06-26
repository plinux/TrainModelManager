/**
 * 火车模型管理系统 - 主 JavaScript 文件
 *
 * 此文件依赖 static/js/core/* 模块提供的基础功能
 * 包含页面特定的初始化和辅助函数
 */

// 等待 DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  // 初始化页面
  initPage();
});

/**
 * 初始化页面
 */
function initPage() {
  // 根据页面类型初始化相应的功能
  const currentPage = getCurrentPage();

  switch (currentPage) {
    case 'locomotive':
      initLocomotivePage();
      break;
    case 'trainset':
      initTrainsetPage();
      break;
    case 'carriage':
      initCarriagePage();
      break;
  }
}

/**
 * 获取当前页面类型
 * @returns {string|null}
 */
function getCurrentPage() {
  const path = window.location.pathname;
  if (path.includes('/locomotive')) return 'locomotive';
  if (path.includes('/trainset')) return 'trainset';
  if (path.includes('/carriage')) return 'carriage';
  return null;
}

/**
 * 初始化机车页面
 */
function initLocomotivePage() {
  // 如果系列数据存在，初始化系列选择事件
  if (window.locomotiveSeriesData) {
    const seriesSelect = document.getElementById('series_id');
    if (seriesSelect) {
      seriesSelect.addEventListener('change', function() {
        ModelForm.handleLocomotiveSeriesChange();
      });
    }
  }
}

/**
 * 初始化动车组页面
 */
function initTrainsetPage() {
  // 如果系列数据存在，初始化系列选择事件
  if (window.trainsetSeriesData) {
    const seriesSelect = document.getElementById('series_id');
    if (seriesSelect) {
      seriesSelect.addEventListener('change', function() {
        ModelForm.handleTrainsetSeriesChange();
      });
    }
  }
}

/**
 * 初始化车厢页面
 */
function initCarriagePage() {
  // 初始化车厢项计数
  if (document.getElementById('carriage-items')) {
    const existingItems = document.querySelectorAll('.carriage-item');
    CarriageManager.itemCount = existingItems.length;
  }
}

// ========== 兼容函数说明 ==========
//
// 历史上这些函数定义在 utils.js 中。utils.js 已被拆分为
// static/js/core/* 下的 7 个模块（modal/api/dropdowns/tables/forms/file_manager/compat），
// 全局函数现统一在 core/compat.js 中显式挂到 window。
// 如需使用，直接调用对应的全局函数即可。

/*
 * 以下函数现在定义在 core/compat.js（实现委托给 core/* 中的具体对象）：
 *
 * - filterLocomotiveModelsBySeries(seriesId)
 * - filterTrainsetModelsBySeries(seriesId)
 * - handleLocomotiveSeriesChange()
 * - handleTrainsetSeriesChange()
 * - autoFillLocomotive()
 * - autoFillTrainset()
 * - addCarriageRow()
 * - removeCarriageRow(button)
 * - handleSeriesChange(seriesSelect)
 * - showTab(tabId)
 * - submitFormAjax(form, apiUrl)
 * - filterModelsBySeries(seriesId, modelSelect)
 * - generateSeriesOptions()
 */
