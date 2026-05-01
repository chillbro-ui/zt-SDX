window.AdminOrg = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px;">
          <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Organization Settings</h1>
          <p style="color: var(--text-secondary); margin-top: 5px;">Manage enterprise tenant configuration and defaults.</p>
        </header>
        <div class="card" style="padding: 40px; max-width: 600px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
            <div class="form-group" style="margin-bottom: 24px;">
                <label style="color: var(--text-secondary); display: block; margin-bottom: 8px; font-weight: 600;">Organization ID</label>
                <input type="text" class="input" value="org-uuid-592f8a1" disabled style="width: 100%; padding: 12px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-strong); color: var(--text-muted); font-family: monospace;">
            </div>
            <div class="form-group" style="margin-bottom: 24px;">
                <label style="color: var(--text-secondary); display: block; margin-bottom: 8px; font-weight: 600;">Organization Name</label>
                <input type="text" class="input" value="Acme Corp" style="width: 100%; padding: 12px; background: var(--bg-elevated); border: 1px solid var(--border-strong); color: var(--text-primary);">
            </div>
            <div class="form-group" style="margin-bottom: 32px;">
                <label style="color: var(--text-secondary); display: block; margin-bottom: 8px; font-weight: 600;">Primary Domain</label>
                <input type="text" class="input" value="acme.com" style="width: 100%; padding: 12px; background: var(--bg-elevated); border: 1px solid var(--border-strong); color: var(--text-primary);">
            </div>
            <div id="org-save-msg" style="color: #52c41a; background: rgba(82,196,26,0.1); padding: 12px; border-radius: 6px; margin-bottom: 20px; display: none; font-size: 0.95rem; border: 1px solid rgba(82,196,26,0.3);"><span style="margin-right:8px;">✓</span> Organization settings updated successfully!</div>
            <button class="btn btn-primary" style="padding: 14px 30px; font-weight: bold; font-size: 1.05rem;" onclick="window.AdminOrg.saveSettings()">Save Configuration</button>
        </div>
      </div>
    `;
  },
  
  saveSettings() {
      const msg = document.getElementById('org-save-msg');
      msg.style.display = 'block';
      setTimeout(() => {
          msg.style.display = 'none';
      }, 3000);
  }
};
