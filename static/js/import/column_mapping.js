/**
 * 火车模型管理系统 - 自定义导入向导 - 列映射步骤（步骤 4）
 *
 * 职责：列映射标签页、Excel 列到系统字段映射行、冲突模式选择、
 * 车厢模型特殊选项、列映射进度。
 *
 * 注意：renderColumnMapping 依赖 sheet_mapping.js 提供的 W.getSheetMappings。
 *
 * 依赖（按加载顺序）：
 *   wizard_core.js -> utils.js -> file_step.js -> sheet_mapping.js -> column_mapping.js -> preview_step.js
 * 所有模块通过共享的 window.CustomImportWizard 对象（别名 W）通信。
 */

(function (global) {
  'use strict';

  /** 共享向导对象（由 wizard_core.js 初始化） */
  let W = global.CustomImportWizard;

  W.renderColumnMapping = function() {
    const tabsContainer = CustomImportWizard.elements.columnMappingTabs;
    const container = CustomImportWizard.elements.columnMappingContainer;
    if (!tabsContainer || !container) return;

    // 清空容器
    W.clearContainer(tabsContainer);
    W.clearContainer(container);

    // 获取已映射的 sheet（排除了跳过的）
    const mappings = W.getSheetMappings().filter(function(m) {
      return m.table_name !== '';
    });

    if (mappings.length === 0) {
      const msg = document.createElement('p');
      msg.className = 'step-desc';
      msg.textContent = '没有需要配置列映射的工作表。';
      container.appendChild(msg);
      return;
    }

    // 初始化列映射配置
    mappings.forEach(function(mapping) {
      if (!CustomImportWizard.columnMappings[mapping.table_name]) {
        CustomImportWizard.columnMappings[mapping.table_name] = {
          columns: [],
          conflict_mode: 'skip',
          carriage_options: {
            set_detection_mode: 'merged', // 'merged' or 'row'
            unmerged_field_value: 'first' // 'first' or 'last'
          }
        };
      }
    });

    // 创建标签页
    mappings.forEach(function(mapping, index) {
      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'column-mapping-tab' + (index === 0 ? ' active' : '');
      tab.dataset.tableName = mapping.table_name;
      tab.dataset.sheetName = mapping.sheet_name;
      tab.textContent = W.getTableDisplayName(mapping.table_name);

      tab.addEventListener('click', function() {
        W.switchColumnMappingTab(mapping.table_name, mapping.sheet_name);
      });

      tabsContainer.appendChild(tab);
    });

    // 显示第一个标签页的内容
    const firstMapping = mappings[0];
    W.renderColumnMappingContent(firstMapping.table_name, firstMapping.sheet_name);

    // 更新进度指示器
    W.updateColumnMappingProgress();

  };

  W.switchColumnMappingTab = function(tableName, sheetName) {
    // 先保存当前标签页的映射配置
    W.saveCurrentColumnMappings();

    // 更新标签页状态
    const tabs = CustomImportWizard.elements.columnMappingTabs.querySelectorAll('.column-mapping-tab');
    tabs.forEach(function(tab) {
      tab.classList.remove('active');
      if (tab.dataset.tableName === tableName) {
        tab.classList.add('active');
      }
    });

    // 渲染对应内容
    W.renderColumnMappingContent(tableName, sheetName);

  };

  W.saveCurrentColumnMappings = function() {
    const activeTab = CustomImportWizard.elements.columnMappingTabs.querySelector('.column-mapping-tab.active');
    if (!activeTab) return;

    const tableName = activeTab.dataset.tableName;
    if (!tableName) return;

    // 获取当前 DOM 中的映射配置
    const tbody = CustomImportWizard.elements.columnMappingContainer.querySelector('.column-mapping-tbody');
    if (!tbody) return;

    const columns = [];
    const rows = tbody.querySelectorAll('.column-mapping-row');

    rows.forEach(function(row) {
      const excelSelect = row.querySelector('.excel-column-select');
      const systemSelect = row.querySelector('.system-field-select');

      if (excelSelect && systemSelect && excelSelect.value && systemSelect.value) {
        columns.push({
          source: excelSelect.value,
          target: systemSelect.value
        });
      }
    });

    // 获取冲突模式
    const conflictRadio = CustomImportWizard.elements.columnMappingContainer.querySelector('input[name="conflict-mode-' + tableName + '"]:checked');
    const conflictMode = conflictRadio ? conflictRadio.value : 'skip';

    // 获取车厢选项（如果是车厢表）
    let carriageOptions = null;
    if (tableName === 'carriage') {
      const detectionRadio = document.querySelector('input[name="carriage-detection-mode"]:checked');
      carriageOptions = {
        set_detection_mode: detectionRadio ? detectionRadio.value : 'merged',
        unmerged_field_value: 'first'
      };
    }

    // 保存到全局配置
    if (!CustomImportWizard.columnMappings[tableName]) {
      CustomImportWizard.columnMappings[tableName] = { columns: [], conflict_mode: 'skip' };
    }
    CustomImportWizard.columnMappings[tableName].columns = columns;
    CustomImportWizard.columnMappings[tableName].conflict_mode = conflictMode;
    if (carriageOptions) {
      CustomImportWizard.columnMappings[tableName].carriage_options = carriageOptions;
    }

  };

  W.renderColumnMappingContent = function(tableName, sheetName) {
    const container = CustomImportWizard.elements.columnMappingContainer;
    if (!container) return;

    W.clearContainer(container);

    // 获取表配置
    const tableConfig = CustomImportWizard.systemTables.find(function(t) {
      return t.name === tableName;
    });

    // 从 SYSTEM_TABLES 获取详细字段配置（需要在运行时获取）
    const systemTableConfig = W.getSystemTableConfig(tableName);
    if (!systemTableConfig) {
      const msg = document.createElement('p');
      msg.className = 'text-danger';
      msg.textContent = '无法获取表配置: ' + tableName;
      container.appendChild(msg);
      return;
    }

    // 获取 Excel 列名
    const sheetInfo = CustomImportWizard.parsedSheets.find(function(s) {
      return s.name === sheetName;
    });
    const excelColumns = sheetInfo ? sheetInfo.columns : [];

    // 获取当前映射配置
    const mappingConfig = CustomImportWizard.columnMappings[tableName] || {
      columns: [],
      conflict_mode: 'skip'
    };

    // 创建进度指示器
    const progressDiv = document.createElement('div');
    progressDiv.className = 'column-mapping-progress';
    progressDiv.style.marginBottom = 'var(--spacing-md)';
    progressDiv.style.color = '#666';
    container.appendChild(progressDiv);

    // 如果是车厢模型，显示额外选项
    if (tableName === 'carriage') {
      const carriageOptionsDiv = W.createCarriageOptions(mappingConfig);
      container.appendChild(carriageOptionsDiv);
    }

    // 创建映射表格
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-wrapper';

    const table = document.createElement('table');
    table.className = 'column-mapping-table';

    // 表头
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const thExcel = document.createElement('th');
    thExcel.textContent = 'Excel 列名';
    headerRow.appendChild(thExcel);

    const thArrow = document.createElement('th');
    thArrow.textContent = '';
    thArrow.style.width = '40px';
    headerRow.appendChild(thArrow);

    const thSystem = document.createElement('th');
    thSystem.innerHTML = '系统字段 <span class="text-muted">(带 * 为必填)</span>';
    headerRow.appendChild(thSystem);

    const thAction = document.createElement('th');
    thAction.textContent = '操作';
    thAction.style.width = '60px';
    headerRow.appendChild(thAction);

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // 表体
    const tbody = document.createElement('tbody');
    tbody.className = 'column-mapping-tbody';

    // 添加现有的映射行
    mappingConfig.columns.forEach(function(colMapping) {
      const row = W.createColumnMappingRow(excelColumns, systemTableConfig, colMapping, tbody);
      tbody.appendChild(row);
    });

    // 添加一个空行用于添加新映射
    const emptyRow = W.createColumnMappingRow(excelColumns, systemTableConfig, null, tbody);
    tbody.appendChild(emptyRow);

    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    container.appendChild(tableWrapper);

    // 创建冲突模式选择
    const conflictDiv = W.createConflictModeSelector(tableName, mappingConfig.conflict_mode);
    container.appendChild(conflictDiv);

    // 更新 Excel 列下拉菜单（禁用已选择的列）
    W.updateExcelColumnDropdowns(tbody, excelColumns);
    // 更新系统字段下拉菜单（禁用已选择的字段）
    W.updateSystemFieldDropdowns(tbody);

    // 更新进度
    W.updateColumnMappingProgress();

  };

  W.createCarriageOptions = function(mappingConfig) {
    const div = document.createElement('div');
    div.className = 'carriage-options';
    div.style.marginBottom = 'var(--spacing-lg)';
    div.style.padding = 'var(--spacing-md)';
    div.style.background = '#fff8e1';
    div.style.border = '1px solid var(--color-warning)';
    div.style.borderRadius = 'var(--border-radius)';

    const title = document.createElement('h4');
    title.textContent = '车厢模型特殊选项';
    title.style.marginTop = '0';
    title.style.marginBottom = 'var(--spacing-sm)';
    title.style.color = '#856404';
    div.appendChild(title);

    const carriageOptions = mappingConfig.carriage_options || {
      set_detection_mode: 'merged',
      unmerged_field_value: 'first'
    };

    // 套装识别方式
    const detectionLabel = document.createElement('label');
    detectionLabel.className = 'radio-label';
    detectionLabel.style.marginBottom = 'var(--spacing-sm)';
    detectionLabel.innerHTML = '<strong>套装识别方式：</strong>';
    div.appendChild(detectionLabel);

    const detectionOptions = [
      { value: 'merged', label: '按合并单元格识别套装（推荐）' },
      { value: 'row', label: '每行作为一个独立套装' }
    ];

    detectionOptions.forEach(function(opt) {
      const label = document.createElement('label');
      label.className = 'radio-label';
      label.style.marginLeft = 'var(--spacing-md)';

      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'carriage-detection-mode';
      radio.value = opt.value;
      radio.checked = carriageOptions.set_detection_mode === opt.value;

      radio.addEventListener('change', function() {
        if (!CustomImportWizard.columnMappings.carriage) {
          CustomImportWizard.columnMappings.carriage = { columns: [], conflict_mode: 'skip', carriage_options: {} };
        }
        CustomImportWizard.columnMappings.carriage.carriage_options = CustomImportWizard.columnMappings.carriage.carriage_options || {};
        CustomImportWizard.columnMappings.carriage.carriage_options.set_detection_mode = opt.value;
      });

      label.appendChild(radio);
      label.appendChild(document.createTextNode(' ' + opt.label));
      div.appendChild(label);
    });

    // 未合并公共字段取值
    const valueLabel = document.createElement('label');
    valueLabel.className = 'radio-label';
    valueLabel.style.marginTop = 'var(--spacing-sm)';
    valueLabel.style.marginBottom = 'var(--spacing-xs)';
    valueLabel.innerHTML = '<strong>未合并公共字段取值：</strong>';
    div.appendChild(valueLabel);

    const valueOptions = [
      { value: 'first', label: '取第一行的值（默认）' },
      { value: 'last', label: '取最后一行的值' }
    ];

    valueOptions.forEach(function(opt) {
      const label = document.createElement('label');
      label.className = 'radio-label';
      label.style.marginLeft = 'var(--spacing-md)';

      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'carriage-unmerged-value';
      radio.value = opt.value;
      radio.checked = carriageOptions.unmerged_field_value === opt.value;

      radio.addEventListener('change', function() {
        if (!CustomImportWizard.columnMappings.carriage) {
          CustomImportWizard.columnMappings.carriage = { columns: [], conflict_mode: 'skip', carriage_options: {} };
        }
        CustomImportWizard.columnMappings.carriage.carriage_options = CustomImportWizard.columnMappings.carriage.carriage_options || {};
        CustomImportWizard.columnMappings.carriage.carriage_options.unmerged_field_value = opt.value;
      });

      label.appendChild(radio);
      label.appendChild(document.createTextNode(' ' + opt.label));
      div.appendChild(label);
    });

    return div;

  };

  W.createColumnMappingRow = function(excelColumns, tableConfig, existingMapping, tbody) {
    const row = document.createElement('tr');
    row.className = 'column-mapping-row';

    // Excel 列选择
    const tdExcel = document.createElement('td');
    const excelSelect = document.createElement('select');
    excelSelect.className = 'excel-column-select';

    // 添加空选项
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '-- 选择 Excel 列 --';
    excelSelect.appendChild(emptyOption);

    // 添加 Excel 列选项
    excelColumns.forEach(function(col) {
      const option = document.createElement('option');
      option.value = col;
      option.textContent = col;
      if (existingMapping && existingMapping.source === col) {
        option.selected = true;
      }
      excelSelect.appendChild(option);
    });

    tdExcel.appendChild(excelSelect);
    row.appendChild(tdExcel);

    // 箭头
    const tdArrow = document.createElement('td');
    tdArrow.textContent = '→';
    tdArrow.style.textAlign = 'center';
    tdArrow.style.color = '#999';
    row.appendChild(tdArrow);

    // 系统字段选择
    const tdSystem = document.createElement('td');
    const systemSelect = document.createElement('select');
    systemSelect.className = 'system-field-select';

    // 添加空选项
    const emptySystemOption = document.createElement('option');
    emptySystemOption.value = '';
    emptySystemOption.textContent = '-- 选择系统字段 --';
    systemSelect.appendChild(emptySystemOption);

    // 添加系统字段选项（按类别分组）
    const fields = tableConfig.fields || [];

    // 必填字段分组
    const requiredGroup = document.createElement('optgroup');
    requiredGroup.label = '必填字段';

    // 可选字段分组
    const optionalGroup = document.createElement('optgroup');
    optionalGroup.label = '可选字段';

    fields.forEach(function(field) {
      const option = document.createElement('option');
      option.value = field.name;

      // 显示名称
      let displayText = field.display || field.name;

      // 标记必填
      if (field.required) {
        displayText += ' *';
      }

      // 标记引用
      if (field.ref) {
        displayText += ' (引用: ' + W.getTableDisplayName(field.ref) + ')';
      }

      option.textContent = displayText;

      // tooltip
      if (field.ref) {
        option.title = '此字段引用 ' + W.getTableDisplayName(field.ref) + ' 表，请确保该表已先导入';
      }

      if (field.required) {
        requiredGroup.appendChild(option);
      } else {
        optionalGroup.appendChild(option);
      }

      if (existingMapping && existingMapping.target === field.name) {
        option.selected = true;
      }
    });

    if (requiredGroup.children.length > 0) {
      systemSelect.appendChild(requiredGroup);
    }
    if (optionalGroup.children.length > 0) {
      systemSelect.appendChild(optionalGroup);
    }

    tdSystem.appendChild(systemSelect);
    row.appendChild(tdSystem);

    // 删除按钮
    const tdAction = document.createElement('td');
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn btn-sm btn-secondary';
    deleteBtn.textContent = '删除';
    deleteBtn.onclick = function() {
      W.removeColumnMappingRow(row, tbody);
    };
    tdAction.appendChild(deleteBtn);
    row.appendChild(tdAction);

    // 事件处理
    excelSelect.addEventListener('change', function() {
      W.checkAndAddNewColumnRow(tbody, excelColumns, tableConfig);
      W.updateExcelColumnDropdowns(tbody, excelColumns);
      W.updateColumnMappingProgress();
    });

    systemSelect.addEventListener('change', function() {
      W.checkAndAddNewColumnRow(tbody, excelColumns, tableConfig);
      W.updateExcelColumnDropdowns(tbody, excelColumns);
      W.updateSystemFieldDropdowns(tbody);
      W.updateColumnMappingProgress();
    });

    return row;

  };

  W.getSelectedExcelColumns = function(tbody, excludeRow) {
    const selected = [];
    const rows = tbody.querySelectorAll('.column-mapping-row');
    rows.forEach(function(row) {
      if (excludeRow && row === excludeRow) return;
      const select = row.querySelector('.excel-column-select');
      if (select && select.value) {
        selected.push(select.value);
      }
    });
    return selected;

  };

  W.getSelectedSystemFields = function(tbody, excludeRow) {
    const selected = [];
    const rows = tbody.querySelectorAll('.column-mapping-row');
    rows.forEach(function(row) {
      if (excludeRow && row === excludeRow) return;
      const select = row.querySelector('.system-field-select');
      if (select && select.value) {
        selected.push(select.value);
      }
    });
    return selected;

  };

  W.updateExcelColumnDropdowns = function(tbody, excelColumns) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    rows.forEach(function(row) {
      const select = row.querySelector('.excel-column-select');
      if (!select) return;

      const currentValue = select.value;
      const selectedInOtherRows = W.getSelectedExcelColumns(tbody, row);

      // 更新选项的禁用状态
      select.querySelectorAll('option').forEach(function(option) {
        if (option.value === '') return; // 空选项不禁用
        if (option.value === currentValue) {
          option.disabled = false;
        } else {
          option.disabled = selectedInOtherRows.indexOf(option.value) !== -1;
        }
      });
    });

  };

  W.updateSystemFieldDropdowns = function(tbody) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    rows.forEach(function(row) {
      const select = row.querySelector('.system-field-select');
      if (!select) return;

      const currentValue = select.value;
      const selectedInOtherRows = W.getSelectedSystemFields(tbody, row);

      // 更新选项的禁用状态
      select.querySelectorAll('option').forEach(function(option) {
        if (option.value === '') return; // 空选项不禁用
        if (option.value === currentValue) {
          option.disabled = false;
        } else {
          option.disabled = selectedInOtherRows.indexOf(option.value) !== -1;
        }
      });
    });

  };

  W.checkAndAddNewColumnRow = function(tbody, excelColumns, tableConfig) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    const lastRow = rows[rows.length - 1];

    if (!lastRow) return;

    const excelSelect = lastRow.querySelector('.excel-column-select');
    const systemSelect = lastRow.querySelector('.system-field-select');

    // 如果最后一行有选择，添加新行
    if (excelSelect && systemSelect && excelSelect.value && systemSelect.value) {
      const newRow = W.createColumnMappingRow(excelColumns, tableConfig, null, tbody);
      tbody.appendChild(newRow);
    }

  };

  W.removeColumnMappingRow = function(row, tbody) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    const excelColumns = [];

    // 获取 Excel 列（从第一行的数据属性或重新获取）
    const firstRowSelect = rows[0] ? rows[0].querySelector('.excel-column-select') : null;
    if (firstRowSelect) {
      firstRowSelect.querySelectorAll('option').forEach(function(opt) {
        if (opt.value) excelColumns.push(opt.value);
      });
    }

    if (rows.length <= 1) {
      // 只有一行时，清空选择
      const excelSelect = row.querySelector('.excel-column-select');
      const systemSelect = row.querySelector('.system-field-select');
      if (excelSelect) excelSelect.value = '';
      if (systemSelect) systemSelect.value = '';
    } else {
      row.remove();
    }

    // 更新下拉菜单
    W.updateExcelColumnDropdowns(tbody, excelColumns);
    W.updateSystemFieldDropdowns(tbody);
    W.updateColumnMappingProgress();

  };

  W.createConflictModeSelector = function(tableName, currentMode) {
    const div = document.createElement('div');
    div.className = 'conflict-mode-selector';
    div.style.marginTop = 'var(--spacing-lg)';
    div.style.padding = 'var(--spacing-md)';
    div.style.background = '#f8f9fa';
    div.style.borderRadius = 'var(--border-radius)';

    const title = document.createElement('h4');
    title.textContent = '冲突处理方式';
    title.style.marginTop = '0';
    title.style.marginBottom = 'var(--spacing-sm)';
    div.appendChild(title);

    const desc = document.createElement('p');
    desc.className = 'step-desc';
    desc.textContent = '当导入的数据与现有数据冲突时的处理方式：';
    div.appendChild(desc);

    const modes = [
      { value: 'skip', label: '跳过冲突（保留现有数据）', desc: '遇到冲突的记录时跳过，不导入该记录' },
      { value: 'overwrite', label: '覆盖冲突（更新现有数据）', desc: '遇到冲突的记录时用新数据覆盖现有数据' }
    ];

    modes.forEach(function(mode) {
      const label = document.createElement('label');
      label.className = 'radio-label';

      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'conflict-mode-' + tableName;
      radio.value = mode.value;
      radio.checked = currentMode === mode.value;

      radio.addEventListener('change', function() {
        if (CustomImportWizard.columnMappings[tableName]) {
          CustomImportWizard.columnMappings[tableName].conflict_mode = mode.value;
        }
      });

      label.appendChild(radio);

      const span = document.createElement('span');
      span.innerHTML = '<strong>' + mode.label + '</strong><br><small class="text-muted">' + mode.desc + '</small>';
      label.appendChild(span);

      div.appendChild(label);
    });

    return div;

  };

  W.updateColumnMappingProgress = function() {
    const activeTab = CustomImportWizard.elements.columnMappingTabs.querySelector('.column-mapping-tab.active');
    if (!activeTab) return;

    const tableName = activeTab.dataset.tableName;
    const tableConfig = W.getSystemTableConfig(tableName);
    if (!tableConfig) return;

    const container = CustomImportWizard.elements.columnMappingContainer.querySelector('.column-mapping-progress');
    if (!container) return;

    // 获取当前映射
    const rows = CustomImportWizard.elements.columnMappingContainer.querySelectorAll('.column-mapping-row');
    let mappedCount = 0;
    const mappedTargets = [];

    rows.forEach(function(row) {
      const excelSelect = row.querySelector('.excel-column-select');
      const systemSelect = row.querySelector('.system-field-select');
      if (excelSelect && systemSelect && excelSelect.value && systemSelect.value) {
        mappedCount++;
        mappedTargets.push(systemSelect.value);
      }
    });

    // 检查必填字段
    const requiredFields = tableConfig.fields.filter(function(f) { return f.required; });
    const missingRequired = requiredFields.filter(function(f) { return mappedTargets.indexOf(f.name) === -1; });

    if (missingRequired.length > 0) {
      container.style.color = 'var(--color-danger)';
      container.innerHTML = '已映射 ' + mappedCount + ' 个字段，<strong>缺少必填字段：' +
        missingRequired.map(function(f) { return f.display; }).join(', ') + '</strong>';
    } else {
      container.style.color = 'var(--color-success)';
      container.textContent = '已映射 ' + mappedCount + ' 个字段，所有必填字段已配置';
    }

  };

  W.getColumnMappings = function(tableName) {
    // 从 DOM 读取当前配置
    const activeTab = CustomImportWizard.elements.columnMappingTabs.querySelector('[data-table-name="' + tableName + '"]');
    if (!activeTab) {
      return CustomImportWizard.columnMappings[tableName] || { columns: [], conflict_mode: 'skip' };
    }

    const tbody = CustomImportWizard.elements.columnMappingContainer.querySelector('.column-mapping-tbody');
    if (!tbody) {
      return CustomImportWizard.columnMappings[tableName] || { columns: [], conflict_mode: 'skip' };
    }

    const columns = [];
    const rows = tbody.querySelectorAll('.column-mapping-row');

    rows.forEach(function(row) {
      const excelSelect = row.querySelector('.excel-column-select');
      const systemSelect = row.querySelector('.system-field-select');

      if (excelSelect && systemSelect && excelSelect.value && systemSelect.value) {
        columns.push({
          source: excelSelect.value,
          target: systemSelect.value
        });
      }
    });

    // 获取冲突模式
    const conflictRadio = CustomImportWizard.elements.columnMappingContainer.querySelector('input[name="conflict-mode-' + tableName + '"]:checked');
    const conflictMode = conflictRadio ? conflictRadio.value : 'skip';

    // 更新存储（使用 snake_case 以匹配后端 API）
    CustomImportWizard.columnMappings[tableName] = {
      columns: columns,
      conflict_mode: conflictMode
    };

    // 如果是车厢，包含特殊选项（使用 snake_case 以匹配后端 API）
    if (tableName === 'carriage') {
      CustomImportWizard.columnMappings[tableName].carriage_options = {
        set_detection_mode: document.querySelector('input[name="carriage-detection-mode"]:checked')?.value || 'merged',
        unmerged_field_value: document.querySelector('input[name="carriage-unmerged-value"]:checked')?.value || 'first'
      };
    }

    return CustomImportWizard.columnMappings[tableName];

  };

  W.saveAllColumnMappings = function() {
    const tabs = CustomImportWizard.elements.columnMappingTabs.querySelectorAll('.column-mapping-tab');
    tabs.forEach(function(tab) {
      const tableName = tab.dataset.tableName;
      W.getColumnMappings(tableName);
    });

  };

})(this);
