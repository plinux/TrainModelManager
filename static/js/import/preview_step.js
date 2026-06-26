/**
 * 火车模型管理系统 - 自定义导入向导 - 预览与执行步骤
 *
 * 步骤 5（确认/预览）：预览渲染、执行导入、禁用/启用导航、成功/错误结果页、保存模板（按需）。
 *
 * 依赖（按加载顺序）：wizard_core.js -> utils.js -> file_step.js -> mapping_step.js -> preview_step.js
 * 所有模块通过共享的 window.CustomImportWizard 对象（别名 W）通信。
 */

(function (global) {
  'use strict';

  /** 共享向导对象（由 wizard_core.js 初始化） */
  let W = global.CustomImportWizard;

  W.renderConfirmPage = function(previewData) {
    const tabsContainer = CustomImportWizard.elements.importSummaryTabs;
    const container = CustomImportWizard.elements.importSummary;
    if (!tabsContainer || !container) return;

    W.clearContainer(tabsContainer);
    W.clearContainer(container);

    if (!previewData || !previewData.previews || previewData.previews.length === 0) {
      const msg = document.createElement('p');
      msg.className = 'text-muted';
      msg.textContent = '无预览数据';
      container.appendChild(msg);
      return;
    }

    // 创建标签页
    previewData.previews.forEach(function(preview, index) {
      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = 'column-mapping-tab' + (index === 0 ? ' active' : '');
      tab.dataset.tableName = preview.table_name;
      tab.textContent = preview.display_name;

      tab.addEventListener('click', function() {
        // 移除所有标签页的 active 类
        tabsContainer.querySelectorAll('.column-mapping-tab').forEach(function(t) {
          t.classList.remove('active');
        });
        tab.classList.add('active');
        // 显示对应的预览内容
        W.renderConfirmPageContent(preview);
      });

      tabsContainer.appendChild(tab);
    });

    // 渲染第一个标签页的内容
    W.renderConfirmPageContent(previewData.previews[0]);

    // 总体状态
    if (!previewData.can_proceed) {
      const errorDiv = document.createElement('div');
      errorDiv.className = 'import-result error';
      errorDiv.style.marginTop = 'var(--spacing-md)';
      errorDiv.innerHTML = '<strong>无法导入：</strong>请返回上一步配置缺少的必填字段。';
      container.appendChild(errorDiv);
    } else {
      const successDiv = document.createElement('div');
      successDiv.className = 'import-result success';
      successDiv.style.marginTop = 'var(--spacing-md)';
      successDiv.textContent = '预览通过，可以开始导入。';
      container.appendChild(successDiv);
    }
  
  };

  W.renderConfirmPageContent = function(preview) {
    const container = CustomImportWizard.elements.importSummary;
    if (!container) return;

    // 清空容器但保留总体状态
    const statusDivs = container.querySelectorAll('.import-result');
    W.clearContainer(container);
    statusDivs.forEach(function(div) {
      container.appendChild(div);
    });

    // 创建预览信息卡片
    const card = document.createElement('div');
    card.className = 'preview-card';
    card.style.marginBottom = 'var(--spacing-md)';
    card.style.padding = 'var(--spacing-md)';
    card.style.background = '#f8f9fa';
    card.style.borderRadius = 'var(--border-radius)';

    // 基本信息
    const infoDiv = document.createElement('div');
    infoDiv.style.display = 'flex';
    infoDiv.style.gap = 'var(--spacing-lg)';
    infoDiv.style.flexWrap = 'wrap';
    infoDiv.style.marginBottom = 'var(--spacing-md)';

    // 数据行数
    const rowCount = document.createElement('div');
    rowCount.innerHTML = '<strong>数据行数：</strong>' + preview.row_count;
    infoDiv.appendChild(rowCount);

    // 冲突处理方式
    const mappingConfig = CustomImportWizard.columnMappings[preview.table_name];
    const conflictMode = mappingConfig ? mappingConfig.conflict_mode : 'skip';
    const conflictModeText = conflictMode === 'overwrite' ? '覆盖' : '跳过';
    const conflictModeDiv = document.createElement('div');
    conflictModeDiv.innerHTML = '<strong>冲突处理：</strong>' + conflictModeText;
    infoDiv.appendChild(conflictModeDiv);

    // 状态
    const statusDiv = document.createElement('div');
    if (preview.missing_required && preview.missing_required.length > 0) {
      statusDiv.innerHTML = '<strong>状态：</strong><span class="text-danger">缺少必填字段</span>';
    } else if (preview.conflicts && preview.conflicts.length > 0) {
      statusDiv.innerHTML = '<strong>状态：</strong><span class="text-warning">' + preview.conflicts.length + ' 个冲突</span>';
    } else {
      statusDiv.innerHTML = '<strong>状态：</strong><span class="text-success">可导入</span>';
    }
    infoDiv.appendChild(statusDiv);

    card.appendChild(infoDiv);

    // 如果有冲突，显示详情
    if (preview.conflicts && preview.conflicts.length > 0) {
      const conflictSection = document.createElement('div');
      conflictSection.style.marginTop = 'var(--spacing-sm)';

      const conflictTitle = document.createElement('strong');
      conflictTitle.textContent = '冲突详情：';
      conflictSection.appendChild(conflictTitle);

      const conflictList = document.createElement('ul');
      conflictList.style.margin = 'var(--spacing-xs) 0';
      conflictList.style.paddingLeft = 'var(--spacing-lg)';
      conflictList.style.fontSize = '0.85rem';
      conflictList.style.color = '#666';

      preview.conflicts.slice(0, 5).forEach(function(conflict) {
        const li = document.createElement('li');
        li.textContent = conflict.message;
        conflictList.appendChild(li);
      });

      if (preview.conflicts.length > 5) {
        const li = document.createElement('li');
        li.textContent = '... 还有 ' + (preview.conflicts.length - 5) + ' 个冲突';
        conflictList.appendChild(li);
      }

      conflictSection.appendChild(conflictList);
      card.appendChild(conflictSection);
    }

    // 如果有警告，显示详情
    if (preview.warnings && preview.warnings.length > 0) {
      const warningSection = document.createElement('div');
      warningSection.style.marginTop = 'var(--spacing-sm)';

      const warningTitle = document.createElement('strong');
      warningTitle.style.color = '#856404';
      warningTitle.textContent = '警告：';
      warningSection.appendChild(warningTitle);

      const warningList = document.createElement('ul');
      warningList.style.margin = 'var(--spacing-xs) 0';
      warningList.style.paddingLeft = 'var(--spacing-lg)';
      warningList.style.fontSize = '0.85rem';
      warningList.style.color = '#856404';

      preview.warnings.forEach(function(warning) {
        const li = document.createElement('li');
        li.textContent = warning;
        warningList.appendChild(li);
      });

      warningSection.appendChild(warningList);
      card.appendChild(warningSection);
    }

    // 插入到总体状态之前
    const firstStatus = container.querySelector('.import-result');
    if (firstStatus) {
      container.insertBefore(card, firstStatus);
    } else {
      container.appendChild(card);
    }
  
  };

  W.executeImport = function() {
    // 如果导入已完成，不重复执行
    if (CustomImportWizard.importCompleted) {
      return;
    }

    const previewResult = CustomImportWizard.previewResult;

    // 检查是否可以导入
    if (previewResult && !previewResult.can_proceed) {
      W.showMessage('存在配置问题，无法导入。请返回上一步检查。', true);
      return;
    }

    // 显示加载状态
    W.showLoading('正在导入数据，请稍候...');
    W.disableNavigationButtons();

    // 构建配置
    const config = {
      sheet_mappings: W.getSheetMappings(),
      column_mappings: CustomImportWizard.columnMappings
    };

    const formData = new FormData();
    formData.append('file', CustomImportWizard.selectedFile);
    formData.append('config', JSON.stringify(config));

    fetch(CustomImportWizard.api.executeImport, {
      method: 'POST',
      body: formData
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        W.hideLoading();
        W.enableNavigationButtons();

        if (data.success) {
          // 存储导入结果
          CustomImportWizard.importResult = data;

          // 显示成功结果
          W.renderImportSuccess(data);

          // 保存模板（如果选择了）
          W.saveTemplateIfNeeded(data);
        } else {
          // 显示失败结果
          W.renderImportError(data);
        }
      })
      .catch(function(error) {
        // 如果导入已完成，忽略错误（可能是页面重新加载导致的）
        if (CustomImportWizard.importCompleted) {
          return;
        }
        W.hideLoading();
        W.enableNavigationButtons();
        W.showMessage('导入时发生错误: ' + error.message, true);
        W.renderImportError({ error: error.message });
      });
  
  };

  W.disableNavigationButtons = function() {
    const els = CustomImportWizard.elements;
    if (els.btnPrev) els.btnPrev.disabled = true;
    if (els.btnNext) els.btnNext.disabled = true;
    if (els.btnFinish) els.btnFinish.disabled = true;
    if (els.btnCancel) els.btnCancel.disabled = true;
  
  };

  W.enableNavigationButtons = function() {
    const els = CustomImportWizard.elements;
    if (els.btnPrev) els.btnPrev.disabled = false;
    if (els.btnNext) els.btnNext.disabled = false;
    if (els.btnFinish) els.btnFinish.disabled = false;
    if (els.btnCancel) els.btnCancel.disabled = false;
  
  };

  W.renderImportSuccess = function(data) {
    const container = CustomImportWizard.elements.importSummary;
    if (!container) return;

    W.clearContainer(container);

    // 标记导入已完成
    CustomImportWizard.importCompleted = true;

    // 成功标题
    const heading = document.createElement('h4');
    heading.textContent = '导入完成';
    heading.style.marginTop = '0';
    heading.style.marginBottom = 'var(--spacing-md)';
    heading.style.color = 'var(--color-success)';
    container.appendChild(heading);

    // 成功消息
    const msgDiv = document.createElement('div');
    msgDiv.className = 'import-result success';
    msgDiv.style.marginBottom = 'var(--spacing-md)';
    msgDiv.innerHTML = '<strong>' + (data.message || '导入成功') + '</strong>';
    container.appendChild(msgDiv);

    // 导入摘要表格
    if (data.summary && Object.keys(data.summary).length > 0) {
      const table = document.createElement('table');
      table.className = 'column-mapping-table';

      // 表头
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      const thTable = document.createElement('th');
      thTable.textContent = '数据表';
      headerRow.appendChild(thTable);

      const thCount = document.createElement('th');
      thCount.textContent = '导入数量';
      headerRow.appendChild(thCount);

      thead.appendChild(headerRow);
      table.appendChild(thead);

      // 表体
      const tbody = document.createElement('tbody');

      Object.keys(data.summary).forEach(function(tableName) {
        const count = data.summary[tableName];
        if (count > 0) {
          const row = document.createElement('tr');

          const tdTable = document.createElement('td');
          tdTable.textContent = W.getTableDisplayName(tableName);
          row.appendChild(tdTable);

          const tdCount = document.createElement('td');
          tdCount.textContent = count + ' 条';
          tdCount.style.color = 'var(--color-success)';
          row.appendChild(tdCount);

          tbody.appendChild(row);
        }
      });

      table.appendChild(tbody);
      container.appendChild(table);
    }

    // 更新底部按钮为导入成功后的操作按钮
    const els = CustomImportWizard.elements;
    if (els.btnPrev) els.btnPrev.style.display = 'none';
    if (els.btnNext) els.btnNext.style.display = 'none';

    // 将"开始导入"按钮改为"完成"按钮
    if (els.btnFinish) {
      els.btnFinish.textContent = '完成';
      els.btnFinish.className = 'btn btn-primary';
      els.btnFinish.style.display = '';
      els.btnFinish.onclick = function(event) {
        // 阻止其他事件处理器（如 addEventListener 绑定的 executeImport）执行
        if (event) {
          event.stopImmediatePropagation();
        }
        W.closeModal();
        // 刷新页面以显示新数据
        window.location.reload();
      };
    }

    // 将"取消"按钮改为"重新导入"按钮
    if (els.btnCancel) {
      els.btnCancel.textContent = '重新导入';
      els.btnCancel.className = 'btn btn-secondary';
      els.btnCancel.onclick = function() {
        W.resetWizard();
      };
    }
  
  };

  W.renderImportError = function(data) {
    const container = CustomImportWizard.elements.importSummary;
    if (!container) return;

    W.clearContainer(container);

    // 错误标题
    const heading = document.createElement('h4');
    heading.textContent = '导入失败';
    heading.style.marginTop = '0';
    heading.style.marginBottom = 'var(--spacing-md)';
    heading.style.color = 'var(--color-danger)';
    container.appendChild(heading);

    // 错误消息
    const msgDiv = document.createElement('div');
    msgDiv.className = 'import-result error';
    msgDiv.style.marginBottom = 'var(--spacing-md)';
    msgDiv.innerHTML = '<strong>导入过程中发生错误：</strong><br>' + (data.error || '未知错误');
    container.appendChild(msgDiv);

    // 部分成功的摘要
    if (data.summary && Object.keys(data.summary).length > 0) {
      const hasPartialSuccess = Object.values(data.summary).some(function(count) {
        return count > 0;
      });

      if (hasPartialSuccess) {
        const partialDiv = document.createElement('div');
        partialDiv.className = 'import-result warning';
        partialDiv.style.marginBottom = 'var(--spacing-md)';

        let summaryHtml = '<strong>部分数据已成功导入：</strong><ul>';
        Object.keys(data.summary).forEach(function(tableName) {
          const count = data.summary[tableName];
          if (count > 0) {
            summaryHtml += '<li>' + W.getTableDisplayName(tableName) + ': ' + count + ' 条</li>';
          }
        });
        summaryHtml += '</ul>';
        partialDiv.innerHTML = summaryHtml;
        container.appendChild(partialDiv);
      }
    }

    // 更新底部按钮为导入失败后的操作按钮
    const els = CustomImportWizard.elements;
    if (els.btnPrev) els.btnPrev.style.display = 'none';
    if (els.btnNext) els.btnNext.style.display = 'none';
    if (els.btnFinish) els.btnFinish.style.display = 'none';

    // 将"取消"按钮改为"返回修改"按钮
    if (els.btnCancel) {
      els.btnCancel.textContent = '返回修改';
      els.btnCancel.className = 'btn btn-secondary';
      els.btnCancel.onclick = function() {
        // 重置按钮状态
        W.resetFooterButtons();
        // 返回步骤 4
        CustomImportWizard.currentStep = 4;
        W.updateStepIndicators();
        W.showCurrentStep();
        W.updateNavigationButtons();
      };
    }

    // 显示一个"关闭"按钮在右侧
    const footerRight = document.querySelector('.footer-right');
    if (footerRight && !document.getElementById('import-error-close-btn')) {
      const closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'btn btn-primary';
      closeBtn.id = 'import-error-close-btn';
      closeBtn.textContent = '关闭';
      closeBtn.onclick = function() {
        W.closeModal();
      };
      footerRight.appendChild(closeBtn);
    }
  
  };

  W.saveTemplateIfNeeded = function(importResult) {
    const mode = W.getSaveTemplateMode();

    if (mode === 'none') {
      return;
    }

    // 构建模板配置
    const templateConfig = {
      sheet_mappings: W.getSheetMappings(),
      column_mappings: CustomImportWizard.columnMappings
    };

    if (mode === 'new') {
      // 保存为新模板
      const name = CustomImportWizard.elements.newTemplateNameInput ?
        CustomImportWizard.elements.newTemplateNameInput.value.trim() : '';

      if (!name) {
        console.warn('Template name is empty, skipping save');
        return;
      }

      fetch('/api/import-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          config: templateConfig
        })
      })
        .then(function(response) {
          return response.json();
        })
        .then(function(data) {
          if (data.success) {
            W.showMessage('模板 "' + name + '" 保存成功');
            // 刷新模板列表
            W.checkTemplates();
          } else {
            console.error('Failed to save template:', data.error);
          }
        })
        .catch(function(error) {
          console.error('Error saving template:', error);
        });

    } else if (mode === 'update') {
      // 更新现有模板
      const templateId = CustomImportWizard.elements.updateTemplateSelect ?
        CustomImportWizard.elements.updateTemplateSelect.value : '';

      if (!templateId) {
        console.warn('No template selected for update, skipping');
        return;
      }

      fetch('/api/import-templates/' + templateId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config: templateConfig
        })
      })
        .then(function(response) {
          return response.json();
        })
        .then(function(data) {
          if (data.success) {
            W.showMessage('模板更新成功');
            // 刷新模板列表
            W.checkTemplates();
          } else {
            console.error('Failed to update template:', data.error);
          }
        })
        .catch(function(error) {
          console.error('Error updating template:', error);
        });
    }
  
  };

})(this);
