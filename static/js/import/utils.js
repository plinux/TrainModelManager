/**
 * 火车模型管理系统 - 自定义导入向导 - 辅助函数
 *
 * 通用辅助函数：消息提示、加载遮罩、容器清空、日期格式化、系统表加载与查询、模板保存模式处理。
 *
 * 依赖（按加载顺序）：wizard_core.js -> utils.js -> file_step.js -> mapping_step.js -> preview_step.js
 * 所有模块通过共享的 window.CustomImportWizard 对象（别名 W）通信。
 */

(function (global) {
  'use strict';

  /** 共享向导对象（由 wizard_core.js 初始化） */
  let W = global.CustomImportWizard;

  W.clearContainer = function(container) {
    while (container && container.firstChild) {
      container.removeChild(container.firstChild);
    }
  
  };

  W.showMessage = function(message, isError) {
    // 使用简单的 alert，可以后续替换为更友好的提示
    if (isError) {
      alert('错误: ' + message);
    } else {
      alert(message);
    }
  
  };

  W.showLoading = function(message) {
    // 可以后续实现加载动画
    console.log('Loading:', message);
  
  };

  W.hideLoading = function() {
    console.log('Loading complete');
  
  };

  W.formatDate = function(isoDate) {
    if (!isoDate) return '';
    const date = new Date(isoDate);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  
  };

  W.getTableDisplayName = function(tableName) {
    const table = CustomImportWizard.systemTables.find(function(t) {
      return t.name === tableName;
    });
    return table ? table.display_name : tableName;
  
  };

  W.loadSystemTables = function() {
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
  
  };

  W.handleSaveTemplateModeChange = function() {
    const els = CustomImportWizard.elements;
    const selectedMode = W.getSaveTemplateMode();

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
      W.populateUpdateTemplateSelect();
    }
  
  };

  W.getSaveTemplateMode = function() {
    const els = CustomImportWizard.elements;
    let mode = 'none';
    els.saveTemplateModeRadios.forEach(function(radio) {
      if (radio.checked) {
        mode = radio.value;
      }
    });
    return mode;
  
  };

  W.populateUpdateTemplateSelect = function() {
    const select = CustomImportWizard.elements.updateTemplateSelect;
    if (!select) return;

    // 清空选项
    W.clearContainer(select);

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
  
  };

  W.getSystemTableConfig = function(tableName) {
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
  
  };

})(this);
