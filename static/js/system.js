/**
 * 系统维护页面 JavaScript
 */
(function() {
  'use strict';

  // DOM 元素
  const btnExport = document.getElementById('btn-export');
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
   */
  function exportToExcel() {
    btnExport.disabled = true;
    btnExport.textContent = '导出中...';

    fetch('/api/export/excel')
      .then(function(response) {
        if (!response.ok) {
          return response.json().then(function(data) {
            throw new Error(data.error || '导出失败');
          });
        }
        return response.blob();
      })
      .then(function(blob) {
        // 创建下载链接
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'train_models_' + new Date().toISOString().slice(0, 10) + '.xlsx';
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
        btnExport.disabled = false;
        btnExport.textContent = '导出数据到 Excel';
      });
  }

  /**
   * 从 Excel 导入数据
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
          if (data.summary) {
            const parts = [];
            for (const key in data.summary) {
              parts.push(key + ': ' + data.summary[key] + ' 条');
            }
            message += '\n' + parts.join('，');
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

  // 事件绑定
  btnExport.addEventListener('click', exportToExcel);

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
