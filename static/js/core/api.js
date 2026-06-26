/**
 * 火车模型管理系统 - 通用工具与 AJAX 封装模块
 *
 * 提供：
 *   - Utils：filterModelsBySeries / autoFill / showTab 等通用工具
 *   - Api：post / postForm 封装
 */
(function (global) {
  'use strict';

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

  global.Utils = Utils;
  global.Api = Api;
})(window);
