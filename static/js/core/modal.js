/**
 * 火车模型管理系统 - 模态框管理模块
 *
 * 提供 ModalManager，负责模态框的打开/关闭/ESC 关闭/初始化。
 * FormHelper 依赖本模块的 close；FormFiller 依赖 open；initFileManagerModal 依赖 init。
 */
(function (global) {
  'use strict';

  // 模态框管理器
  const ModalManager = {
    _escHandlers: {},

    /**
     * 打开模态框
     * @param {string} modalId - 模态框元素ID
     */
    open(modalId) {
      const modal = document.getElementById(modalId);
      if (!modal) return;

      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';

      // 重置表单
      const form = modal.querySelector('form');
      if (form) {
        form.reset();
        FormHelper.clearErrors(form);
        FormHelper.clearErrorSummary(form);
      }
    },

    /**
     * 关闭模态框
     * @param {string} modalId - 模态框元素ID
     */
    close(modalId) {
      const modal = document.getElementById(modalId);
      if (!modal) return;

      modal.style.display = 'none';
      document.body.style.overflow = '';
    },

    /**
     * 初始化模态框事件
     * @param {string} modalId - 模态框元素ID
     * @param {string} openBtnId - 打开按钮元素ID
     */
    init(modalId, openBtnId) {
      const modal = document.getElementById(modalId);
      const openBtn = document.getElementById(openBtnId);

      if (!modal) return;

      // 打开按钮点击事件
      if (openBtn) {
        openBtn.addEventListener('click', () => this.open(modalId));
      }

      // 关闭按钮点击事件
      const closeBtn = modal.querySelector('.modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.close(modalId));
      }

      // 点击遮罩关闭
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.close(modalId);
        }
      });

      // ESC 键关闭（避免重复注册）
      if (!this._escHandlers[modalId]) {
        const handler = (e) => {
          if (e.key === 'Escape' && modal.style.display === 'flex') {
            this.close(modalId);
          }
        };
        document.addEventListener('keydown', handler);
        this._escHandlers[modalId] = handler;
      }
    }
  };

  global.ModalManager = ModalManager;
})(window);
