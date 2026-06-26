/**
 * 火车模型管理系统 - 下拉组件模块
 *
 * 提供：
 *   - LightDropdownManager：灯型号下拉组件（基于 API 加载）
 *   - AutocompleteManager：可搜索下拉框组件
 */
(function (global) {
  'use strict';

  // 灯型号下拉管理器
  const LightDropdownManager = {
    instances: {},

    /**
     * 初始化灯型号下拉组件
     * @param {Object} config
     *   - textInputId: 显示文本的input ID
     *   - hiddenInputId: 存储light_model_id的hidden input ID
     *   - scaleSource: function() 返回当前比例值
     *   - modelType: 'carriage' | 'trainset'（用于API）
     *   - modelIdSource: function() 返回当前车型ID
     *   - brandIdSource: function() 返回当前品牌ID
     */
    init(config) {
      const instance = { config, dropdown: null };
      this.instances[config.textInputId] = instance;

      const textInput = document.getElementById(config.textInputId);
      if (!textInput) return;

      // 创建下拉列表容器（挂到 body 避免 overflow 裁剪）
      const dropdown = document.createElement('div');
      dropdown.className = 'light-dropdown';
      dropdown.style.display = 'none';
      dropdown.style.position = 'fixed';
      dropdown.style.zIndex = '1100';
      dropdown.style.background = '#fff';
      dropdown.style.border = '1px solid #ccc';
      dropdown.style.borderRadius = '4px';
      dropdown.style.maxHeight = '200px';
      dropdown.style.overflowY = 'auto';
      dropdown.style.minWidth = '250px';
      dropdown.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
      document.body.appendChild(dropdown);
      instance.dropdown = dropdown;

      // 定位下拉菜单到输入框下方
      const positionDropdown = () => {
        if (dropdown.style.display === 'none') return;
        const rect = textInput.getBoundingClientRect();
        dropdown.style.top = (rect.bottom + 2) + 'px';
        dropdown.style.left = rect.left + 'px';
      };

      // 点击文本框时显示下拉
      textInput.addEventListener('focus', () => {
        this.refresh(config.textInputId);
        // refresh 完成后会调用 showDropdown 触发定位
      });

      // 点击外部关闭
      document.addEventListener('click', (e) => {
        if (e.target !== textInput && !dropdown.contains(e.target)) {
          dropdown.style.display = 'none';
        }
      });

      // 滚动时关闭下拉（防止位置错乱）
      const scrollParent = textInput.closest('.carriage-items-container');
      if (scrollParent) {
        scrollParent.addEventListener('scroll', () => { dropdown.style.display = 'none'; });
      }
      // 保存引用以便后续定位
      instance.positionDropdown = positionDropdown;

      // 监听关联字段变化
      document.addEventListener('change', (e) => {
        const target = e.target;
        const shouldRefresh = (
          (target.id === 'model_id' || target.name?.startsWith('model_')) ||
          target.id === 'brand_id' || target.id === 'scale'
        );
        if (shouldRefresh && instance) {
          this.refresh(config.textInputId);
        }
      });
    },

    /**
     * 从API加载兼容灯型号并刷新下拉列表
     * @param {string} instanceId - 实例ID（textInputId）
     */
    async refresh(instanceId) {
      const instance = this.instances[instanceId];
      if (!instance) return;

      const { config, dropdown } = instance;
      const scale = config.scaleSource();
      const modelId = config.modelIdSource();
      const brandId = config.brandIdSource();
      const brandOnly = config.modelType === 'brand_only';

      if ((!brandOnly && !modelId) || !brandId) {
        dropdown.textContent = '';
        const hint = document.createElement('div');
        hint.style.padding = '8px';
        hint.style.color = '#999';
        hint.textContent = brandOnly ? '请先选择品牌' : '请先选择型号和品牌';
        dropdown.appendChild(hint);
        dropdown.style.display = 'block';
        if (instance.positionDropdown) instance.positionDropdown();
        return;
      }

      dropdown.textContent = '';
      const loading = document.createElement('div');
      loading.style.padding = '8px';
      loading.style.color = '#999';
      loading.textContent = '加载中...';
      dropdown.appendChild(loading);
      dropdown.style.display = 'block';
      if (instance.positionDropdown) instance.positionDropdown();

      try {
        const params = new URLSearchParams({
          model_type: config.modelType,
          brand_id: brandId
        });
        if (!brandOnly && modelId) params.set('model_id', modelId);
        if (scale) params.set('scale', scale);

        const response = await fetch(`/api/light-models/compatible?${params}`);
        const data = await response.json();

        if (data.success && data.groups) {
          this.renderDropdown(instanceId, data.groups, data.unfiltered);
        } else {
          dropdown.textContent = '';
          const noResult = document.createElement('div');
          noResult.style.padding = '8px';
          noResult.style.color = '#999';
          noResult.textContent = '无可用灯型号';
          dropdown.appendChild(noResult);
        }
      } catch (err) {
        dropdown.textContent = '';
        const errorEl = document.createElement('div');
        errorEl.style.padding = '8px';
        errorEl.style.color = '#f00';
        errorEl.textContent = '加载失败';
        dropdown.appendChild(errorEl);
      }
    },

    /**
     * 渲染下拉选项
     * @param {string} instanceId - 实例ID
     * @param {Array} groups - 按灯品牌分组的灯型号列表
     */
    renderDropdown(instanceId, groups, unfiltered) {
      const instance = this.instances[instanceId];
      if (!instance) return;

      const { config, dropdown } = instance;
      const hiddenInput = document.getElementById(config.hiddenInputId);
      const currentId = hiddenInput?.value;

      dropdown.textContent = '';

      if (groups.length === 0) {
        const noResult = document.createElement('div');
        noResult.style.padding = '8px';
        noResult.style.color = '#999';
        noResult.textContent = '无可用灯型号';
        dropdown.appendChild(noResult);
        dropdown.style.display = 'block';
        if (instance.positionDropdown) instance.positionDropdown();
        return;
      }

      // 未配置适用关系时显示提示
      if (unfiltered) {
        const hint = document.createElement('div');
        hint.style.padding = '6px 8px';
        hint.style.background = '#fff3cd';
        hint.style.color = '#856404';
        hint.style.fontSize = '0.75rem';
        hint.style.borderBottom = '1px solid #ffc107';
        hint.textContent = '提示：未配置适用车型，请在信息维护中编辑灯型号设置';
        dropdown.appendChild(hint);
      }

      groups.forEach(group => {
        // 灯品牌标题
        const header = document.createElement('div');
        header.style.padding = '4px 8px';
        header.style.fontWeight = 'bold';
        header.style.background = '#f5f5f5';
        header.style.borderBottom = '1px solid #eee';
        header.textContent = group.light_brand_name;
        dropdown.appendChild(header);

        group.models.forEach(lm => {
          const item = document.createElement('div');
          item.style.padding = '6px 12px';
          item.style.cursor = 'pointer';
          item.style.borderBottom = '1px solid #f0f0f0';
          if (String(lm.id) === currentId) {
            item.style.backgroundColor = '#e3f2fd';
          }
          const displayText = lm.name + ' (' + lm.color_temperature + ', ' + (lm.scale || 'HO') + ')';
          item.textContent = displayText;

          item.addEventListener('mouseenter', () => { item.style.backgroundColor = '#f0f0f0'; });
          item.addEventListener('mouseleave', () => {
            item.style.backgroundColor = String(lm.id) === currentId ? '#e3f2fd' : '';
          });
          item.addEventListener('click', () => {
            this.handleSelect(instanceId, lm.id, displayText);
          });

          dropdown.appendChild(item);
        });
      });
      // 定位到输入框下方
      dropdown.style.display = 'block';
      if (instance.positionDropdown) instance.positionDropdown();
    },

    /**
     * 处理选择
     * @param {string} instanceId - 实例ID
     * @param {number} lightModelId - 灯型号ID
     * @param {string} displayName - 显示文本
     */
    handleSelect(instanceId, lightModelId, displayName) {
      const instance = this.instances[instanceId];
      if (!instance) return;

      const { config, dropdown } = instance;
      const textInput = document.getElementById(config.textInputId);
      const hiddenInput = document.getElementById(config.hiddenInputId);

      if (textInput) textInput.value = displayName;
      if (hiddenInput) hiddenInput.value = lightModelId;
      dropdown.style.display = 'none';
    }
  };

  // 可搜索下拉框管理器
  const AutocompleteManager = {
    // 存储所有自动完成的实例
    instances: {},

    /**
     * 初始化自动完成组件
     * @param {string} inputId - 输入框ID
     * @param {string} hiddenId - 隐藏域ID（存储实际值）
     * @param {Array} options - 选项数组 [{id, name}]
     * @param {Object} config - 配置项 { onchange }
     */
    init(inputId, hiddenId, options, config = {}) {
      const input = document.getElementById(inputId);
      const hidden = document.getElementById(hiddenId);
      const wrapper = input?.closest('.autocomplete-wrapper');

      if (!input || !hidden) return;

      const instance = {
        input,
        hidden,
        wrapper,
        options: options || [],
        config,
        selectedIndex: -1,
        filteredOptions: []
      };

      this.instances[inputId] = instance;

      // 创建下拉列表
      let dropdown = wrapper?.querySelector('.autocomplete-dropdown');
      if (!dropdown && wrapper) {
        dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        wrapper.appendChild(dropdown);
      }
      instance.dropdown = dropdown;

      // 创建提示文字
      let hint = wrapper?.querySelector('.autocomplete-hint');
      if (!hint && wrapper) {
        hint = document.createElement('div');
        hint.className = 'autocomplete-hint';
        hint.textContent = '该选项不存在，请先到信息维护页面添加';
        wrapper.appendChild(hint);
      }
      instance.hint = hint;

      // 绑定事件
      this.bindEvents(instance);
    },

    /**
     * 绑定事件
     */
    bindEvents(instance) {
      const { input, hidden, dropdown, wrapper, config } = instance;

      // 输入事件
      input.addEventListener('input', (e) => {
        this.handleInput(instance, e.target.value);
      });

      // 聚焦事件
      input.addEventListener('focus', (e) => {
        if (e.target.value) {
          this.handleInput(instance, e.target.value);
        } else {
          this.showAllOptions(instance);
        }
      });

      // 失焦事件（延迟处理，让点击事件先执行）
      input.addEventListener('blur', () => {
        setTimeout(() => {
          this.handleBlur(instance);
        }, 200);
      });

      // 键盘事件
      input.addEventListener('keydown', (e) => {
        this.handleKeydown(instance, e);
      });
    },

    /**
     * 处理输入
     */
    handleInput(instance, value) {
      const { options, dropdown } = instance;
      instance.selectedIndex = -1;

      if (!value) {
        this.showAllOptions(instance);
        return;
      }

      // 过滤选项
      const lowerValue = value.toLowerCase();
      instance.filteredOptions = options.filter(opt =>
        opt.name.toLowerCase().includes(lowerValue)
      );

      // 渲染下拉列表
      this.renderDropdown(instance, value);

      if (instance.filteredOptions.length > 0) {
        dropdown.classList.add('show');
      } else {
        dropdown.classList.remove('show');
      }
    },

    /**
     * 显示所有选项
     */
    showAllOptions(instance) {
      const { options, dropdown } = instance;
      instance.filteredOptions = options;
      instance.selectedIndex = -1;

      this.renderDropdown(instance, '');
      dropdown.classList.add('show');
    },

    /**
     * 渲染下拉列表（使用安全的 DOM 方法）
     */
    renderDropdown(instance, searchValue) {
      const { dropdown, filteredOptions } = instance;

      // 清空下拉列表
      while (dropdown.firstChild) {
        dropdown.removeChild(dropdown.firstChild);
      }

      if (filteredOptions.length === 0) {
        const noMatch = document.createElement('div');
        noMatch.className = 'autocomplete-option no-match';
        noMatch.textContent = '无匹配选项';
        dropdown.appendChild(noMatch);
        return;
      }

      const lowerSearch = searchValue.toLowerCase();
      filteredOptions.forEach((opt, index) => {
        const optionEl = document.createElement('div');
        optionEl.className = 'autocomplete-option';
        optionEl.dataset.index = index;
        optionEl.dataset.id = opt.id;
        optionEl.dataset.name = opt.name;

        // 高亮匹配部分
        if (searchValue) {
          const displayName = opt.name;
          const pos = displayName.toLowerCase().indexOf(lowerSearch);
          if (pos !== -1) {
            const before = document.createTextNode(displayName.substring(0, pos));
            const highlight = document.createElement('span');
            highlight.className = 'highlight';
            highlight.textContent = displayName.substring(pos, pos + searchValue.length);
            const after = document.createTextNode(displayName.substring(pos + searchValue.length));
            optionEl.appendChild(before);
            optionEl.appendChild(highlight);
            optionEl.appendChild(after);
          } else {
            optionEl.textContent = displayName;
          }
        } else {
          optionEl.textContent = opt.name;
        }

        // 点击事件
        optionEl.addEventListener('click', () => {
          this.selectOption(instance, opt.id, opt.name);
        });

        dropdown.appendChild(optionEl);
      });
    },

    /**
     * 选择选项
     */
    selectOption(instance, id, name) {
      const { input, hidden, dropdown, wrapper, config } = instance;

      input.value = name;
      hidden.value = id;
      dropdown.classList.remove('show');
      wrapper?.classList.remove('no-match');

      // 触发回调
      if (config.onchange && typeof config.onchange === 'function') {
        config.onchange(id, name);
      }

      // 触发原生 change 事件
      const event = new Event('change', { bubbles: true });
      hidden.dispatchEvent(event);
    },

    /**
     * 处理失焦
     */
    handleBlur(instance) {
      const { input, hidden, wrapper, options, config } = instance;
      instance.dropdown.classList.remove('show');

      const value = input.value.trim();

      if (!value) {
        hidden.value = '';
        wrapper?.classList.remove('no-match');
        return;
      }

      // 检查输入值是否在选项中
      const matchedOption = options.find(opt =>
        opt.name.toLowerCase() === value.toLowerCase()
      );

      if (matchedOption) {
        hidden.value = matchedOption.id;
        input.value = matchedOption.name; // 使用标准化的名称
        wrapper?.classList.remove('no-match');
      } else {
        hidden.value = '';
        wrapper?.classList.add('no-match');
      }
    },

    /**
     * 处理键盘事件
     */
    handleKeydown(instance, e) {
      const { dropdown, filteredOptions, selectedIndex } = instance;

      if (!dropdown.classList.contains('show')) return;

      const options = dropdown.querySelectorAll('.autocomplete-option:not(.no-match)');

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          instance.selectedIndex = Math.min(selectedIndex + 1, options.length - 1);
          this.updateSelection(instance, options);
          break;

        case 'ArrowUp':
          e.preventDefault();
          instance.selectedIndex = Math.max(selectedIndex - 1, 0);
          this.updateSelection(instance, options);
          break;

        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0 && options[selectedIndex]) {
            const opt = options[selectedIndex];
            this.selectOption(instance, opt.dataset.id, opt.dataset.name);
          }
          break;

        case 'Escape':
          dropdown.classList.remove('show');
          break;
      }
    },

    /**
     * 更新选中状态
     */
    updateSelection(instance, options) {
      options.forEach((opt, i) => {
        opt.classList.toggle('selected', i === instance.selectedIndex);
      });

      // 滚动到可见
      if (instance.selectedIndex >= 0 && options[instance.selectedIndex]) {
        options[instance.selectedIndex].scrollIntoView({ block: 'nearest' });
      }
    },

    /**
     * 设置选项（用于动态更新）
     */
    setOptions(inputId, options) {
      const instance = this.instances[inputId];
      if (instance) {
        instance.options = options || [];
      }
    },

    /**
     * 获取当前值
     */
    getValue(inputId) {
      const instance = this.instances[inputId];
      if (instance) {
        return {
          id: instance.hidden.value,
          name: instance.input.value
        };
      }
      return null;
    },

    /**
     * 设置当前值
     */
    setValue(inputId, id, name) {
      const instance = this.instances[inputId];
      if (instance) {
        instance.hidden.value = id;
        instance.input.value = name;
        instance.wrapper?.classList.remove('no-match');
      }
    }
  };

  global.LightDropdownManager = LightDropdownManager;
  global.AutocompleteManager = AutocompleteManager;
})(window);
