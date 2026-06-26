/**
 * 火车模型管理系统 - 自定义导入向导 - 核心模块
 *
 * 向导状态、DOM 缓存、事件绑定、模态框操作、步骤指示器、导航逻辑、步骤验证。定义 window.CustomImportWizard 全局对象（状态 + 公共 API）。
 *
 * 依赖（按加载顺序）：wizard_core.js -> utils.js -> file_step.js -> mapping_step.js -> preview_step.js
 * 所有模块通过共享的 window.CustomImportWizard 对象（别名 W）通信。
 */

(function (global) {
  'use strict';

  /** 共享向导对象（由 wizard_core.js 初始化） */
  let W = global.CustomImportWizard;

  // ==================== 模块状态 ====================
  // 定义全局向导对象（其他模块通过 W = window.CustomImportWizard 访问）
  global.CustomImportWizard = {
    // 当前步骤 (1-5)
    currentStep: 1,
    // 最大步骤
    maxStep: 5,
    // 是否跳过模板选择步骤
    skipTemplateStep: false,
    // 是否正在解析文件
    isParsing: false,
    // 文件是否已解析完成
    isParsed: false,
    // 导入是否已完成
    importCompleted: false,

    // 文件数据
    selectedFile: null,
    fileName: '',
    parsedSheets: [],

    // 模板数据
    templates: [],
    selectedTemplate: null,
    templateConfig: null,

    // 表格配置
    systemTables: [],

    // 映射配置
    sheetMappings: [],  // [{sheetName, tableName}, ...]
    columnMappings: {}, // {tableName: {columns: [...], conflict_mode: 'skip|overwrite'}}

    // DOM 元素引用
    elements: {},

    // API 端点
    api: {
      parseFile: '/api/custom-import/parse',
      getTables: '/api/custom-import/tables',
      getTemplates: '/api/import-templates',
      previewImport: '/api/custom-import/preview',
      executeImport: '/api/custom-import/execute'
    }
  };

  // 重新绑定 W 到刚创建的对象
  W = global.CustomImportWizard;

  W.init = function() {
    // 获取 DOM 元素引用
    W.cacheElements();

    // 绑定事件
    W.bindEvents();

    // 加载系统表格配置
    W.loadSystemTables();

    // 检查是否有模板
    W.checkTemplates();
  
  };

  W.cacheElements = function() {
    CustomImportWizard.elements = {
      // 模态框
      modal: document.getElementById('custom-import-modal'),
      btnClose: document.getElementById('btn-custom-import-close'),
      btnCancel: document.getElementById('btn-custom-import-cancel'),

      // 步骤指示器
      stepIndicators: document.querySelectorAll('.step-indicator'),

      // 步骤内容（新顺序：1=模板, 2=文件, 3=工作表, 4=列映射, 5=确认）
      stepContents: {
        1: document.getElementById('step-1-template'),
        2: document.getElementById('step-2-file'),
        3: document.getElementById('step-3-sheet'),
        4: document.getElementById('step-4-column'),
        5: document.getElementById('step-5-confirm')
      },

      // 步骤 1: 模板选择
      templateList: document.getElementById('template-list'),
      noTemplatesMsg: document.getElementById('no-templates-msg'),

      // 步骤 2: 文件选择
      fileInput: document.getElementById('custom-import-file'),
      fileUploadArea: document.querySelector('.file-upload-area'),
      filePreview: document.getElementById('file-preview'),
      selectedFilename: document.getElementById('selected-filename'),
      sheetCount: document.getElementById('sheet-count'),

      // 步骤 3: 工作表映射
      sheetMappingContainer: document.getElementById('sheet-mapping-container'),

      // 步骤 4: 列映射
      columnMappingTabs: document.getElementById('column-mapping-tabs'),
      columnMappingContainer: document.getElementById('column-mapping-container'),

      // 步骤 5: 确认导入
      importSummaryTabs: document.getElementById('import-summary-tabs'),
      importSummary: document.getElementById('import-summary'),
      saveTemplateModeRadios: document.querySelectorAll('input[name="save-template-mode"]'),
      newTemplateModeRadio: document.querySelector('input[name="save-template-mode"][value="new"]'),
      updateTemplateModeRadio: document.querySelector('input[name="save-template-mode"][value="update"]'),
      newTemplateNameContainer: document.getElementById('new-template-name-container'),
      newTemplateNameInput: document.getElementById('new-template-name'),
      updateTemplateSelectContainer: document.getElementById('update-template-select-container'),
      updateTemplateSelect: document.getElementById('update-template-select'),

      // 导航按钮
      btnPrev: document.getElementById('btn-custom-import-prev'),
      btnNext: document.getElementById('btn-custom-import-next'),
      btnFinish: document.getElementById('btn-custom-import-finish'),

      // 触发按钮
      btnOpen: document.getElementById('btn-custom-import')
    };
  
  };

  W.bindEvents = function() {
    const els = CustomImportWizard.elements;

    // 打开模态框
    if (els.btnOpen) {
      els.btnOpen.addEventListener('click', W.openModal);
    }

    // 关闭模态框
    if (els.btnClose) {
      els.btnClose.addEventListener('click', W.closeModal);
    }
    if (els.btnCancel) {
      els.btnCancel.addEventListener('click', W.closeModal);
    }

    // 点击遮罩层关闭
    if (els.modal) {
      els.modal.addEventListener('click', function(e) {
        if (e.target === els.modal) {
          W.closeModal();
        }
      });
    }

    // 文件选择
    if (els.fileInput) {
      els.fileInput.addEventListener('change', W.handleFileSelect);
    }

    // 拖拽上传
    if (els.fileUploadArea) {
      els.fileUploadArea.addEventListener('dragover', W.handleDragOver);
      els.fileUploadArea.addEventListener('dragleave', W.handleDragLeave);
      els.fileUploadArea.addEventListener('drop', W.handleDrop);
    }

    // 跳过模板复选框
    if (els.skipTemplateCheckbox) {
      els.skipTemplateCheckbox.addEventListener('change', W.handleSkipTemplateChange);
    }

    // 保存模板模式单选框
    els.saveTemplateModeRadios.forEach(function(radio) {
      radio.addEventListener('change', W.handleSaveTemplateModeChange);
    });

    // 导航按钮
    if (els.btnPrev) {
      els.btnPrev.addEventListener('click', W.goToPrevStep);
    }
    if (els.btnNext) {
      els.btnNext.addEventListener('click', W.goToNextStep);
    }
    if (els.btnFinish) {
      els.btnFinish.addEventListener('click', W.executeImport);
    }
  
  };

  W.openModal = function() {
    const els = CustomImportWizard.elements;
    if (els.modal) {
      els.modal.style.display = 'flex';
      W.resetWizard();
    }
  
  };

  W.closeModal = function() {
    const els = CustomImportWizard.elements;
    if (els.modal) {
      els.modal.style.display = 'none';
    }
  
  };

  W.resetFooterButtons = function() {
    const els = CustomImportWizard.elements;

    // 恢复取消按钮
    if (els.btnCancel) {
      els.btnCancel.textContent = '取消';
      els.btnCancel.className = 'btn btn-secondary';
      els.btnCancel.onclick = function() {
        W.closeModal();
      };
    }

    // 恢复上一步按钮
    if (els.btnPrev) {
      els.btnPrev.textContent = '上一步';
      els.btnPrev.className = 'btn btn-secondary';
      els.btnPrev.style.display = '';
    }

    // 恢复下一步按钮
    if (els.btnNext) {
      els.btnNext.textContent = '下一步';
      els.btnNext.className = 'btn btn-primary';
      els.btnNext.style.display = '';
    }

    // 恢复开始导入按钮
    if (els.btnFinish) {
      els.btnFinish.textContent = '开始导入';
      els.btnFinish.className = 'btn btn-success';
      els.btnFinish.style.display = '';
    }

    // 移除动态添加的关闭按钮
    const closeBtn = document.getElementById('import-error-close-btn');
    if (closeBtn) {
      closeBtn.remove();
    }
  
  };

  W.resetWizard = function() {
    CustomImportWizard.currentStep = 1;
    CustomImportWizard.selectedFile = null;
    CustomImportWizard.fileName = '';
    CustomImportWizard.parsedSheets = [];
    CustomImportWizard.isParsing = false;
    CustomImportWizard.isParsed = false;
    CustomImportWizard.importCompleted = false;
    CustomImportWizard.selectedTemplate = null;
    CustomImportWizard.templateConfig = null;
    CustomImportWizard.sheetMappings = [];
    CustomImportWizard.columnMappings = {};

    const els = CustomImportWizard.elements;

    // 重置文件输入
    if (els.fileInput) {
      els.fileInput.value = '';
    }

    // 隐藏文件预览
    if (els.filePreview) {
      els.filePreview.style.display = 'none';
    }

    // 清空工作表映射容器
    if (els.sheetMappingContainer) {
      W.clearContainer(els.sheetMappingContainer);
    }

    // 清空列映射容器
    if (els.columnMappingTabs) {
      W.clearContainer(els.columnMappingTabs);
    }
    if (els.columnMappingContainer) {
      W.clearContainer(els.columnMappingContainer);
    }

    // 重置确认页面
    if (els.importSummary) {
      W.clearContainer(els.importSummary);
    }
    // 重置保存模板选项
    els.saveTemplateModeRadios.forEach(function(radio) {
      radio.checked = (radio.value === 'none');
    });
    if (els.newTemplateNameContainer) {
      els.newTemplateNameContainer.style.display = 'none';
    }
    if (els.newTemplateNameInput) {
      els.newTemplateNameInput.value = '';
    }
    if (els.updateTemplateSelectContainer) {
      els.updateTemplateSelectContainer.style.display = 'none';
    }
    if (els.updateTemplateSelect) {
      els.updateTemplateSelect.value = '';
    }
    // 清空导入结果
    CustomImportWizard.importResult = null;

    // 重置底部按钮
    W.resetFooterButtons();

    // 更新 UI
    W.updateStepIndicators();
    W.showCurrentStep();
    W.updateNavigationButtons();

    // 重新检查模板
    W.checkTemplates();
  
  };

  W.updateStepIndicators = function() {
    const indicators = CustomImportWizard.elements.stepIndicators;
    const currentStep = CustomImportWizard.currentStep;

    indicators.forEach(function(indicator) {
      const step = parseInt(indicator.dataset.step, 10);
      indicator.classList.remove('active', 'completed');

      if (step < currentStep) {
        indicator.classList.add('completed');
      } else if (step === currentStep) {
        indicator.classList.add('active');
      }
    });
  
  };

  W.showCurrentStep = function() {
    const contents = CustomImportWizard.elements.stepContents;
    const currentStep = CustomImportWizard.currentStep;

    Object.keys(contents).forEach(function(step) {
      const stepNum = parseInt(step, 10);
      if (contents[stepNum]) {
        contents[stepNum].style.display = (stepNum === currentStep) ? 'block' : 'none';
      }
    });
  
  };

  W.updateNavigationButtons = function() {
    const els = CustomImportWizard.elements;
    const currentStep = CustomImportWizard.currentStep;
    const maxStep = CustomImportWizard.maxStep;

    // 上一步按钮
    if (els.btnPrev) {
      // 如果跳过模板步骤且在步骤2，不显示上一步按钮
      if (currentStep === 2 && CustomImportWizard.skipTemplateStep) {
        els.btnPrev.style.display = 'none';
      } else {
        els.btnPrev.style.display = (currentStep > 1) ? 'inline-block' : 'none';
      }
    }

    // 下一步按钮
    if (els.btnNext) {
      els.btnNext.style.display = (currentStep < maxStep) ? 'inline-block' : 'none';

      // 新流程：步骤1是模板选择（始终启用），步骤2是文件选择（需要文件）
      if (currentStep === 1) {
        // 步骤1：模板选择，始终可进入下一步
        els.btnNext.disabled = false;
        els.btnNext.textContent = '下一步';
      } else if (currentStep === 2) {
        // 步骤2：文件选择，需要解析文件后才能继续
        els.btnNext.disabled = CustomImportWizard.isParsing || !CustomImportWizard.isParsed;
        if (els.btnNext.disabled) {
          els.btnNext.textContent = CustomImportWizard.isParsing ? '解析中...' : '请选择文件';
        } else {
          els.btnNext.textContent = '下一步';
        }
      } else {
        // 其他步骤
        els.btnNext.disabled = false;
        els.btnNext.textContent = '下一步';
      }
    }

    // 完成按钮
    if (els.btnFinish) {
      els.btnFinish.style.display = (currentStep === maxStep) ? 'inline-block' : 'none';
    }
  
  };

  W.goToNextStep = function() {
    const currentStep = CustomImportWizard.currentStep;

    // 验证当前步骤
    if (!W.validateCurrentStep()) {
      return;
    }

    // 新流程：步骤1是模板选择，如果无模板则跳过
    // 如果当前在步骤1且无模板，直接跳到步骤2
    if (currentStep === 1 && CustomImportWizard.skipTemplateStep) {
      CustomImportWizard.currentStep = 2;
    } else {
      CustomImportWizard.currentStep = Math.min(currentStep + 1, CustomImportWizard.maxStep);
    }

    // 如果到步骤 3，渲染工作表映射
    if (CustomImportWizard.currentStep === 3) {
      W.renderSheetMapping();
    }

    // 如果到步骤 4，渲染列映射
    if (CustomImportWizard.currentStep === 4) {
      W.renderColumnMapping();
    }

    // 如果到步骤 5，先调用预览 API
    if (CustomImportWizard.currentStep === 5) {
      W.callPreviewApiAndRenderConfirm();
      return; // 异步处理，在回调中继续
    }

    W.updateStepIndicators();
    W.showCurrentStep();
    W.updateNavigationButtons();
  
  };

  W.goToPrevStep = function() {
    const currentStep = CustomImportWizard.currentStep;

    // 新流程：步骤1是模板，步骤2是文件
    // 如果当前在步骤2且无模板，回到步骤1（会自动跳过）
    if (currentStep === 2 && CustomImportWizard.skipTemplateStep) {
      CustomImportWizard.currentStep = 1;
    } else if (currentStep === 3 && CustomImportWizard.skipTemplateStep) {
      // 如果在步骤3（工作表映射）且无模板，回到步骤2（文件选择）
      CustomImportWizard.currentStep = 2;
    } else {
      CustomImportWizard.currentStep = Math.max(currentStep - 1, 1);
    }

    W.updateStepIndicators();
    W.showCurrentStep();
    W.updateNavigationButtons();
  
  };

  W.validateCurrentStep = function() {
    const currentStep = CustomImportWizard.currentStep;

    switch (currentStep) {
      case 1:
        return W.validateStep1(); // 模板选择验证
      case 2:
        return W.validateStep2(); // 文件选择验证
      case 3:
        return W.validateStep3(); // 工作表映射验证
      case 4:
        return W.validateStep4(); // 列映射验证
      default:
        return true;
    }
  
  };

  W.validateStep1 = function() {
    // 模板选择是可选的，始终返回 true
    // 如果选择了模板，应用模板配置
    if (CustomImportWizard.selectedTemplate && CustomImportWizard.templateConfig) {
      W.applyTemplateConfig(CustomImportWizard.templateConfig);
    }
    return true;
  
  };

  W.validateStep2 = function() {
    if (!CustomImportWizard.selectedFile) {
      W.showMessage('请选择要导入的 Excel 文件', true);
      return false;
    }
    if (CustomImportWizard.isParsing) {
      W.showMessage('文件正在解析中，请稍候...', true);
      return false;
    }
    if (!CustomImportWizard.isParsed) {
      W.showMessage('文件尚未解析完成，请稍候...', true);
      return false;
    }
    return true;
  
  };

  W.validateStep3 = function() {
    const mappings = W.getSheetMappings();

    // 检查是否所有 sheet 都已映射或跳过
    const mappedCount = mappings.filter(function(m) {
      return m.table_name !== '';
    }).length;

    // 至少映射一个 sheet
    if (mappedCount === 0) {
      W.showMessage('请至少映射一个工作表', true);
      return false;
    }

    return true;
  
  };

  W.validateStep4 = function() {
    // 保存所有列映射配置
    W.saveAllColumnMappings();

    // 检查每个表的必填字段
    const sheetMappings = W.getSheetMappings();
    let allValid = true;
    const missingFields = [];

    sheetMappings.forEach(function(mapping) {
      if (!mapping.table_name) return;

      const tableConfig = W.getSystemTableConfig(mapping.table_name);
      if (!tableConfig) return;

      const columnMapping = CustomImportWizard.columnMappings[mapping.table_name];
      if (!columnMapping || !columnMapping.columns || columnMapping.columns.length === 0) {
        missingFields.push(W.getTableDisplayName(mapping.table_name) + ': 未配置任何列映射');
        allValid = false;
        return;
      }

      // 检查必填字段
      const mappedTargets = columnMapping.columns.map(function(c) { return c.target; });
      const requiredFields = tableConfig.fields.filter(function(f) { return f.required; });

      requiredFields.forEach(function(field) {
        if (mappedTargets.indexOf(field.name) === -1) {
          missingFields.push(W.getTableDisplayName(mapping.table_name) + ': 缺少必填字段 "' + field.display + '"');
          allValid = false;
        }
      });
    });

    if (!allValid) {
      W.showMessage('列映射配置不完整：\n' + missingFields.join('\n'), true);
      return false;
    }

    return true;
  
  };

  W.callPreviewApiAndRenderConfirm = function() {
    W.showLoading('正在预览导入数据...');

    // 保存所有列映射配置
    W.saveAllColumnMappings();

    // 构建配置
    const config = {
      sheet_mappings: W.getSheetMappings(),
      column_mappings: CustomImportWizard.columnMappings
    };

    const formData = new FormData();
    formData.append('file', CustomImportWizard.selectedFile);
    formData.append('config', JSON.stringify(config));

    fetch(CustomImportWizard.api.previewImport, {
      method: 'POST',
      body: formData
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        W.hideLoading();

        if (data.success) {
          // 存储预览结果
          CustomImportWizard.previewResult = data;
          W.renderConfirmPage(data);
          W.updateStepIndicators();
          W.showCurrentStep();
          W.updateNavigationButtons();
        } else {
          W.showMessage(data.error || '预览失败', true);
          // 回到步骤 4
          CustomImportWizard.currentStep = 4;
          W.updateStepIndicators();
          W.showCurrentStep();
          W.updateNavigationButtons();
        }
      })
      .catch(function(error) {
        W.hideLoading();
        W.showMessage('预览时发生错误: ' + error.message, true);
        // 回到步骤 4
        CustomImportWizard.currentStep = 4;
        W.updateStepIndicators();
        W.showCurrentStep();
        W.updateNavigationButtons();
      });
  
  };

  // ==================== 初始化与公共 API ====================

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', W.init);
  } else {
    W.init();
  }

  // 公共 API（保持向后兼容：window.CustomImportWizard.open/close/reset）
  W.open = W.openModal;
  W.close = W.closeModal;
  W.reset = W.resetWizard;
})(this);
