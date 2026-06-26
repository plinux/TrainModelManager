/**
 * 火车模型管理系统 - 文件管理模块
 *
 * 提供：
 *   - FileManager：模型文件上传/下载/预览/删除、模型详情渲染、功能键编辑
 *   - initFileManagerModal：页面加载时初始化模型详情模态框 + 表格文件状态
 *
 * 依赖（按加载顺序）：modal.js、api.js、dropdowns.js、tables.js、forms.js
 */
(function (global) {
  'use strict';

  /**
   * 文件管理器
   * 处理模型文件的上传、下载、预览、删除等功能
   */
  const FileManager = {
    // 当前模型信息
    currentModel: {
      type: null,
      id: null,
      files: null
    },

    // 属性名称映射（中文显示名）
    attributeNames: {
      'brand': '品牌',
      'series': '系列',
      'model': '型号',
      'power_type': '动力',
      'depot': '配属',
      'scale': '比例',
      'locomotive_number': '机车号',
      'trainset_number': '动车号',
      'decoder_number': '编号',
      'plaque': '挂牌',
      'color': '颜色',
      'special_color': '涂装',
      'chip_interface': '芯片接口',
      'chip_model': '芯片型号',
      'head_light': '头车灯',
      'light_model': '室内灯',
      'formation': '编组',
      'price': '价格',
      'total_price': '总价',
      'item_number': '货号',
      'purchase_date': '购买日期',
      'merchant': '购买商家',
      'train_number': '车次'
    },

    /**
     * 显示模型详情
     * @param {string} modelType - 模型类型
     * @param {number} modelId - 模型ID
     */
    showModelDetail(modelType, modelId) {
      this.currentModel.type = modelType;
      this.currentModel.id = modelId;

      fetch(`/api/files/model/${modelType}/${modelId}`)
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            this.currentModel.files = data.model.files;
            this.renderModelDetail(data.model);
            ModalManager.open('model-detail-modal');
          } else {
            alert('获取模型详情失败: ' + (data.error || '未知错误'));
          }
        })
        .catch(error => {
          console.error('获取模型详情失败:', error);
          alert('获取模型详情失败');
        });
    },

    /**
     * 渲染模型详情
     * @param {Object} model - 模型数据
     */
    renderModelDetail(model) {
      const hasFunctionTable = model.type !== 'locomotive_head';

      // 渲染图片
      this.renderImage(model.files.image);

      // 渲染属性表
      this.renderAttributes(model.attributes);

      // 渲染功能表（先头车无）
      if (hasFunctionTable) {
        this.renderFunctionTable(model.files.function_table);
      } else {
        // 先头车没有数码功能表，隐藏该区域
        const container = document.getElementById('function-table-container');
        if (container) {
          const section = container.closest('.model-file-section');
          if (section) {
            section.style.display = 'none';
          }
        }
      }

      // 渲染说明书列表
      this.renderManuals(model.files.manual);
    },

    /**
     * 渲染图片
     * @param {Object} imageFile - 图片文件信息
     */
    renderImage(imageFile) {
      const img = document.getElementById('model-detail-image');
      const placeholder = document.getElementById('model-detail-image-placeholder');
      const btnView = document.getElementById('btn-view-image');
      const btnDownload = document.getElementById('btn-download-image');
      const btnDelete = document.getElementById('btn-delete-image');

      if (imageFile) {
        img.src = `/api/files/view/${imageFile.id}`;
        img.style.display = 'block';
        placeholder.style.display = 'none';
        btnView.style.display = 'inline-block';
        if (btnDownload) btnDownload.style.display = 'inline-block';
        btnDelete.style.display = 'inline-block';
      } else {
        img.src = '';
        img.style.display = 'none';
        placeholder.style.display = 'flex';
        btnView.style.display = 'none';
        if (btnDownload) btnDownload.style.display = 'none';
        btnDelete.style.display = 'none';
      }
    },

    /**
     * 渲染属性表
     * @param {Object} attributes - 属性对象
     */
    renderAttributes(attributes) {
      const tbody = document.querySelector('#model-attributes-table tbody');
      while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
      }

      // purchase_date 放最后，不包含 product_url（作为货号链接处理）
      const displayOrder = ['brand', 'series', 'model', 'power_type', 'scale',
        'locomotive_number', 'trainset_number', 'decoder_number', 'depot',
        'plaque', 'color', 'special_color', 'formation', 'head_light',
        'light_model', 'chip_interface', 'chip_model', 'price', 'total_price',
        'item_number', 'merchant', 'train_number', 'purchase_date'];

      displayOrder.forEach(key => {
        if (attributes[key] !== undefined && attributes[key] !== null && attributes[key] !== '') {
          const tr = document.createElement('tr');
          const th = document.createElement('th');
          const td = document.createElement('td');

          th.textContent = this.attributeNames[key] || key;

          let value = attributes[key];
          // 处理布尔值
          if (key === 'head_light') {
            value = value === true || value === 'true' ? '有' : '无';
            td.textContent = value;
          }
          // 处理财号：如果有产品地址，显示为链接
          else if (key === 'item_number') {
            const productUrl = attributes['product_url'];
            // 仅允许 http(s) 协议，防止 javascript: 等协议触发 XSS
            if (productUrl && /^https?:\/\//i.test(productUrl)) {
              const link = document.createElement('a');
              link.href = productUrl;
              link.target = '_blank';
              link.rel = 'noopener noreferrer';
              link.textContent = value;
              td.appendChild(link);
            } else {
              td.textContent = value;
            }
          }
          // 处理购买日期：只显示日期部分
          else if (key === 'purchase_date') {
            if (value) {
              if (value.includes('T')) {
                value = value.split('T')[0];
              } else if (value.includes(' ')) {
                value = value.split(' ')[0];
              }
            }
            td.textContent = value;
          }
          else {
            td.textContent = value;
          }

          tr.appendChild(th);
          tr.appendChild(td);
          tbody.appendChild(tr);
        }
      });
    },

    /**
     * 渲染功能表
     * @param {Object} functionTable - 功能表文件信息
     */
    renderFunctionTable(functionTable) {
      const statusContainer = document.getElementById('function-table-status');
      const btnView = document.getElementById('btn-view-function-table');
      const btnDownload = document.getElementById('btn-download-function-table');
      const btnDelete = document.getElementById('btn-delete-function-table');

      if (!statusContainer) return;

      // 显示功能表区域（先头车可能隐藏了）
      const section = statusContainer.closest('.model-file-section');
      if (section) {
        section.style.display = 'block';
      }

      // 保存文件引用
      this.currentModel.files.function_table = functionTable;

      // 更新状态显示
      statusContainer.innerHTML = '';
      if (functionTable) {
        const status = document.createElement('span');
        status.className = 'file-status file-status-exists';
        const displayName = functionTable.stored_filename || functionTable.original_filename;
        status.textContent = displayName;
        status.title = displayName;
        statusContainer.appendChild(status);

        // 显示操作按钮
        if (btnView) btnView.style.display = 'inline-block';
        if (btnDownload) btnDownload.style.display = 'inline-block';
        if (btnDelete) btnDelete.style.display = 'inline-block';
      } else {
        const status = document.createElement('span');
        status.className = 'file-status file-status-none';
        status.textContent = '未上传';
        statusContainer.appendChild(status);

        // 隐藏操作按钮
        if (btnView) btnView.style.display = 'none';
        if (btnDownload) btnDownload.style.display = 'none';
        if (btnDelete) btnDelete.style.display = 'none';
      }

      // 自动加载功能键解析结果
      if (functionTable) {
        this.loadFunctionKeys();
      } else {
        this.renderFunctionKeyTable(null);
      }
    },

    /**
     * 加载功能键解析结果
     */
    async loadFunctionKeys() {
      if (!this.currentModel) return;
      const { type, id } = this.currentModel;
      if (type === 'locomotive_head') return;

      try {
        const resp = await fetch(`/api/files/function-keys/${type}/${id}`);
        const data = await resp.json();
        if (data.success) {
          this.renderFunctionKeyTable(data.keys);
        }
      } catch (err) {
        console.error('加载功能键失败:', err);
      }
    },

    /**
     * 渲染功能键表格
     * @param {Array|null} keys - 功能键数据列表
     */
    renderFunctionKeyTable(keys) {
      const container = document.getElementById('function-keys-container');
      const btnRow = document.getElementById('function-keys-actions');
      if (!container) return;

      container.innerHTML = '';

      if (!keys || keys.length === 0) {
        if (btnRow) btnRow.style.display = 'none';
        return;
      }

      if (btnRow) btnRow.style.display = 'flex';

      // 构建表格
      const table = document.createElement('table');
      table.className = 'function-keys-table';

      const thead = document.createElement('thead');
      thead.innerHTML = '<tr><th>功能键</th><th>功能名称</th><th>说明</th></tr>';
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      keys.forEach(key => {
        const tr = document.createElement('tr');
        // createElement + textContent 防止 function_name/description 存储型 XSS
        const tdNumber = document.createElement('td');
        tdNumber.className = 'key-number';
        tdNumber.textContent = `F${key.key_number}`;

        const tdName = document.createElement('td');
        tdName.className = 'key-name';
        tdName.contentEditable = 'false';
        tdName.dataset.keyId = key.id;
        tdName.dataset.field = 'function_name';
        tdName.textContent = key.function_name || '';

        const tdDesc = document.createElement('td');
        tdDesc.className = 'key-desc';
        tdDesc.contentEditable = 'false';
        tdDesc.dataset.keyId = key.id;
        tdDesc.dataset.field = 'description';
        tdDesc.textContent = key.description || '';

        tr.appendChild(tdNumber);
        tr.appendChild(tdName);
        tr.appendChild(tdDesc);
        // 双击进入编辑模式
        tr.querySelectorAll('[contenteditable]').forEach(cell => {
          cell.addEventListener('dblclick', () => {
            cell.contentEditable = 'true';
            cell.focus();
          });
          cell.addEventListener('blur', () => {
            cell.contentEditable = 'false';
            this.saveFunctionKeyField(cell);
          });
          cell.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              cell.blur();
            }
          });
        });
        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
      container.appendChild(table);
    },

    /**
     * 保存单个功能键字段
     * @param {HTMLElement} cell - 可编辑单元格
     */
    async saveFunctionKeyField(cell) {
      if (!this.currentModel) return;
      const { type, id } = this.currentModel;

      // 收集所有行数据
      const rows = cell.closest('tbody').querySelectorAll('tr');
      const keysData = [];
      rows.forEach(row => {
        const nameCell = row.querySelector('.key-name');
        const descCell = row.querySelector('.key-desc');
        const numCell = row.querySelector('.key-number');
        const keyNum = parseInt(numCell.textContent.replace('F', ''));
        keysData.push({
          key_number: keyNum,
          function_name: nameCell.textContent.trim(),
          description: descCell.textContent.trim()
        });
      });

      try {
        const resp = await fetch(`/api/files/function-keys/${type}/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ keys: keysData })
        });
        const data = await resp.json();
        if (!data.success) {
          alert('保存失败: ' + (data.error || '未知错误'));
        }
      } catch (err) {
        console.error('保存功能键失败:', err);
        alert('保存失败');
      }
    },

    /**
     * 重新解析功能表
     */
    async reparseFunctionTable() {
      if (!this.currentModel) return;
      const { type, id } = this.currentModel;

      try {
        const resp = await fetch(`/api/files/reparse-function-table/${type}/${id}`, {
          method: 'POST'
        });
        const data = await resp.json();
        if (data.success) {
          this.renderFunctionKeyTable(data.keys);
          alert(`解析成功，共 ${data.count} 个功能键`);
        } else {
          alert('解析失败: ' + (data.error || '未知错误'));
        }
      } catch (err) {
        console.error('重新解析失败:', err);
        alert('重新解析失败');
      }
    },

    /**
     * 导出功能键为 Excel
     */
    exportFunctionKeys() {
      if (!this.currentModel) return;
      const { type, id } = this.currentModel;
      window.location.href = `/api/files/function-keys/${type}/${id}/export`;
    },

    /**
     * 渲染说明书列表
     * @param {Array} manuals - 说明书文件数组
     */
    renderManuals(manuals) {
      const container = document.getElementById('manual-list');
      const countSpan = document.getElementById('manual-count');

      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
      countSpan.textContent = `(${manuals ? manuals.length : 0})`;

      if (manuals && manuals.length > 0) {
        manuals.forEach(manual => {
          const fileItem = this.createFileItem(manual);
          container.appendChild(fileItem);
        });
      }
    },

    /**
     * 创建文件项元素
     * @param {Object} file - 文件信息
     * @returns {HTMLElement}
     */
    createFileItem(file) {
      const div = document.createElement('div');
      div.className = 'file-item';
      div.dataset.fileId = file.id;

      const name = document.createElement('span');
      name.className = 'file-name';
      const displayName = file.stored_filename || file.original_filename;
      name.textContent = displayName;
      name.title = displayName;  // hover 显示完整文件名

      const actions = document.createElement('div');
      actions.className = 'file-actions';

      const btnView = document.createElement('button');
      btnView.type = 'button';
      btnView.className = 'btn-icon btn-view';
      btnView.textContent = '○';
      btnView.title = '查看';
      btnView.onclick = () => window.open(`/api/files/view/${file.id}`, '_blank');

      const btnDownload = document.createElement('button');
      btnDownload.type = 'button';
      btnDownload.className = 'btn-icon btn-download';
      btnDownload.textContent = '↓';
      btnDownload.title = '下载';
      btnDownload.onclick = () => window.location.href = `/api/files/download/${file.id}`;

      const btnDelete = document.createElement('button');
      btnDelete.type = 'button';
      btnDelete.className = 'btn-icon btn-delete';
      btnDelete.textContent = '×';
      btnDelete.title = '删除';
      btnDelete.onclick = () => this.deleteFileById(file.id, div);

      actions.appendChild(btnView);
      actions.appendChild(btnDownload);
      actions.appendChild(btnDelete);

      div.appendChild(name);
      div.appendChild(actions);

      return div;
    },

    /**
     * 触发文件上传
     * @param {string} fileType - 文件类型 (image/manual/function_table)
     */
    triggerUpload(fileType) {
      const inputId = fileType === 'image' ? 'image-upload-input' :
        fileType === 'function_table' ? 'function-table-upload-input' :
          'manual-upload-input';

      const input = document.getElementById(inputId);
      if (input) {
        input.onchange = (e) => this.handleFileSelect(e, fileType);
        input.click();
      }
    },

    /**
     * 处理文件选择
     * @param {Event} e - 文件选择事件
     * @param {string} fileType - 文件类型
     */
    handleFileSelect(e, fileType) {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);
      formData.append('model_type', this.currentModel.type);
      formData.append('model_id', this.currentModel.id);
      formData.append('file_type', fileType);

      fetch('/api/files/upload', {
        method: 'POST',
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // 刷新模型详情
            this.showModelDetail(this.currentModel.type, this.currentModel.id);
          } else {
            alert('上传失败: ' + (data.error || '未知错误'));
          }
        })
        .catch(error => {
          console.error('上传失败:', error);
          alert('上传失败');
        })
        .finally(() => {
          // 清空文件输入
          e.target.value = '';
        });
    },

    /**
     * 预览文件
     * @param {string} fileType - 文件类型
     */
    viewFile(fileType) {
      const file = this.currentModel.files[fileType];
      if (file) {
        window.open(`/api/files/view/${file.id}`, '_blank');
      }
    },

    /**
     * 下载文件
     * @param {string} fileType - 文件类型 (image/function_table)
     */
    downloadFile(fileType) {
      const file = this.currentModel.files[fileType];
      if (file) {
        window.location.href = `/api/files/download/${file.id}`;
      }
    },

    /**
     * 删除文件
     * @param {string} fileType - 文件类型
     */
    deleteFile(fileType) {
      const file = this.currentModel.files[fileType];
      if (file) {
        this.deleteFileById(file.id);
      }
    },

    /**
     * 根据 ID 删除文件
     * @param {number} fileId - 文件ID
     * @param {HTMLElement} element - 可选，要移除的元素
     */
    deleteFileById(fileId, element) {
      if (!confirm('确定删除此文件？')) return;

      fetch(`/api/files/delete/${fileId}`, {
        method: 'DELETE'
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            if (element) {
              element.remove();
            }
            // 刷新模型详情
            this.showModelDetail(this.currentModel.type, this.currentModel.id);
          } else {
            alert('删除失败: ' + (data.error || '未知错误'));
          }
        })
        .catch(error => {
          console.error('删除失败:', error);
          alert('删除失败');
        });
    },

    /**
     * 格式化文件大小
     * @param {number} bytes - 文件大小（字节）
     * @returns {string}
     */
    formatFileSize(bytes) {
      if (!bytes) return '0 B';

      const units = ['B', 'KB', 'MB', 'GB'];
      let unitIndex = 0;
      let size = bytes;

      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }

      return size.toFixed(unitIndex > 0 ? 1 : 0) + ' ' + units[unitIndex];
    },

    /**
     * 加载表格中的文件状态
     * 在页面加载时调用，更新表格中每一行的文件状态显示
     */
    loadTableFileStatus() {
      const rows = document.querySelectorAll('tr[data-model_type][data-model_id]');

      rows.forEach(row => {
        const modelType = row.dataset.model_type;
        const modelId = row.dataset.model_id;

        fetch(`/api/files/list/${modelType}/${modelId}`)
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              this.updateRowFileStatus(row, data.files);
            }
          })
          .catch(error => console.error('获取文件状态失败:', error));
      });
    },

    /**
     * 更新行文件状态显示
     * @param {HTMLElement} row - 表格行
     * @param {Object} files - 文件信息
     */
    updateRowFileStatus(row, files) {
      // 更新图片
      const imageCell = row.querySelector('.image-cell');
      if (imageCell) {
        if (files.image) {
          // 使用安全的 DOM 方法创建图片元素
          while (imageCell.firstChild) {
            imageCell.removeChild(imageCell.firstChild);
          }
          const img = document.createElement('img');
          img.src = `/api/files/view/${files.image.id}`;
          img.className = 'thumbnail';
          img.title = '点击查看详情';
          // 校验 model_type/model_id 防止 onclick 字符串注入（保留 setAttribute 兼容 cloneNode 排序）
          const modelType = row.dataset.model_type;
          const modelId = parseInt(row.dataset.model_id, 10);
          if (['locomotive', 'carriage', 'trainset', 'locomotive_head'].includes(modelType) && Number.isInteger(modelId)) {
            img.setAttribute('onclick', `FileManager.showModelDetail('${modelType}', ${modelId})`);
          }
          imageCell.appendChild(img);
        }
      }

      // 更新功能表状态
      const functionTableCell = row.querySelector('.file-status-cell[data-file-type="function_table"]');
      if (functionTableCell) {
        const status = functionTableCell.querySelector('.file-status');
        if (files.function_table) {
          status.className = 'file-status file-status-exists';
          status.textContent = '✓'; // ✓
          status.title = '已上传，点击查看';
        }
      }

      // 更新说明书数量
      const manualCell = row.querySelector('.file-status-cell[data-file-type="manual"]');
      if (manualCell) {
        const status = manualCell.querySelector('.file-status');
        const count = files.manual ? files.manual.length : 0;
        status.textContent = count;
        if (count > 0) {
          status.className = 'file-status file-status-exists';
          status.title = count + '个文件，点击查看';
        }
      }
    }
  };

  /**
   * 初始化文件管理模态框
   */
  function initFileManagerModal() {
    const modal = document.getElementById('model-detail-modal');
    if (modal) {
      ModalManager.init('model-detail-modal', null);

      // 页面加载时获取表格中的文件状态
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          FileManager.loadTableFileStatus();
        });
      } else {
        FileManager.loadTableFileStatus();
      }
    }
  }

  global.FileManager = FileManager;
  global.initFileManagerModal = initFileManagerModal;

  // 自动初始化
  initFileManagerModal();
})(window);
