/**
 * 火车模型管理系统 - 表格排序筛选模块
 *
 * 提供 TableManager：表格列头排序 + 列筛选 + 重置。
 */
(function (global) {
  'use strict';

  // 表格排序筛选管理器
  const TableManager = {
    // 存储每个表格实例的状态
    instances: new Map(),

    /**
     * 初始化表格
     * @param {string} tableId - 表格 ID
     */
    init(tableId) {
      const table = document.getElementById(tableId);
      if (!table) return;

      const tbody = table.querySelector('tbody');
      const originalRows = Array.from(tbody.querySelectorAll('tr'));

      // 创建该表格的独立状态
      const state = {
        table: table,
        tbody: tbody,
        originalRows: originalRows,
        sortColumn: null,
        sortDirection: 'asc',
        filters: {}
      };

      this.instances.set(tableId, state);
      this.setupSortHeaders(tableId);
      this.setupFilterHeaders(tableId);
    },

    /**
     * 设置排序表头
     * @param {string} tableId - 表格 ID
     */
    setupSortHeaders(tableId) {
      const state = this.instances.get(tableId);
      if (!state) return;

      const headers = state.table.querySelectorAll('th[data-sort]');
      headers.forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => this.handleSort(tableId, th));

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
     * @param {string} tableId - 表格 ID
     */
    setupFilterHeaders(tableId) {
      const state = this.instances.get(tableId);
      if (!state) return;

      const headers = state.table.querySelectorAll('th[data-filter]');
      headers.forEach(th => {
        const filterKey = th.dataset.filter;
        const uniqueValues = this.getUniqueValues(tableId, filterKey);

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

        select.addEventListener('change', (e) => this.handleFilter(tableId, filterKey, e.target.value));

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
     * @param {string} tableId - 表格 ID
     * @param {string} key - 列标识
     * @returns {string[]}
     */
    getUniqueValues(tableId, key) {
      const state = this.instances.get(tableId);
      if (!state) return [];

      const values = new Set();
      state.originalRows.forEach(row => {
        const value = row.dataset[key];
        if (value !== undefined && value !== '') {
          values.add(value);
        }
      });
      return Array.from(values).sort();
    },

    /**
     * 处理排序
     * @param {string} tableId - 表格 ID
     * @param {HTMLElement} th - 被点击的表头
     */
    handleSort(tableId, th) {
      const state = this.instances.get(tableId);
      if (!state) return;

      const column = th.dataset.sort;

      // 切换排序方向
      if (state.sortColumn === column) {
        state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortColumn = column;
        state.sortDirection = 'asc';
      }

      // 更新排序指示器
      this.updateSortIndicators(tableId);

      // 执行排序
      this.applySortAndFilter(tableId);
    },

    /**
     * 更新排序指示器
     * @param {string} tableId - 表格 ID
     */
    updateSortIndicators(tableId) {
      const state = this.instances.get(tableId);
      if (!state) return;

      const headers = state.table.querySelectorAll('th[data-sort]');
      headers.forEach(th => {
        const indicator = th.querySelector('.sort-indicator');
        if (th.dataset.sort === state.sortColumn) {
          indicator.textContent = state.sortDirection === 'asc' ? '▲' : '▼';
          indicator.className = 'sort-indicator active';
        } else {
          indicator.textContent = '⇅';
          indicator.className = 'sort-indicator';
        }
      });
    },

    /**
     * 处理筛选
     * @param {string} tableId - 表格 ID
     * @param {string} key - 列标识
     * @param {string} value - 筛选值
     */
    handleFilter(tableId, key, value) {
      const state = this.instances.get(tableId);
      if (!state) return;

      if (value === '') {
        delete state.filters[key];
      } else {
        state.filters[key] = value;
      }
      this.applySortAndFilter(tableId);
    },

    /**
     * 执行排序和筛选
     * @param {string} tableId - 表格 ID
     */
    applySortAndFilter(tableId) {
      const state = this.instances.get(tableId);
      if (!state) return;

      // 筛选
      let filteredRows = state.originalRows.filter(row => {
        return Object.entries(state.filters).every(([key, value]) => {
          return row.dataset[key] === value;
        });
      });

      // 排序
      if (state.sortColumn) {
        filteredRows.sort((a, b) => {
          const aVal = a.dataset[state.sortColumn] || '';
          const bVal = b.dataset[state.sortColumn] || '';

          // 尝试数字比较
          const aNum = parseFloat(aVal);
          const bNum = parseFloat(bVal);
          if (!isNaN(aNum) && !isNaN(bNum)) {
            return state.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
          }

          // 字符串比较
          const compareResult = aVal.localeCompare(bVal, 'zh-CN');
          return state.sortDirection === 'asc' ? compareResult : -compareResult;
        });
      }

      // 重新渲染
      while (state.tbody.firstChild) {
        state.tbody.removeChild(state.tbody.firstChild);
      }
      filteredRows.forEach(row => state.tbody.appendChild(row.cloneNode(true)));
    },

    /**
     * 重置表格
     * @param {string} tableId - 表格 ID
     */
    reset(tableId) {
      const state = this.instances.get(tableId);
      if (!state) return;

      state.sortColumn = null;
      state.sortDirection = 'asc';
      state.filters = {};
      this.updateSortIndicators(tableId);

      // 重置筛选下拉框
      state.table.querySelectorAll('.column-filter').forEach(select => {
        select.value = '';
      });

      // 恢复原始顺序
      while (state.tbody.firstChild) {
        state.tbody.removeChild(state.tbody.firstChild);
      }
      state.originalRows.forEach(row => state.tbody.appendChild(row.cloneNode(true)));
    }
  };

  global.TableManager = TableManager;
})(window);
