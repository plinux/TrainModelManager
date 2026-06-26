/**
 * 火车模型管理系统 - 自定义导入向导 - 文件与模板步骤
 *
 * 步骤 1（文件选择/解析）和步骤 2（模板管理）：拖拽上传、Excel 解析、模板列表渲染、选择/复制/重命名/删除模板。
 *
 * 依赖（按加载顺序）：wizard_core.js -> utils.js -> file_step.js -> mapping_step.js -> preview_step.js
 * 所有模块通过共享的 window.CustomImportWizard 对象（别名 W）通信。
 */

(function (global) {
  'use strict';

  /** 共享向导对象（由 wizard_core.js 初始化） */
  let W = global.CustomImportWizard;

  W.handleDragOver = function(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('drag-over');
  
  };

  W.handleDragLeave = function(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');
  
  };

  W.handleDrop = function(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      W.processFile(files[0]);
    }
  
  };

  W.handleFileSelect = function(e) {
    const file = e.target.files[0];
    if (file) {
      W.processFile(file);
    }
  
  };

  W.processFile = function(file) {
    // 验证文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      W.showMessage('请选择 .xlsx 或 .xls 格式的 Excel 文件', true);
      return;
    }

    CustomImportWizard.selectedFile = file;
    CustomImportWizard.fileName = file.name;

    // 显示加载状态
    W.showLoading('正在解析文件...');

    // 调用 API 解析文件
    W.parseExcelFile(file);
  
  };

  W.parseExcelFile = function(file) {
    // 设置解析状态
    CustomImportWizard.isParsing = true;
    CustomImportWizard.isParsed = false;
    W.updateNavigationButtons();

    const formData = new FormData();
    formData.append('file', file);

    fetch(CustomImportWizard.api.parseFile, {
      method: 'POST',
      body: formData
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        W.hideLoading();
        CustomImportWizard.isParsing = false;

        if (data.success) {
          // 确保sheets是数组
          CustomImportWizard.parsedSheets = Array.isArray(data.sheets) ? data.sheets : [];
          CustomImportWizard.isParsed = true;

          // 更新 UI
          const els = CustomImportWizard.elements;
          if (els.selectedFilename) {
            els.selectedFilename.textContent = data.filename;
          }
          if (els.sheetCount) {
            els.sheetCount.textContent = data.sheets.length;
          }
          if (els.filePreview) {
            els.filePreview.style.display = 'block';
          }

          W.showMessage('文件解析成功，共 ' + data.sheets.length + ' 个工作表');
        } else {
          CustomImportWizard.isParsed = false;
          W.showMessage(data.error || '文件解析失败', true);
          W.resetFileSelection();
        }
        W.updateNavigationButtons();
      })
      .catch(function(error) {
        W.hideLoading();
        CustomImportWizard.isParsing = false;
        CustomImportWizard.isParsed = false;
        W.showMessage('解析文件时发生错误: ' + error.message, true);
        W.resetFileSelection();
        W.updateNavigationButtons();
      });
  
  };

  W.resetFileSelection = function() {
    CustomImportWizard.selectedFile = null;
    CustomImportWizard.fileName = '';
    CustomImportWizard.parsedSheets = [];
    CustomImportWizard.isParsing = false;
    CustomImportWizard.isParsed = false;

    const els = CustomImportWizard.elements;
    if (els.fileInput) {
      els.fileInput.value = '';
    }
    if (els.filePreview) {
      els.filePreview.style.display = 'none';
    }
  
  };

  W.checkTemplates = function() {
    fetch(CustomImportWizard.api.getTemplates)
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          CustomImportWizard.templates = data.templates || [];

          if (CustomImportWizard.templates.length > 0) {
            CustomImportWizard.skipTemplateStep = false;
            W.renderTemplateList();
          } else {
            CustomImportWizard.skipTemplateStep = true;
            W.updateSkipTemplateUI();
          }
        }
      })
      .catch(function(error) {
        console.error('Failed to load templates:', error);
        CustomImportWizard.skipTemplateStep = true;
        W.updateSkipTemplateUI();
      });
  
  };

  W.renderTemplateList = function() {
    const container = CustomImportWizard.elements.templateList;
    if (!container) return;

    // 清空容器
    W.clearContainer(container);

    const templates = CustomImportWizard.templates;

    if (templates.length === 0) {
      // 显示无模板消息
      const noMsg = document.createElement('p');
      noMsg.className = 'no-templates';
      noMsg.textContent = '暂无保存的模板，请手动配置映射。';
      container.appendChild(noMsg);
      return;
    }

    // 创建表格
    const table = document.createElement('table');
    table.className = 'template-table';

    // 创建表头
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['', '模板名称', '修改时间', '操作'].forEach(function(text, index) {
      const th = document.createElement('th');
      th.textContent = text;
      if (index === 0) {
        th.className = 'col-select';
      } else if (index === 1) {
        th.className = 'col-name';
      } else if (index === 2) {
        th.className = 'col-time';
      } else {
        th.className = 'col-actions';
      }
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // 创建表体
    const tbody = document.createElement('tbody');

    // 添加 "不使用模板" 选项
    const noTemplateRow = W.createTemplateTableRow(null, '不使用模板', true);
    tbody.appendChild(noTemplateRow);

    // 添加模板列表
    templates.forEach(function(template) {
      const row = W.createTemplateTableRow(template, template.name, false);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
  
  };

  W.createTemplateTableRow = function(template, displayName, isSelected) {
    const row = document.createElement('tr');
    row.className = 'template-row' + (isSelected ? ' selected' : '');
    row.dataset.templateId = template ? template.id : '';

    // 第一列：单选框
    const selectCell = document.createElement('td');
    selectCell.className = 'col-select';
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'template-choice';
    radio.value = template ? template.id : '';
    radio.checked = isSelected;
    selectCell.appendChild(radio);
    row.appendChild(selectCell);

    // 第二列：模板名称
    const nameCell = document.createElement('td');
    nameCell.className = 'col-name';
    nameCell.textContent = displayName;
    row.appendChild(nameCell);

    // 第三列：修改时间
    const timeCell = document.createElement('td');
    timeCell.className = 'col-time';
    if (template && template.updated_at) {
      timeCell.textContent = W.formatDate(template.updated_at);
    } else {
      timeCell.textContent = '-';
    }
    row.appendChild(timeCell);

    // 第四列：操作按钮
    const actionsCell = document.createElement('td');
    actionsCell.className = 'col-actions';
    if (template) {
      // 复制按钮
      const copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'btn btn-sm btn-secondary';
      copyBtn.textContent = '复制';
      copyBtn.onclick = function(e) {
        e.stopPropagation();
        W.copyTemplate(template);
      };

      // 重命名按钮
      const renameBtn = document.createElement('button');
      renameBtn.type = 'button';
      renameBtn.className = 'btn btn-sm btn-secondary';
      renameBtn.textContent = '重命名';
      renameBtn.onclick = function(e) {
        e.stopPropagation();
        W.renameTemplate(template);
      };

      // 删除按钮
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'btn btn-sm btn-danger';
      deleteBtn.textContent = '删除';
      deleteBtn.onclick = function(e) {
        e.stopPropagation();
        W.deleteTemplate(template);
      };

      actionsCell.appendChild(copyBtn);
      actionsCell.appendChild(renameBtn);
      actionsCell.appendChild(deleteBtn);
    } else {
      actionsCell.textContent = '-';
    }
    row.appendChild(actionsCell);

    // 点击行选择模板
    row.addEventListener('click', function() {
      W.selectTemplate(template);
    });

    return row;
  
  };

  W.copyTemplate = function(template) {
    // 生成新名称：原模板名_副本_时间戳
    const now = new Date();
    const timestamp = now.getFullYear().toString() +
      String(now.getMonth() + 1).padStart(2, '0') +
      String(now.getDate()).padStart(2, '0') + '_' +
      String(now.getHours()).padStart(2, '0') +
      String(now.getMinutes()).padStart(2, '0') +
      String(now.getSeconds()).padStart(2, '0');
    const newName = template.name + '_副本_' + timestamp;

    // 调用复制 API
    fetch('/api/import-templates/' + template.id + '/copy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: newName })
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          // 添加到本地列表
          CustomImportWizard.templates.push(data.template);
          W.renderTemplateList();
          W.showMessage('模板复制成功');
        } else {
          W.showMessage(data.error || '复制失败', true);
        }
      })
      .catch(function(error) {
        W.showMessage('复制失败: ' + error.message, true);
      });
  
  };

  W.selectTemplate = function(template) {
    // 更新选中状态
    const items = CustomImportWizard.elements.templateList.querySelectorAll('.template-item');
    items.forEach(function(item) {
      item.classList.remove('selected');
      const radio = item.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = false;
      }
    });

    // 选中当前项
    const currentItem = template
      ? CustomImportWizard.elements.templateList.querySelector('[data-template-id="' + template.id + '"]')
      : CustomImportWizard.elements.templateList.querySelector('[data-template-id=""]');
    if (currentItem) {
      currentItem.classList.add('selected');
      const radio = currentItem.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
      }
    }

    CustomImportWizard.selectedTemplate = template;
    CustomImportWizard.templateConfig = template ? template.config : null;

    // 如果选择了模板，立即应用配置
    if (template && template.config) {
      W.applyTemplateConfig(template.config);
    }
  
  };

  W.applyTemplateConfig = function(config) {
    if (!config) return;

    // 应用列映射配置
    if (config.column_mappings) {
      CustomImportWizard.columnMappings = config.column_mappings;
    }

    // 工作表映射会在解析文件后应用
    if (config.sheet_mappings) {
      CustomImportWizard.sheetMappings = config.sheet_mappings;
    }
  
  };

  W.renameTemplate = function(template) {
    const newName = prompt('请输入新的模板名称:', template.name);
    if (newName && newName.trim() && newName !== template.name) {
      fetch('/api/import-templates/' + template.id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim() })
      })
        .then(function(response) {
          return response.json();
        })
        .then(function(data) {
          if (data.success) {
            template.name = newName.trim();
            W.renderTemplateList();
            W.showMessage('模板重命名成功');
          } else {
            W.showMessage(data.error || '重命名失败', true);
          }
        })
        .catch(function(error) {
          W.showMessage('重命名失败: ' + error.message, true);
        });
    }
  
  };

  W.deleteTemplate = function(template) {
    if (!confirm('确定要删除模板 "' + template.name + '" 吗?')) {
      return;
    }

    fetch('/api/import-templates/' + template.id, {
      method: 'DELETE'
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          // 从列表中移除
          CustomImportWizard.templates = CustomImportWizard.templates.filter(function(t) {
            return t.id !== template.id;
          });

          // 如果删除的是当前选中的模板，清除选择
          if (CustomImportWizard.selectedTemplate &&
              CustomImportWizard.selectedTemplate.id === template.id) {
            CustomImportWizard.selectedTemplate = null;
            CustomImportWizard.templateConfig = null;
          }

          W.renderTemplateList();
          W.showMessage('模板删除成功');

          // 检查是否需要跳过模板步骤
          if (CustomImportWizard.templates.length === 0) {
            CustomImportWizard.skipTemplateStep = true;
            W.updateSkipTemplateUI();
          }
        } else {
          W.showMessage(data.error || '删除失败', true);
        }
      })
      .catch(function(error) {
        W.showMessage('删除失败: ' + error.message, true);
      });
  
  };

  W.handleSkipTemplateChange = function() {
    const checkbox = CustomImportWizard.elements.skipTemplateCheckbox;
    CustomImportWizard.skipTemplateStep = checkbox ? checkbox.checked : true;
  
  };

  W.updateSkipTemplateUI = function() {
    const checkbox = CustomImportWizard.elements.skipTemplateCheckbox;
    if (checkbox) {
      checkbox.checked = CustomImportWizard.skipTemplateStep;
    }
  
  };

})(this);
