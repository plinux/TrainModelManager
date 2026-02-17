/**
 * 自定义导入向导 JavaScript 模块
 * 处理自定义导入流程的步骤 1-5
 *
 * 步骤说明:
 * 1. 选择文件 - 支持拖拽或点击上传 Excel 文件
 * 2. 选择模板 - 选择已保存的导入模板（如有）
 * 3. 工作表映射 - 将 Excel 工作表映射到系统数据类型
 * 4. 列映射 - 为每个数据类型配置列映射关系
 * 5. 确认导入 - 预览并执行导入
 */
(function() {
  'use strict';

  // ==================== 模块状态 ====================
  const CustomImportWizard = {
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

  // ==================== 初始化 ====================

  /**
   * 初始化自定义导入向导
   */
  function init() {
    // 获取 DOM 元素引用
    cacheElements();

    // 绑定事件
    bindEvents();

    // 加载系统表格配置
    loadSystemTables();

    // 检查是否有模板
    checkTemplates();
  }

  /**
   * 缓存 DOM 元素引用
   */
  function cacheElements() {
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
  }

  /**
   * 绑定事件监听器
   */
  function bindEvents() {
    const els = CustomImportWizard.elements;

    // 打开模态框
    if (els.btnOpen) {
      els.btnOpen.addEventListener('click', openModal);
    }

    // 关闭模态框
    if (els.btnClose) {
      els.btnClose.addEventListener('click', closeModal);
    }
    if (els.btnCancel) {
      els.btnCancel.addEventListener('click', closeModal);
    }

    // 点击遮罩层关闭
    if (els.modal) {
      els.modal.addEventListener('click', function(e) {
        if (e.target === els.modal) {
          closeModal();
        }
      });
    }

    // 文件选择
    if (els.fileInput) {
      els.fileInput.addEventListener('change', handleFileSelect);
    }

    // 拖拽上传
    if (els.fileUploadArea) {
      els.fileUploadArea.addEventListener('dragover', handleDragOver);
      els.fileUploadArea.addEventListener('dragleave', handleDragLeave);
      els.fileUploadArea.addEventListener('drop', handleDrop);
    }

    // 跳过模板复选框
    if (els.skipTemplateCheckbox) {
      els.skipTemplateCheckbox.addEventListener('change', handleSkipTemplateChange);
    }

    // 保存模板模式单选框
    els.saveTemplateModeRadios.forEach(function(radio) {
      radio.addEventListener('change', handleSaveTemplateModeChange);
    });

    // 导航按钮
    if (els.btnPrev) {
      els.btnPrev.addEventListener('click', goToPrevStep);
    }
    if (els.btnNext) {
      els.btnNext.addEventListener('click', goToNextStep);
    }
    if (els.btnFinish) {
      els.btnFinish.addEventListener('click', executeImport);
    }
  }

  // ==================== 模态框操作 ====================

  /**
   * 打开模态框
   */
  function openModal() {
    const els = CustomImportWizard.elements;
    if (els.modal) {
      els.modal.style.display = 'flex';
      resetWizard();
    }
  }

  /**
   * 关闭模态框
   */
  function closeModal() {
    const els = CustomImportWizard.elements;
    if (els.modal) {
      els.modal.style.display = 'none';
    }
  }

  /**
   * 重置底部按钮到初始状态
   */
  function resetFooterButtons() {
    const els = CustomImportWizard.elements;

    // 恢复取消按钮
    if (els.btnCancel) {
      els.btnCancel.textContent = '取消';
      els.btnCancel.className = 'btn btn-secondary';
      els.btnCancel.onclick = function() {
        closeModal();
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
  }

  /**
   * 清空容器的安全方法
   * @param {HTMLElement} container
   */
  function clearContainer(container) {
    while (container && container.firstChild) {
      container.removeChild(container.firstChild);
    }
  }

  /**
   * 重置向导状态
   */
  function resetWizard() {
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
      clearContainer(els.sheetMappingContainer);
    }

    // 清空列映射容器
    if (els.columnMappingTabs) {
      clearContainer(els.columnMappingTabs);
    }
    if (els.columnMappingContainer) {
      clearContainer(els.columnMappingContainer);
    }

    // 重置确认页面
    if (els.importSummary) {
      clearContainer(els.importSummary);
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
    resetFooterButtons();

    // 更新 UI
    updateStepIndicators();
    showCurrentStep();
    updateNavigationButtons();

    // 重新检查模板
    checkTemplates();
  }

  // ==================== 步骤指示器 ====================

  /**
   * 更新步骤指示器状态
   */
  function updateStepIndicators() {
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
  }

  /**
   * 显示当前步骤内容
   */
  function showCurrentStep() {
    const contents = CustomImportWizard.elements.stepContents;
    const currentStep = CustomImportWizard.currentStep;

    Object.keys(contents).forEach(function(step) {
      const stepNum = parseInt(step, 10);
      if (contents[stepNum]) {
        contents[stepNum].style.display = (stepNum === currentStep) ? 'block' : 'none';
      }
    });
  }

  /**
   * 更新导航按钮状态
   */
  function updateNavigationButtons() {
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
  }

  // ==================== 导航 ====================

  /**
   * 前往下一步
   */
  function goToNextStep() {
    const currentStep = CustomImportWizard.currentStep;

    // 验证当前步骤
    if (!validateCurrentStep()) {
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
      renderSheetMapping();
    }

    // 如果到步骤 4，渲染列映射
    if (CustomImportWizard.currentStep === 4) {
      renderColumnMapping();
    }

    // 如果到步骤 5，先调用预览 API
    if (CustomImportWizard.currentStep === 5) {
      callPreviewApiAndRenderConfirm();
      return; // 异步处理，在回调中继续
    }

    updateStepIndicators();
    showCurrentStep();
    updateNavigationButtons();
  }

  /**
   * 调用预览 API 并渲染确认页面
   */
  function callPreviewApiAndRenderConfirm() {
    showLoading('正在预览导入数据...');

    // 保存所有列映射配置
    saveAllColumnMappings();

    // 构建配置
    const config = {
      sheet_mappings: getSheetMappings(),
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
        hideLoading();

        if (data.success) {
          // 存储预览结果
          CustomImportWizard.previewResult = data;
          renderConfirmPage(data);
          updateStepIndicators();
          showCurrentStep();
          updateNavigationButtons();
        } else {
          showMessage(data.error || '预览失败', true);
          // 回到步骤 4
          CustomImportWizard.currentStep = 4;
          updateStepIndicators();
          showCurrentStep();
          updateNavigationButtons();
        }
      })
      .catch(function(error) {
        hideLoading();
        showMessage('预览时发生错误: ' + error.message, true);
        // 回到步骤 4
        CustomImportWizard.currentStep = 4;
        updateStepIndicators();
        showCurrentStep();
        updateNavigationButtons();
      });
  }

  /**
   * 前往上一步
   */
  function goToPrevStep() {
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

    updateStepIndicators();
    showCurrentStep();
    updateNavigationButtons();
  }

  /**
   * 验证当前步骤
   * @returns {boolean}
   */
  function validateCurrentStep() {
    const currentStep = CustomImportWizard.currentStep;

    switch (currentStep) {
      case 1:
        return validateStep1(); // 模板选择验证
      case 2:
        return validateStep2(); // 文件选择验证
      case 3:
        return validateStep3(); // 工作表映射验证
      case 4:
        return validateStep4(); // 列映射验证
      default:
        return true;
    }
  }

  /**
   * 验证步骤 1: 文件选择
   * @returns {boolean}
   */
  /**
   * 验证步骤 1: 模板选择（新流程）
   * @returns {boolean}
   */
  function validateStep1() {
    // 模板选择是可选的，始终返回 true
    // 如果选择了模板，应用模板配置
    if (CustomImportWizard.selectedTemplate && CustomImportWizard.templateConfig) {
      applyTemplateConfig(CustomImportWizard.templateConfig);
    }
    return true;
  }

  /**
   * 验证步骤 2: 文件选择（新流程）
   * @returns {boolean}
   */
  function validateStep2() {
    if (!CustomImportWizard.selectedFile) {
      showMessage('请选择要导入的 Excel 文件', true);
      return false;
    }
    if (CustomImportWizard.isParsing) {
      showMessage('文件正在解析中，请稍候...', true);
      return false;
    }
    if (!CustomImportWizard.isParsed) {
      showMessage('文件尚未解析完成，请稍候...', true);
      return false;
    }
    return true;
  }

  /**
   * 验证步骤 3: 工作表映射
   * @returns {boolean}
   */
  function validateStep3() {
    const mappings = getSheetMappings();

    // 检查是否所有 sheet 都已映射或跳过
    const mappedCount = mappings.filter(function(m) {
      return m.table_name !== '';
    }).length;

    // 至少映射一个 sheet
    if (mappedCount === 0) {
      showMessage('请至少映射一个工作表', true);
      return false;
    }

    return true;
  }

  /**
   * 验证步骤 4: 列映射
   * @returns {boolean}
   */
  function validateStep4() {
    // 保存所有列映射配置
    saveAllColumnMappings();

    // 检查每个表的必填字段
    const sheetMappings = getSheetMappings();
    let allValid = true;
    const missingFields = [];

    sheetMappings.forEach(function(mapping) {
      if (!mapping.table_name) return;

      const tableConfig = getSystemTableConfig(mapping.table_name);
      if (!tableConfig) return;

      const columnMapping = CustomImportWizard.columnMappings[mapping.table_name];
      if (!columnMapping || !columnMapping.columns || columnMapping.columns.length === 0) {
        missingFields.push(getTableDisplayName(mapping.table_name) + ': 未配置任何列映射');
        allValid = false;
        return;
      }

      // 检查必填字段
      const mappedTargets = columnMapping.columns.map(function(c) { return c.target; });
      const requiredFields = tableConfig.fields.filter(function(f) { return f.required; });

      requiredFields.forEach(function(field) {
        if (mappedTargets.indexOf(field.name) === -1) {
          missingFields.push(getTableDisplayName(mapping.table_name) + ': 缺少必填字段 "' + field.display + '"');
          allValid = false;
        }
      });
    });

    if (!allValid) {
      showMessage('列映射配置不完整：\n' + missingFields.join('\n'), true);
      return false;
    }

    return true;
  }

  // ==================== 步骤 1: 文件选择 ====================

  /**
   * 处理拖拽悬停
   * @param {DragEvent} e
   */
  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('drag-over');
  }

  /**
   * 处理拖拽离开
   * @param {DragEvent} e
   */
  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');
  }

  /**
   * 处理文件拖放
   * @param {DragEvent} e
   */
  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFile(files[0]);
    }
  }

  /**
   * 处理文件选择
   * @param {Event} e
   */
  function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
      processFile(file);
    }
  }

  /**
   * 处理选中的文件
   * @param {File} file
   */
  function processFile(file) {
    // 验证文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      showMessage('请选择 .xlsx 或 .xls 格式的 Excel 文件', true);
      return;
    }

    CustomImportWizard.selectedFile = file;
    CustomImportWizard.fileName = file.name;

    // 显示加载状态
    showLoading('正在解析文件...');

    // 调用 API 解析文件
    parseExcelFile(file);
  }

  /**
   * 调用 API 解析 Excel 文件
   * @param {File} file
   */
  function parseExcelFile(file) {
    // 设置解析状态
    CustomImportWizard.isParsing = true;
    CustomImportWizard.isParsed = false;
    updateNavigationButtons();

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
        hideLoading();
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

          showMessage('文件解析成功，共 ' + data.sheets.length + ' 个工作表');
        } else {
          CustomImportWizard.isParsed = false;
          showMessage(data.error || '文件解析失败', true);
          resetFileSelection();
        }
        updateNavigationButtons();
      })
      .catch(function(error) {
        hideLoading();
        CustomImportWizard.isParsing = false;
        CustomImportWizard.isParsed = false;
        showMessage('解析文件时发生错误: ' + error.message, true);
        resetFileSelection();
        updateNavigationButtons();
      });
  }

  /**
   * 重置文件选择
   */
  function resetFileSelection() {
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
  }

  // ==================== 步骤 2: 模板选择 ====================

  /**
   * 检查是否有模板
   */
  function checkTemplates() {
    fetch(CustomImportWizard.api.getTemplates)
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          CustomImportWizard.templates = data.templates || [];

          if (CustomImportWizard.templates.length > 0) {
            CustomImportWizard.skipTemplateStep = false;
            renderTemplateList();
          } else {
            CustomImportWizard.skipTemplateStep = true;
            updateSkipTemplateUI();
          }
        }
      })
      .catch(function(error) {
        console.error('Failed to load templates:', error);
        CustomImportWizard.skipTemplateStep = true;
        updateSkipTemplateUI();
      });
  }

  /**
   * 渲染模板列表（表格布局）
   */
  function renderTemplateList() {
    const container = CustomImportWizard.elements.templateList;
    if (!container) return;

    // 清空容器
    clearContainer(container);

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
    const noTemplateRow = createTemplateTableRow(null, '不使用模板', true);
    tbody.appendChild(noTemplateRow);

    // 添加模板列表
    templates.forEach(function(template) {
      const row = createTemplateTableRow(template, template.name, false);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
  }

  /**
   * 创建模板表格行
   * @param {Object|null} template - 模板对象，null 表示"不使用模板"
   * @param {string} displayName - 显示名称
   * @param {boolean} isSelected - 是否选中
   * @returns {HTMLElement}
   */
  function createTemplateTableRow(template, displayName, isSelected) {
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
      timeCell.textContent = formatDate(template.updated_at);
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
        copyTemplate(template);
      };

      // 重命名按钮
      const renameBtn = document.createElement('button');
      renameBtn.type = 'button';
      renameBtn.className = 'btn btn-sm btn-secondary';
      renameBtn.textContent = '重命名';
      renameBtn.onclick = function(e) {
        e.stopPropagation();
        renameTemplate(template);
      };

      // 删除按钮
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'btn btn-sm btn-danger';
      deleteBtn.textContent = '删除';
      deleteBtn.onclick = function(e) {
        e.stopPropagation();
        deleteTemplate(template);
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
      selectTemplate(template);
    });

    return row;
  }

  /**
   * 复制模板
   * @param {Object} template
   */
  function copyTemplate(template) {
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
          renderTemplateList();
          showMessage('模板复制成功');
        } else {
          showMessage(data.error || '复制失败', true);
        }
      })
      .catch(function(error) {
        showMessage('复制失败: ' + error.message, true);
      });
  }

  /**
   * 选择模板
   * @param {Object|null} template
   */
  function selectTemplate(template) {
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
      applyTemplateConfig(template.config);
    }
  }

  /**
   * 应用模板配置到向导状态
   * @param {Object} config
   */
  function applyTemplateConfig(config) {
    if (!config) return;

    // 应用列映射配置
    if (config.column_mappings) {
      CustomImportWizard.columnMappings = config.column_mappings;
    }

    // 工作表映射会在解析文件后应用
    if (config.sheet_mappings) {
      CustomImportWizard.sheetMappings = config.sheet_mappings;
    }
  }

  /**
   * 重命名模板
   * @param {Object} template
   */
  function renameTemplate(template) {
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
            renderTemplateList();
            showMessage('模板重命名成功');
          } else {
            showMessage(data.error || '重命名失败', true);
          }
        })
        .catch(function(error) {
          showMessage('重命名失败: ' + error.message, true);
        });
    }
  }

  /**
   * 删除模板
   * @param {Object} template
   */
  function deleteTemplate(template) {
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

          renderTemplateList();
          showMessage('模板删除成功');

          // 检查是否需要跳过模板步骤
          if (CustomImportWizard.templates.length === 0) {
            CustomImportWizard.skipTemplateStep = true;
            updateSkipTemplateUI();
          }
        } else {
          showMessage(data.error || '删除失败', true);
        }
      })
      .catch(function(error) {
        showMessage('删除失败: ' + error.message, true);
      });
  }

  /**
   * 处理跳过模板复选框变化
   */
  function handleSkipTemplateChange() {
    const checkbox = CustomImportWizard.elements.skipTemplateCheckbox;
    CustomImportWizard.skipTemplateStep = checkbox ? checkbox.checked : true;
  }

  /**
   * 更新跳过模板 UI
   */
  function updateSkipTemplateUI() {
    const checkbox = CustomImportWizard.elements.skipTemplateCheckbox;
    if (checkbox) {
      checkbox.checked = CustomImportWizard.skipTemplateStep;
    }
  }

  // ==================== 步骤 3: 工作表映射 ====================

  /**
   * 渲染工作表映射界面
   */
  function renderSheetMapping() {
    const container = CustomImportWizard.elements.sheetMappingContainer;
    if (!container) return;

    // 清空容器
    clearContainer(container);

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
      addSheetMappingRow(rowsContainer, null);
    }

    // 更新进度
    updateSheetMappingProgress();

    // 如果有模板配置，自动填充映射
    if (templateMappings.length > 0) {
      applyTemplateSheetMappings(rowsContainer, templateMappings);
    }
  }

  /**
   * 添加工作表映射行
   * @param {HTMLElement} container
   * @param {Object|null} sheet - sheet 对象，null 表示空行
   * @returns {HTMLElement}
   */
  function addSheetMappingRow(container, sheet) {
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
    const availableSheets = getAvailableSheets(sheet ? sheet.name : null);
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
    const tableSelect = createTableSelect(null);

    // 删除按钮
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn btn-sm btn-secondary';
    deleteBtn.textContent = '删除';
    deleteBtn.onclick = function() {
      removeSheetMappingRow(row);
    };

    // 工作表选择变化事件
    sheetSelect.addEventListener('change', function() {
      row.dataset.sheetName = sheetSelect.value;
      updateSheetSelects();
      checkAndAddNewRow(container);
      updateSheetMappingProgress();
    });

    // 表选择变化事件
    tableSelect.addEventListener('change', function() {
      checkAndAddNewRow(container);
      updateSheetMappingProgress();
    });

    row.appendChild(sheetSelect);
    row.appendChild(arrow);
    row.appendChild(tableSelect);
    row.appendChild(deleteBtn);

    container.appendChild(row);

    return row;
  }

  /**
   * 创建系统表下拉框
   * @param {string|null} selectedValue
   * @returns {HTMLElement}
   */
  function createTableSelect(selectedValue) {
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
  }

  /**
   * 获取可用的 sheet（排除已选中的）
   * @param {string|null} currentSheet - 当前行选中的 sheet，不排除
   * @returns {Array}
   */
  function getAvailableSheets(currentSheet) {
    const selectedSheets = getSelectedSheetNames();
    return CustomImportWizard.parsedSheets.filter(function(sheet) {
      return sheet.name === currentSheet || selectedSheets.indexOf(sheet.name) === -1;
    });
  }

  /**
   * 获取已选中的 sheet 名称
   * @returns {Array}
   */
  function getSelectedSheetNames() {
    const rows = CustomImportWizard.elements.sheetMappingContainer.querySelectorAll('.sheet-mapping-row');
    const selected = [];
    rows.forEach(function(row) {
      const select = row.querySelector('.sheet-select');
      if (select && select.value) {
        selected.push(select.value);
      }
    });
    return selected;
  }

  /**
   * 更新所有 sheet 下拉框的选项
   */
  function updateSheetSelects() {
    const rows = CustomImportWizard.elements.sheetMappingContainer.querySelectorAll('.sheet-mapping-row');
    rows.forEach(function(row) {
      const sheetSelect = row.querySelector('.sheet-select');
      if (!sheetSelect) return;

      const currentValue = sheetSelect.value;

      // 重建选项 - 使用 clearContainer 安全清空
      clearContainer(sheetSelect);

      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.textContent = '-- 选择工作表 --';
      sheetSelect.appendChild(emptyOption);

      const availableSheets = getAvailableSheets(currentValue);
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
  }

  /**
   * 检查并添加新行
   * @param {HTMLElement} container
   */
  function checkAndAddNewRow(container) {
    const rows = container.querySelectorAll('.sheet-mapping-row');
    const lastRow = rows[rows.length - 1];

    if (!lastRow) {
      addSheetMappingRow(container, null);
      return;
    }

    const sheetSelect = lastRow.querySelector('.sheet-select');
    const tableSelect = lastRow.querySelector('.table-select');

    // 如果最后一行有选择，添加新行
    if (sheetSelect && tableSelect && sheetSelect.value && tableSelect.value) {
      // 检查是否还有未映射的 sheet
      const availableSheets = getAvailableSheets(null);
      if (availableSheets.length > 0) {
        addSheetMappingRow(container, null);
      }
    }
  }

  /**
   * 移除工作表映射行
   * @param {HTMLElement} row
   */
  function removeSheetMappingRow(row) {
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

    updateSheetSelects();
    updateSheetMappingProgress();
  }

  /**
   * 更新工作表映射进度指示器
   */
  function updateSheetMappingProgress() {
    const progressDiv = CustomImportWizard.elements.sheetMappingContainer.querySelector('.sheet-mapping-progress');
    if (!progressDiv) return;

    const totalSheets = CustomImportWizard.parsedSheets ? CustomImportWizard.parsedSheets.length : 0;
    const mappings = getSheetMappings();
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
  }

  /**
   * 获取工作表映射配置
   * @returns {Array}
   */
  function getSheetMappings() {
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
  }

  /**
   * 应用模板的工作表映射
   * @param {HTMLElement} container
   * @param {Array} templateMappings
   */
  function applyTemplateSheetMappings(container, templateMappings) {
    // 清空现有行
    clearContainer(container);

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
        const row = addSheetMappingRow(rowsContainer, sheet);
        const tableSelect = row.querySelector('.table-select');
        if (tableSelect) {
          tableSelect.value = mapping.table_name;
        }
      }
    });

    // 添加一个空行以便添加更多映射
    addSheetMappingRow(rowsContainer, null);

    updateSheetSelects();
    updateSheetMappingProgress();
  }

  // ==================== 步骤 4: 列映射 ====================

  /**
   * 渲染列映射界面
   */
  function renderColumnMapping() {
    const tabsContainer = CustomImportWizard.elements.columnMappingTabs;
    const container = CustomImportWizard.elements.columnMappingContainer;
    if (!tabsContainer || !container) return;

    // 清空容器
    clearContainer(tabsContainer);
    clearContainer(container);

    // 获取已映射的 sheet（排除了跳过的）
    const mappings = getSheetMappings().filter(function(m) {
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
      tab.textContent = getTableDisplayName(mapping.table_name);

      tab.addEventListener('click', function() {
        switchColumnMappingTab(mapping.table_name, mapping.sheet_name);
      });

      tabsContainer.appendChild(tab);
    });

    // 显示第一个标签页的内容
    const firstMapping = mappings[0];
    renderColumnMappingContent(firstMapping.table_name, firstMapping.sheet_name);

    // 更新进度指示器
    updateColumnMappingProgress();
  }

  /**
   * 切换列映射标签页
   * @param {string} tableName
   * @param {string} sheetName
   */
  function switchColumnMappingTab(tableName, sheetName) {
    // 先保存当前标签页的映射配置
    saveCurrentColumnMappings();

    // 更新标签页状态
    const tabs = CustomImportWizard.elements.columnMappingTabs.querySelectorAll('.column-mapping-tab');
    tabs.forEach(function(tab) {
      tab.classList.remove('active');
      if (tab.dataset.tableName === tableName) {
        tab.classList.add('active');
      }
    });

    // 渲染对应内容
    renderColumnMappingContent(tableName, sheetName);
  }

  /**
   * 保存当前标签页的列映射配置
   */
  function saveCurrentColumnMappings() {
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
  }

  /**
   * 渲染列映射内容
   * @param {string} tableName
   * @param {string} sheetName
   */
  function renderColumnMappingContent(tableName, sheetName) {
    const container = CustomImportWizard.elements.columnMappingContainer;
    if (!container) return;

    clearContainer(container);

    // 获取表配置
    const tableConfig = CustomImportWizard.systemTables.find(function(t) {
      return t.name === tableName;
    });

    // 从 SYSTEM_TABLES 获取详细字段配置（需要在运行时获取）
    const systemTableConfig = getSystemTableConfig(tableName);
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
      const carriageOptionsDiv = createCarriageOptions(mappingConfig);
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
      const row = createColumnMappingRow(excelColumns, systemTableConfig, colMapping, tbody);
      tbody.appendChild(row);
    });

    // 添加一个空行用于添加新映射
    const emptyRow = createColumnMappingRow(excelColumns, systemTableConfig, null, tbody);
    tbody.appendChild(emptyRow);

    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    container.appendChild(tableWrapper);

    // 创建冲突模式选择
    const conflictDiv = createConflictModeSelector(tableName, mappingConfig.conflict_mode);
    container.appendChild(conflictDiv);

    // 更新 Excel 列下拉菜单（禁用已选择的列）
    updateExcelColumnDropdowns(tbody, excelColumns);
    // 更新系统字段下拉菜单（禁用已选择的字段）
    updateSystemFieldDropdowns(tbody);

    // 更新进度
    updateColumnMappingProgress();
  }

  /**
   * 创建车厢模型额外选项
   * @param {Object} mappingConfig
   * @returns {HTMLElement}
   */
  function createCarriageOptions(mappingConfig) {
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
  }

  /**
   * 创建列映射行
   * @param {Array} excelColumns
   * @param {Object} tableConfig
   * @param {Object|null} existingMapping
   * @param {HTMLElement} tbody
   * @returns {HTMLElement}
   */
  function createColumnMappingRow(excelColumns, tableConfig, existingMapping, tbody) {
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
        displayText += ' (引用: ' + getTableDisplayName(field.ref) + ')';
      }

      option.textContent = displayText;

      // tooltip
      if (field.ref) {
        option.title = '此字段引用 ' + getTableDisplayName(field.ref) + ' 表，请确保该表已先导入';
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
      removeColumnMappingRow(row, tbody);
    };
    tdAction.appendChild(deleteBtn);
    row.appendChild(tdAction);

    // 事件处理
    excelSelect.addEventListener('change', function() {
      checkAndAddNewColumnRow(tbody, excelColumns, tableConfig);
      updateExcelColumnDropdowns(tbody, excelColumns);
      updateColumnMappingProgress();
    });

    systemSelect.addEventListener('change', function() {
      checkAndAddNewColumnRow(tbody, excelColumns, tableConfig);
      updateExcelColumnDropdowns(tbody, excelColumns);
      updateSystemFieldDropdowns(tbody);
      updateColumnMappingProgress();
    });

    return row;
  }

  /**
   * 获取当前已选择的 Excel 列
   * @param {HTMLElement} tbody
   * @param {HTMLElement} excludeRow - 排除的行（当前正在选择的行）
   * @returns {Array}
   */
  function getSelectedExcelColumns(tbody, excludeRow) {
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
  }

  /**
   * 获取当前已选择的系统字段
   * @param {HTMLElement} tbody
   * @param {HTMLElement} excludeRow - 排除的行（当前正在选择的行）
   * @returns {Array}
   */
  function getSelectedSystemFields(tbody, excludeRow) {
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
  }

  /**
   * 更新所有 Excel 列下拉菜单，禁用已选择的列
   * @param {HTMLElement} tbody
   * @param {Array} excelColumns
   */
  function updateExcelColumnDropdowns(tbody, excelColumns) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    rows.forEach(function(row) {
      const select = row.querySelector('.excel-column-select');
      if (!select) return;

      const currentValue = select.value;
      const selectedInOtherRows = getSelectedExcelColumns(tbody, row);

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
  }

  /**
   * 更新所有系统字段下拉菜单，禁用已选择的字段
   * @param {HTMLElement} tbody
   */
  function updateSystemFieldDropdowns(tbody) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    rows.forEach(function(row) {
      const select = row.querySelector('.system-field-select');
      if (!select) return;

      const currentValue = select.value;
      const selectedInOtherRows = getSelectedSystemFields(tbody, row);

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
  }

  /**
   * 检查并添加新的列映射行
   * @param {HTMLElement} tbody
   * @param {Array} excelColumns
   * @param {Object} tableConfig
   */
  function checkAndAddNewColumnRow(tbody, excelColumns, tableConfig) {
    const rows = tbody.querySelectorAll('.column-mapping-row');
    const lastRow = rows[rows.length - 1];

    if (!lastRow) return;

    const excelSelect = lastRow.querySelector('.excel-column-select');
    const systemSelect = lastRow.querySelector('.system-field-select');

    // 如果最后一行有选择，添加新行
    if (excelSelect && systemSelect && excelSelect.value && systemSelect.value) {
      const newRow = createColumnMappingRow(excelColumns, tableConfig, null, tbody);
      tbody.appendChild(newRow);
    }
  }

  /**
   * 移除列映射行
   * @param {HTMLElement} row
   * @param {HTMLElement} tbody
   */
  function removeColumnMappingRow(row, tbody) {
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
    updateExcelColumnDropdowns(tbody, excelColumns);
    updateSystemFieldDropdowns(tbody);
    updateColumnMappingProgress();
  }

  /**
   * 创建冲突模式选择器
   * @param {string} tableName
   * @param {string} currentMode
   * @returns {HTMLElement}
   */
  function createConflictModeSelector(tableName, currentMode) {
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
  }

  /**
   * 获取系统表配置（包含详细字段信息）
   * @param {string} tableName
   * @returns {Object|null}
   */
  function getSystemTableConfig(tableName) {
    // 内置的表配置（与后端 SYSTEM_TABLES 保持一致）
    var systemTableConfigs = {
      'brand': {
        display_name: '品牌',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true},
          {name: 'search_url', display: '搜索地址', required: false}
        ]
      },
      'depot': {
        display_name: '配属',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'merchant': {
        display_name: '商家',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'power_type': {
        display_name: '动力类型',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'chip_interface': {
        display_name: '芯片接口',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'chip_model': {
        display_name: '芯片型号',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'locomotive_series': {
        display_name: '机车系列',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'carriage_series': {
        display_name: '车厢系列',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'trainset_series': {
        display_name: '动车组系列',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true, unique: true}
        ]
      },
      'locomotive_model': {
        display_name: '机车车型',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true},
          {name: 'series_id', display: '系列', required: true, ref: 'locomotive_series'},
          {name: 'power_type_id', display: '动力类型', required: true, ref: 'power_type'}
        ]
      },
      'carriage_model': {
        display_name: '车厢车型',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true},
          {name: 'series_id', display: '系列', required: true, ref: 'carriage_series'},
          {name: 'type', display: '类型', required: true}
        ]
      },
      'trainset_model': {
        display_name: '动车组车型',
        category: 'system',
        fields: [
          {name: 'name', display: '名称', required: true},
          {name: 'series_id', display: '系列', required: true, ref: 'trainset_series'},
          {name: 'power_type_id', display: '动力类型', required: true, ref: 'power_type'}
        ]
      },
      'locomotive': {
        display_name: '机车模型',
        category: 'model',
        fields: [
          {name: 'brand_id', display: '品牌', required: true, ref: 'brand'},
          {name: 'scale', display: '比例', required: true},
          {name: 'series_id', display: '系列', required: false, ref: 'locomotive_series'},
          {name: 'power_type_id', display: '动力', required: false, ref: 'power_type'},
          {name: 'model_id', display: '车型', required: false, ref: 'locomotive_model'},
          {name: 'depot_id', display: '配属', required: false, ref: 'depot'},
          {name: 'plaque', display: '挂牌', required: false},
          {name: 'color', display: '颜色', required: false},
          {name: 'locomotive_number', display: '机车号', required: false, unique_in_scale: true},
          {name: 'decoder_number', display: '编号', required: false, unique_in_scale: true},
          {name: 'chip_interface_id', display: '芯片接口', required: false, ref: 'chip_interface'},
          {name: 'chip_model_id', display: '芯片型号', required: false, ref: 'chip_model'},
          {name: 'price', display: '价格', required: false},
          {name: 'item_number', display: '货号', required: false},
          {name: 'purchase_date', display: '购买日期', required: false},
          {name: 'merchant_id', display: '购买商家', required: false, ref: 'merchant'}
        ]
      },
      'carriage': {
        display_name: '车厢模型',
        category: 'model',
        fields: [
          {name: 'brand_id', display: '品牌', required: true, ref: 'brand', is_set_field: true},
          {name: 'scale', display: '比例', required: true, is_set_field: true},
          {name: 'series_id', display: '系列', required: false, ref: 'carriage_series', is_set_field: true},
          {name: 'depot_id', display: '配属', required: false, ref: 'depot', is_set_field: true},
          {name: 'train_number', display: '车次', required: false, is_set_field: true},
          {name: 'plaque', display: '挂牌', required: false, is_set_field: true},
          {name: 'item_number', display: '货号', required: false, is_set_field: true},
          {name: 'total_price', display: '总价', required: false, is_set_field: true},
          {name: 'purchase_date', display: '购买日期', required: false, is_set_field: true},
          {name: 'merchant_id', display: '购买商家', required: false, ref: 'merchant', is_set_field: true},
          {name: 'model_id', display: '车型', required: false, ref: 'carriage_model', is_item_field: true},
          {name: 'car_number', display: '车辆号', required: false, is_item_field: true},
          {name: 'color', display: '颜色', required: false, is_item_field: true},
          {name: 'lighting', display: '灯光', required: false, is_item_field: true}
        ]
      },
      'trainset': {
        display_name: '动车组模型',
        category: 'model',
        fields: [
          {name: 'brand_id', display: '品牌', required: true, ref: 'brand'},
          {name: 'scale', display: '比例', required: true},
          {name: 'series_id', display: '系列', required: false, ref: 'trainset_series'},
          {name: 'power_type_id', display: '动力', required: false, ref: 'power_type'},
          {name: 'model_id', display: '车型', required: false, ref: 'trainset_model'},
          {name: 'depot_id', display: '配属', required: false, ref: 'depot'},
          {name: 'plaque', display: '挂牌', required: false},
          {name: 'color', display: '颜色', required: false},
          {name: 'formation', display: '编组', required: false},
          {name: 'trainset_number', display: '动车号', required: false, unique_in_scale: true},
          {name: 'decoder_number', display: '编号', required: false},
          {name: 'head_light', display: '头车灯', required: false},
          {name: 'interior_light', display: '室内灯', required: false},
          {name: 'chip_interface_id', display: '芯片接口', required: false, ref: 'chip_interface'},
          {name: 'chip_model_id', display: '芯片型号', required: false, ref: 'chip_model'},
          {name: 'price', display: '价格', required: false},
          {name: 'item_number', display: '货号', required: false},
          {name: 'purchase_date', display: '购买日期', required: false},
          {name: 'merchant_id', display: '购买商家', required: false, ref: 'merchant'}
        ]
      },
      'locomotive_head': {
        display_name: '先头车模型',
        category: 'model',
        fields: [
          {name: 'brand_id', display: '品牌', required: true, ref: 'brand'},
          {name: 'scale', display: '比例', required: true},
          {name: 'model_id', display: '车型', required: false, ref: 'trainset_model'},
          {name: 'special_color', display: '涂装', required: false},
          {name: 'head_light', display: '头车灯', required: false},
          {name: 'interior_light', display: '室内灯', required: false},
          {name: 'price', display: '价格', required: false},
          {name: 'item_number', display: '货号', required: false},
          {name: 'purchase_date', display: '购买日期', required: false},
          {name: 'merchant_id', display: '购买商家', required: false, ref: 'merchant'}
        ]
      }
    };

    return systemTableConfigs[tableName] || null;
  }

  /**
   * 更新列映射进度指示器
   */
  function updateColumnMappingProgress() {
    const activeTab = CustomImportWizard.elements.columnMappingTabs.querySelector('.column-mapping-tab.active');
    if (!activeTab) return;

    const tableName = activeTab.dataset.tableName;
    const tableConfig = getSystemTableConfig(tableName);
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
  }

  /**
   * 获取列映射配置
   * @param {string} tableName
   * @returns {Object}
   */
  function getColumnMappings(tableName) {
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
  }

  /**
   * 保存所有列映射配置
   */
  function saveAllColumnMappings() {
    const tabs = CustomImportWizard.elements.columnMappingTabs.querySelectorAll('.column-mapping-tab');
    tabs.forEach(function(tab) {
      const tableName = tab.dataset.tableName;
      getColumnMappings(tableName);
    });
  }

  // ==================== 步骤 5: 确认导入 ====================

  /**
   * 渲染确认页面
   * @param {Object|null} previewData - 预览 API 返回的数据
   */
  function renderConfirmPage(previewData) {
    const tabsContainer = CustomImportWizard.elements.importSummaryTabs;
    const container = CustomImportWizard.elements.importSummary;
    if (!tabsContainer || !container) return;

    clearContainer(tabsContainer);
    clearContainer(container);

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
        renderConfirmPageContent(preview);
      });

      tabsContainer.appendChild(tab);
    });

    // 渲染第一个标签页的内容
    renderConfirmPageContent(previewData.previews[0]);

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
  }

  /**
   * 渲染确认页面单个表的预览内容
   * @param {Object} preview
   */
  function renderConfirmPageContent(preview) {
    const container = CustomImportWizard.elements.importSummary;
    if (!container) return;

    // 清空容器但保留总体状态
    const statusDivs = container.querySelectorAll('.import-result');
    clearContainer(container);
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
  }

  /**
   * 获取表显示名称
   * @param {string} tableName
   * @returns {string}
   */
  function getTableDisplayName(tableName) {
    const table = CustomImportWizard.systemTables.find(function(t) {
      return t.name === tableName;
    });
    return table ? table.display_name : tableName;
  }

  /**
   * 执行导入
   */
  function executeImport() {
    // 如果导入已完成，不重复执行
    if (CustomImportWizard.importCompleted) {
      return;
    }

    const previewResult = CustomImportWizard.previewResult;

    // 检查是否可以导入
    if (previewResult && !previewResult.can_proceed) {
      showMessage('存在配置问题，无法导入。请返回上一步检查。', true);
      return;
    }

    // 显示加载状态
    showLoading('正在导入数据，请稍候...');
    disableNavigationButtons();

    // 构建配置
    const config = {
      sheet_mappings: getSheetMappings(),
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
        hideLoading();
        enableNavigationButtons();

        if (data.success) {
          // 存储导入结果
          CustomImportWizard.importResult = data;

          // 显示成功结果
          renderImportSuccess(data);

          // 保存模板（如果选择了）
          saveTemplateIfNeeded(data);
        } else {
          // 显示失败结果
          renderImportError(data);
        }
      })
      .catch(function(error) {
        // 如果导入已完成，忽略错误（可能是页面重新加载导致的）
        if (CustomImportWizard.importCompleted) {
          return;
        }
        hideLoading();
        enableNavigationButtons();
        showMessage('导入时发生错误: ' + error.message, true);
        renderImportError({ error: error.message });
      });
  }

  /**
   * 禁用导航按钮
   */
  function disableNavigationButtons() {
    const els = CustomImportWizard.elements;
    if (els.btnPrev) els.btnPrev.disabled = true;
    if (els.btnNext) els.btnNext.disabled = true;
    if (els.btnFinish) els.btnFinish.disabled = true;
    if (els.btnCancel) els.btnCancel.disabled = true;
  }

  /**
   * 启用导航按钮
   */
  function enableNavigationButtons() {
    const els = CustomImportWizard.elements;
    if (els.btnPrev) els.btnPrev.disabled = false;
    if (els.btnNext) els.btnNext.disabled = false;
    if (els.btnFinish) els.btnFinish.disabled = false;
    if (els.btnCancel) els.btnCancel.disabled = false;
  }

  /**
   * 渲染导入成功结果
   * @param {Object} data - API 返回的数据
   */
  function renderImportSuccess(data) {
    const container = CustomImportWizard.elements.importSummary;
    if (!container) return;

    clearContainer(container);

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
          tdTable.textContent = getTableDisplayName(tableName);
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
        closeModal();
        // 刷新页面以显示新数据
        window.location.reload();
      };
    }

    // 将"取消"按钮改为"重新导入"按钮
    if (els.btnCancel) {
      els.btnCancel.textContent = '重新导入';
      els.btnCancel.className = 'btn btn-secondary';
      els.btnCancel.onclick = function() {
        resetWizard();
      };
    }
  }

  /**
   * 渲染导入失败结果
   * @param {Object} data - API 返回的错误数据
   */
  function renderImportError(data) {
    const container = CustomImportWizard.elements.importSummary;
    if (!container) return;

    clearContainer(container);

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
            summaryHtml += '<li>' + getTableDisplayName(tableName) + ': ' + count + ' 条</li>';
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
        resetFooterButtons();
        // 返回步骤 4
        CustomImportWizard.currentStep = 4;
        updateStepIndicators();
        showCurrentStep();
        updateNavigationButtons();
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
        closeModal();
      };
      footerRight.appendChild(closeBtn);
    }
  }

  /**
   * 如果选择了保存模板，则在导入成功后保存
   * @param {Object} importResult - 导入结果
   */
  function saveTemplateIfNeeded(importResult) {
    const mode = getSaveTemplateMode();

    if (mode === 'none') {
      return;
    }

    // 构建模板配置
    const templateConfig = {
      sheet_mappings: getSheetMappings(),
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
            showMessage('模板 "' + name + '" 保存成功');
            // 刷新模板列表
            checkTemplates();
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
            showMessage('模板更新成功');
            // 刷新模板列表
            checkTemplates();
          } else {
            console.error('Failed to update template:', data.error);
          }
        })
        .catch(function(error) {
          console.error('Error updating template:', error);
        });
    }
  }

  // ==================== 辅助函数 ====================

  /**
   * 加载系统表格配置
   */
  function loadSystemTables() {
    fetch(CustomImportWizard.api.getTables)
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          CustomImportWizard.systemTables = data.tables || [];
        }
      })
      .catch(function(error) {
        console.error('Failed to load system tables:', error);
      });
  }

  /**
   * 处理保存模板复选框变化
   */
  function handleSaveTemplateModeChange() {
    const els = CustomImportWizard.elements;
    const selectedMode = getSaveTemplateMode();

    // 显示/隐藏新模板名称输入框
    if (els.newTemplateNameContainer) {
      els.newTemplateNameContainer.style.display = (selectedMode === 'new') ? 'block' : 'none';
    }

    // 显示/隐藏更新模板选择框
    if (els.updateTemplateSelectContainer) {
      els.updateTemplateSelectContainer.style.display = (selectedMode === 'update') ? 'block' : 'none';
    }

    // 如果选择更新模板，填充模板列表
    if (selectedMode === 'update' && els.updateTemplateSelect) {
      populateUpdateTemplateSelect();
    }
  }

  /**
   * 获取保存模板模式
   * @returns {string} 'none' | 'new' | 'update'
   */
  function getSaveTemplateMode() {
    const els = CustomImportWizard.elements;
    let mode = 'none';
    els.saveTemplateModeRadios.forEach(function(radio) {
      if (radio.checked) {
        mode = radio.value;
      }
    });
    return mode;
  }

  /**
   * 填充更新模板选择框
   */
  function populateUpdateTemplateSelect() {
    const select = CustomImportWizard.elements.updateTemplateSelect;
    if (!select) return;

    // 清空选项
    clearContainer(select);

    // 添加空选项
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '-- 选择模板 --';
    select.appendChild(emptyOption);

    // 添加模板选项
    CustomImportWizard.templates.forEach(function(template) {
      const option = document.createElement('option');
      option.value = template.id;
      option.textContent = template.name;
      select.appendChild(option);
    });
  }

  /**
   * 显示消息
   * @param {string} message
   * @param {boolean} isError
   */
  function showMessage(message, isError) {
    // 使用简单的 alert，可以后续替换为更友好的提示
    if (isError) {
      alert('错误: ' + message);
    } else {
      alert(message);
    }
  }

  /**
   * 显示加载状态
   * @param {string} message
   */
  function showLoading(message) {
    // 可以后续实现加载动画
    console.log('Loading:', message);
  }

  /**
   * 隐藏加载状态
   */
  function hideLoading() {
    console.log('Loading complete');
  }

  /**
   * 格式化日期
   * @param {string} isoDate
   * @returns {string}
   */
  function formatDate(isoDate) {
    if (!isoDate) return '';
    const date = new Date(isoDate);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // ==================== 导出 ====================

  // 初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // 导出公共方法（用于调试或外部调用）
  window.CustomImportWizard = {
    open: openModal,
    close: closeModal,
    reset: resetWizard
  };

})();
