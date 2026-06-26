/**
 * 火车模型管理系统 - 自定义导入向导 - 工作表映射步骤（步骤 3）
 *
 * 职责：工作表下拉、系统表选择、映射行管理、模板回填、映射进度。
 *
 * 依赖（按加载顺序）：
 *   wizard_core.js -> utils.js -> file_step.js -> sheet_mapping.js -> column_mapping.js -> preview_step.js
 * 所有模块通过共享的 window.CustomImportWizard 对象（别名 W）通信。
 */

(function (global) {
  'use strict';

  /** 共享向导对象（由 wizard_core.js 初始化） */
  let W = global.CustomImportWizard;

  W.renderSheetMapping = function() {
    const container = CustomImportWizard.elements.sheetMappingContainer;
    if (!container) return;

    // 清空容器
    W.clearContainer(container);

    const sheets = CustomImportWizard.parsedSheets;

    // 如果有模板配置，使用模板的 sheet 映射
    const templateMappings = CustomImportWizard.templateConfig
      ? (CustomImportWizard.templateConfig.sheet_mappings || [])
      : [];

    // 进度指示器
    const progressDiv = document.createElement('div');
    progressDiv.className = 'sheet-mapping-progress';
    progressDiv.style.marginBottom = 'var(--spacing-md)';
    progressDiv.style.color = '#666';
    container.appendChild(progressDiv);

    // 映射行容器
    const rowsContainer = document.createElement('div');
    rowsContainer.className = 'sheet-mapping-rows';
    container.appendChild(rowsContainer);

    // 为每个 sheet 创建映射行（初始只显示一个空行）
    if (sheets.length > 0) {
      // 创建第一个空行
      W.addSheetMappingRow(rowsContainer, null);
    }

    // 更新进度
    W.updateSheetMappingProgress();

    // 如果有模板配置，自动填充映射
    if (templateMappings.length > 0) {
      W.applyTemplateSheetMappings(rowsContainer, templateMappings);
    }

  };

  W.addSheetMappingRow = function(container, sheet) {
    const row = document.createElement('div');
    row.className = 'sheet-mapping-row';
    row.dataset.sheetName = sheet ? sheet.name : '';

    // 工作表名称下拉框
    const sheetSelect = document.createElement('select');
    sheetSelect.className = 'sheet-select';
    sheetSelect.name = 'sheet_name';
    sheetSelect.style.flex = '1';

    // 添加空选项
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '-- 选择工作表 --';
    sheetSelect.appendChild(emptyOption);

    // 添加可用 sheet 选项
    const availableSheets = W.getAvailableSheets(sheet ? sheet.name : null);
    availableSheets.forEach(function(s) {
      const option = document.createElement('option');
      option.value = s.name;
      option.textContent = s.name + ' (' + s.row_count + ' 行)';
      if (sheet && s.name === sheet.name) {
        option.selected = true;
      }
      sheetSelect.appendChild(option);
    });

    // 箭头
    const arrow = document.createElement('span');
    arrow.textContent = ' -> ';
    arrow.style.color = '#999';

    // 系统表下拉框
    const tableSelect = W.createTableSelect(null);

    // 删除按钮
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn btn-sm btn-secondary';
    deleteBtn.textContent = '删除';
    deleteBtn.onclick = function() {
      W.removeSheetMappingRow(row);
    };

    // 工作表选择变化事件
    sheetSelect.addEventListener('change', function() {
      row.dataset.sheetName = sheetSelect.value;
      W.updateSheetSelects();
      W.checkAndAddNewRow(container);
      W.updateSheetMappingProgress();
    });

    // 表选择变化事件
    tableSelect.addEventListener('change', function() {
      W.checkAndAddNewRow(container);
      W.updateSheetMappingProgress();
    });

    row.appendChild(sheetSelect);
    row.appendChild(arrow);
    row.appendChild(tableSelect);
    row.appendChild(deleteBtn);

    container.appendChild(row);

    return row;

  };

  W.createTableSelect = function(selectedValue) {
    const select = document.createElement('select');
    select.className = 'table-select';
    select.name = 'table_name';
    select.style.flex = '1';
    select.style.maxWidth = '200px';

    // 添加空选项
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '-- 跳过 --';
    select.appendChild(emptyOption);

    // 添加系统信息分组
    const systemGroup = document.createElement('optgroup');
    systemGroup.label = '系统信息 (建议先导入)';

    // 添加模型数据分组
    const modelGroup = document.createElement('optgroup');
    modelGroup.label = '模型数据 (依赖系统信息)';

    CustomImportWizard.systemTables.forEach(function(table) {
      const option = document.createElement('option');
      option.value = table.name;
      option.textContent = table.display_name;

      // 添加 tooltip
      if (table.tooltip) {
        option.title = table.tooltip;
      }

      if (table.category === 'system') {
        systemGroup.appendChild(option);
      } else {
        modelGroup.appendChild(option);
      }

      if (selectedValue && table.name === selectedValue) {
        option.selected = true;
      }
    });

    select.appendChild(systemGroup);
    select.appendChild(modelGroup);

    return select;

  };

  W.getAvailableSheets = function(currentSheet) {
    const selectedSheets = W.getSelectedSheetNames();
    return CustomImportWizard.parsedSheets.filter(function(sheet) {
      return sheet.name === currentSheet || selectedSheets.indexOf(sheet.name) === -1;
    });

  };

  W.getSelectedSheetNames = function() {
    const rows = CustomImportWizard.elements.sheetMappingContainer.querySelectorAll('.sheet-mapping-row');
    const selected = [];
    rows.forEach(function(row) {
      const select = row.querySelector('.sheet-select');
      if (select && select.value) {
        selected.push(select.value);
      }
    });
    return selected;

  };

  W.updateSheetSelects = function() {
    const rows = CustomImportWizard.elements.sheetMappingContainer.querySelectorAll('.sheet-mapping-row');
    rows.forEach(function(row) {
      const sheetSelect = row.querySelector('.sheet-select');
      if (!sheetSelect) return;

      const currentValue = sheetSelect.value;

      // 重建选项 - 使用 clearContainer 安全清空
      W.clearContainer(sheetSelect);

      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.textContent = '-- 选择工作表 --';
      sheetSelect.appendChild(emptyOption);

      const availableSheets = W.getAvailableSheets(currentValue);
      availableSheets.forEach(function(s) {
        const option = document.createElement('option');
        option.value = s.name;
        option.textContent = s.name + ' (' + s.row_count + ' 行)';
        if (s.name === currentValue) {
          option.selected = true;
        }
        sheetSelect.appendChild(option);
      });
    });

  };

  W.checkAndAddNewRow = function(container) {
    const rows = container.querySelectorAll('.sheet-mapping-row');
    const lastRow = rows[rows.length - 1];

    if (!lastRow) {
      W.addSheetMappingRow(container, null);
      return;
    }

    const sheetSelect = lastRow.querySelector('.sheet-select');
    const tableSelect = lastRow.querySelector('.table-select');

    // 如果最后一行有选择，添加新行
    if (sheetSelect && tableSelect && sheetSelect.value && tableSelect.value) {
      // 检查是否还有未映射的 sheet
      const availableSheets = W.getAvailableSheets(null);
      if (availableSheets.length > 0) {
        W.addSheetMappingRow(container, null);
      }
    }

  };

  W.removeSheetMappingRow = function(row) {
    const container = row.parentElement;
    const rows = container.querySelectorAll('.sheet-mapping-row');

    // 至少保留一行
    if (rows.length <= 1) {
      // 清空选择而不是删除
      const sheetSelect = row.querySelector('.sheet-select');
      const tableSelect = row.querySelector('.table-select');
      if (sheetSelect) sheetSelect.value = '';
      if (tableSelect) tableSelect.value = '';
    } else {
      row.remove();
    }

    W.updateSheetSelects();
    W.updateSheetMappingProgress();

  };

  W.updateSheetMappingProgress = function() {
    const progressDiv = CustomImportWizard.elements.sheetMappingContainer.querySelector('.sheet-mapping-progress');
    if (!progressDiv) return;

    const totalSheets = CustomImportWizard.parsedSheets ? CustomImportWizard.parsedSheets.length : 0;
    const mappings = W.getSheetMappings();
    const mappedCount = mappings.filter(function(m) {
      return m.table_name !== '';
    }).length;

    progressDiv.textContent = '您的文件包含 ' + totalSheets + ' 个工作表，已配置 ' + mappedCount + ' 个';

    // 检查是否所有 sheet 都已映射
    if (mappedCount === totalSheets) {
      progressDiv.style.color = 'var(--color-success)';
    } else {
      progressDiv.style.color = '#666';
    }

  };

  W.getSheetMappings = function() {
    const rows = CustomImportWizard.elements.sheetMappingContainer.querySelectorAll('.sheet-mapping-row');
    const mappings = [];

    rows.forEach(function(row) {
      const sheetSelect = row.querySelector('.sheet-select');
      const tableSelect = row.querySelector('.table-select');

      if (sheetSelect && tableSelect && sheetSelect.value) {
        mappings.push({
          sheet_name: sheetSelect.value,
          table_name: tableSelect.value
        });
      }
    });

    return mappings;

  };

  W.applyTemplateSheetMappings = function(container, templateMappings) {
    // 清空现有行
    W.clearContainer(container);

    // 添加进度指示器
    const progressDiv = document.createElement('div');
    progressDiv.className = 'sheet-mapping-progress';
    progressDiv.style.marginBottom = 'var(--spacing-md)';
    progressDiv.style.color = '#666';
    container.appendChild(progressDiv);

    const rowsContainer = document.createElement('div');
    rowsContainer.className = 'sheet-mapping-rows';
    container.appendChild(rowsContainer);

    // 创建映射行
    templateMappings.forEach(function(mapping) {
      const sheet = CustomImportWizard.parsedSheets.find(function(s) {
        return s.name === mapping.sheet_name;
      });

      if (sheet) {
        const row = W.addSheetMappingRow(rowsContainer, sheet);
        const tableSelect = row.querySelector('.table-select');
        if (tableSelect) {
          tableSelect.value = mapping.table_name;
        }
      }
    });

    // 添加一个空行以便添加更多映射
    W.addSheetMappingRow(rowsContainer, null);

    W.updateSheetSelects();
    W.updateSheetMappingProgress();

  };

})(this);
