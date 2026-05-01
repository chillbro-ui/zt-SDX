// =========================================================================
// ZT-SDX Enterprise — UI Components
// Generators for Modals, Toasts, Badges, etc.
// =========================================================================

window.Components = {
  badge(text, colorClass = 'badge-muted') {
    return `<span class="badge ${colorClass}">${text}</span>`;
  }
};

// =========================================================================
// ZT-SDX Modal System — Replaces native alert/confirm/prompt
// =========================================================================
window.Modal = {

  _injectStyles() {
    if (document.getElementById('ztsdx-modal-styles')) return;
    const style = document.createElement('style');
    style.id = 'ztsdx-modal-styles';
    style.textContent = `
      .ztsdx-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.65);
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
        display: flex; align-items: center; justify-content: center;
        z-index: 9999;
        animation: modalFadeIn 0.2s ease;
      }
      .ztsdx-dialog {
        background: var(--bg-elevated);
        border: 1px solid var(--border-strong);
        border-radius: 16px;
        padding: 35px;
        max-width: 460px;
        width: 90%;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        animation: modalSlideUp 0.25s ease;
      }
      .ztsdx-dialog-icon {
        font-size: 2.8rem;
        margin-bottom: 16px;
        display: block;
      }
      .ztsdx-dialog-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 10px;
      }
      .ztsdx-dialog-message {
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.6;
        margin-bottom: 25px;
      }
      .ztsdx-dialog-input {
        width: 100%;
        background: var(--bg-surface-hover);
        border: 1px solid var(--border-strong);
        color: var(--text-primary);
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 0.95rem;
        margin-bottom: 20px;
        font-family: var(--font-sans);
        transition: border-color 0.2s;
      }
      .ztsdx-dialog-input:focus {
        outline: none;
        border-color: var(--ztsdx-cyan);
        box-shadow: 0 0 0 3px rgba(0,240,255,0.15);
      }
      .ztsdx-dialog-actions {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
      }
      .ztsdx-dialog-actions .btn {
        padding: 10px 22px;
        font-size: 0.95rem;
        border-radius: 8px;
        font-weight: 600;
      }
      @keyframes modalFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes modalSlideUp {
        from { opacity: 0; transform: translateY(20px) scale(0.97); }
        to { opacity: 1; transform: translateY(0) scale(1); }
      }
    `;
    document.head.appendChild(style);
  },

  _create(html) {
    this._injectStyles();
    const overlay = document.createElement('div');
    overlay.className = 'ztsdx-overlay';
    overlay.innerHTML = `<div class="ztsdx-dialog">${html}</div>`;
    document.body.appendChild(overlay);
    return overlay;
  },

  _destroy(overlay) {
    overlay.style.opacity = '0';
    setTimeout(() => overlay.remove(), 150);
  },

  /**
   * Custom alert — replaces window.alert()
   */
  alert(message, { title = 'Notice', icon = 'ℹ️', buttonText = 'OK' } = {}) {
    return new Promise(resolve => {
      const overlay = this._create(`
        <div class="ztsdx-dialog-icon">${icon}</div>
        <div class="ztsdx-dialog-title">${title}</div>
        <div class="ztsdx-dialog-message">${message}</div>
        <div class="ztsdx-dialog-actions">
          <button class="btn btn-primary" id="ztsdx-alert-ok">${buttonText}</button>
        </div>
      `);
      overlay.querySelector('#ztsdx-alert-ok').addEventListener('click', () => {
        this._destroy(overlay);
        resolve();
      });
      overlay.querySelector('#ztsdx-alert-ok').focus();
    });
  },

  /**
   * Custom confirm — replaces window.confirm()
   */
  confirm(message, { title = 'Confirm Action', icon = '⚠️', confirmText = 'Confirm', cancelText = 'Cancel', danger = false } = {}) {
    return new Promise(resolve => {
      const btnClass = danger ? 'btn btn-danger' : 'btn btn-primary';
      const overlay = this._create(`
        <div class="ztsdx-dialog-icon">${icon}</div>
        <div class="ztsdx-dialog-title">${title}</div>
        <div class="ztsdx-dialog-message">${message}</div>
        <div class="ztsdx-dialog-actions">
          <button class="btn btn-secondary" id="ztsdx-confirm-cancel">${cancelText}</button>
          <button class="${btnClass}" id="ztsdx-confirm-ok">${confirmText}</button>
        </div>
      `);
      overlay.querySelector('#ztsdx-confirm-ok').addEventListener('click', () => {
        this._destroy(overlay);
        resolve(true);
      });
      overlay.querySelector('#ztsdx-confirm-cancel').addEventListener('click', () => {
        this._destroy(overlay);
        resolve(false);
      });
    });
  },

  /**
   * Custom prompt — replaces window.prompt()
   */
  prompt(message, { title = 'Input Required', icon = '✏️', placeholder = '', defaultValue = '', confirmText = 'Submit', cancelText = 'Cancel' } = {}) {
    return new Promise(resolve => {
      const overlay = this._create(`
        <div class="ztsdx-dialog-icon">${icon}</div>
        <div class="ztsdx-dialog-title">${title}</div>
        <div class="ztsdx-dialog-message">${message}</div>
        <input class="ztsdx-dialog-input" id="ztsdx-prompt-input" placeholder="${placeholder}" value="${defaultValue}" autocomplete="off" />
        <div class="ztsdx-dialog-actions">
          <button class="btn btn-secondary" id="ztsdx-prompt-cancel">${cancelText}</button>
          <button class="btn btn-primary" id="ztsdx-prompt-ok">${confirmText}</button>
        </div>
      `);
      const input = overlay.querySelector('#ztsdx-prompt-input');
      input.focus();
      input.select();
      
      const submit = () => {
        const val = input.value;
        this._destroy(overlay);
        resolve(val || null);
      };
      
      overlay.querySelector('#ztsdx-prompt-ok').addEventListener('click', submit);
      input.addEventListener('keydown', e => { if (e.key === 'Enter') submit(); });
      overlay.querySelector('#ztsdx-prompt-cancel').addEventListener('click', () => {
        this._destroy(overlay);
        resolve(null);
      });
    });
  },

  /**
   * Success toast notification
   */
  success(message) {
    return this.alert(message, { title: 'Success', icon: '✅' });
  },

  /**
   * Error toast notification
   */
  error(message) {
    return this.alert(message, { title: 'Error', icon: '❌' });
  }
};
