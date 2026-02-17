/**
 * 系统维护页面 JavaScript
 */
(function() {
  'use strict';

  // DOM 元素
  const btnExportModels = document.getElementById('btn-export-models');
  const btnExportSystem = document.getElementById('btn-export-system');
  const btnExportAll = document.getElementById('btn-export-all');
  const btnImport = document.getElementById('btn-import');
  const importFile = document.getElementById('import-file');
  const importFilename = document.getElementById('import-filename');
  const btnReinit = document.getElementById('btn-reinit');
  const confirmDialog = document.getElementById('confirm-dialog');
  const confirmMessage = document.getElementById('confirm-message');
  const btnCancel = document.getElementById('btn-cancel');
  const btnConfirm = document.getElementById('btn-confirm');

  // 当前待确认的操作
  let pendingAction = null;

  /**
   * 显示消息提示
   */
  function showMessage(message, isError) {
    alert(isError ? '错误: ' + message : message);
  }

  /**
   * 显示确认对话框
   */
  function showConfirmDialog(message, action) {
    confirmMessage.textContent = message;
    pendingAction = action;
    confirmDialog.style.display = 'flex';
  }

  /**
   * 隐藏确认对话框
   */
  function hideConfirmDialog() {
    confirmDialog.style.display = 'none';
    pendingAction = null;
  }

  /**
   * 导出数据到 Excel
   * @param {string} mode - 导出模式: 'models', 'system', 'all'
   * @param {HTMLElement} button - 触发的按钮元素
   */
  function exportToExcel(mode, button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = '导出中...';

    fetch('/api/export/excel?mode=' + mode)
      .then(function(response) {
        if (!response.ok) {
          return response.json().then(function(data) {
            throw new Error(data.error || '导出失败');
          });
        }
        // 从响应头获取文件名
        var contentDisposition = response.headers.get('Content-Disposition');
        var filename = 'export.xlsx';
        if (contentDisposition) {
          var filenameMatch = contentDisposition.match(/filename\*?=['"]?(?:UTF-\d['"]*)?([^'";\s]+)['"]?;?/i);
          if (filenameMatch && filenameMatch[1]) {
            filename = decodeURIComponent(filenameMatch[1]);
          }
        }
        return response.blob().then(function(blob) {
          return { blob: blob, filename: filename };
        });
      })
      .then(function(result) {
        // 创建下载链接
        var url = window.URL.createObjectURL(result.blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = result.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showMessage('导出成功！');
      })
      .catch(function(error) {
        showMessage(error.message, true);
      })
      .finally(function() {
        button.disabled = false;
        button.textContent = originalText;
      });
  }

  /**
   * 从 Excel 导入数据（自适应导入）
   */
  function importFromExcel(file) {
    btnImport.disabled = true;
    btnImport.textContent = '导入中...';

    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/import/excel', {
      method: 'POST',
      body: formData
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          let message = '导入成功！';
          if (data.summary && Object.keys(data.summary).length > 0) {
            const parts = [];
            for (const key in data.summary) {
              parts.push(key + ': ' + data.summary[key] + ' 条');
            }
            message += '\n' + parts.join('，');
          } else {
            message += '\n没有找到可导入的数据（请检查工作表名称是否正确）';
          }
          showMessage(message);
        } else {
          throw new Error(data.error || '导入失败');
        }
      })
      .catch(function(error) {
        showMessage(error.message, true);
      })
      .finally(function() {
        btnImport.disabled = false;
        btnImport.textContent = '从 Excel 导入数据';
        importFile.value = '';
        importFilename.textContent = '';
      });
  }

  /**
   * 重新初始化数据库
   */
  function reinitDatabase() {
    btnReinit.disabled = true;
    btnReinit.textContent = '初始化中...';

    fetch('/system/reinit', {
      method: 'POST'
    })
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        if (data.success) {
          showMessage(data.message || '数据库重新初始化成功！');
        } else {
          throw new Error(data.error || '初始化失败');
        }
      })
      .catch(function(error) {
        showMessage(error.message, true);
      })
      .finally(function() {
        btnReinit.disabled = false;
        btnReinit.textContent = '重新初始化数据库';
      });
  }

  // 事件绑定 - 导出按钮
  btnExportModels.addEventListener('click', function() {
    exportToExcel('models', btnExportModels);
  });

  btnExportSystem.addEventListener('click', function() {
    exportToExcel('system', btnExportSystem);
  });

  btnExportAll.addEventListener('click', function() {
    exportToExcel('all', btnExportAll);
  });

  // 事件绑定 - 导入
  btnImport.addEventListener('click', function() {
    importFile.click();
  });

  importFile.addEventListener('change', function() {
    const file = importFile.files[0];
    if (file) {
      importFilename.textContent = file.name;
      importFromExcel(file);
    }
  });

  // 事件绑定 - 数据库初始化
  btnReinit.addEventListener('click', function() {
    showConfirmDialog(
      '确定要重新初始化数据库吗？此操作将删除所有数据，且不可撤销！',
      reinitDatabase
    );
  });

  btnCancel.addEventListener('click', hideConfirmDialog);

  btnConfirm.addEventListener('click', function() {
    if (pendingAction) {
      pendingAction();
    }
    hideConfirmDialog();
  });

  // 点击遮罩层关闭对话框
  confirmDialog.addEventListener('click', function(e) {
    if (e.target === confirmDialog) {
      hideConfirmDialog();
    }
  });
})();
