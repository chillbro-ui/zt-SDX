window.Audit = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Immutable Audit Ledger</h1>
            <p style="color: var(--text-secondary); margin-top: 5px;">Cryptographically verified chain of all system events.</p>
          </div>
          <button class="btn btn-primary" onclick="window.Audit.verifyChain()">🔗 Verify Chain Integrity</button>
        </header>

        <div id="chain-status" style="display:none; margin-bottom: 20px;"></div>

        <div class="card" style="padding: 0; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
          <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
            <thead style="background: var(--bg-secondary); border-bottom: 1px solid var(--border-subtle);">
              <tr>
                <th style="padding: 14px 20px; color: var(--text-secondary); text-transform: uppercase; font-size: 0.8rem;">Timestamp</th>
                <th style="padding: 14px 20px; color: var(--text-secondary); text-transform: uppercase; font-size: 0.8rem;">Action</th>
                <th style="padding: 14px 20px; color: var(--text-secondary); text-transform: uppercase; font-size: 0.8rem;">Actor</th>
                <th style="padding: 14px 20px; color: var(--text-secondary); text-transform: uppercase; font-size: 0.8rem;">Resource</th>
                <th style="padding: 14px 20px; color: var(--text-secondary); text-transform: uppercase; font-size: 0.8rem;">Result</th>
                <th style="padding: 14px 20px; color: var(--text-secondary); text-transform: uppercase; font-size: 0.8rem;">Hash</th>
              </tr>
            </thead>
            <tbody id="audit-table-body">
              <tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-muted);">⏳ Loading audit ledger...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async afterRender() {
    try {
      const data = await window.api.getAuditEvents(100);
      const tbody = document.getElementById('audit-table-body');

      // Backend returns array directly
      const logs = Array.isArray(data) ? data : (data.logs || data.events || []);

      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 2rem; margin-bottom: 8px;">📭</div>
          No audit events recorded yet.
        </td></tr>`;
        return;
      }

      tbody.innerHTML = logs.map(log => {
        const time = log.created_at ? new Date(log.created_at).toLocaleString() : '—';
        const hash = log.hash ? log.hash.substring(0, 16) + '...' : '—';
        const resultColor = log.result === 'SUCCESS' ? '#52c41a' : (log.result === 'FAILURE' ? '#ff4d4f' : 'var(--text-secondary)');
        const actor = log.actor ? (log.actor.length > 20 ? log.actor.substring(0, 8) + '...' : log.actor) : '—';
        const resource = log.resource ? (log.resource.length > 20 ? log.resource.substring(0, 16) + '...' : log.resource) : '—';

        return `
          <tr style="border-bottom: 1px solid var(--border-subtle); transition: background 0.15s;"
              onmouseover="this.style.background='var(--bg-secondary)'"
              onmouseout="this.style.background='transparent'">
            <td style="padding: 12px 20px; color: var(--text-muted); white-space: nowrap;">${time}</td>
            <td style="padding: 12px 20px; color: var(--text-primary); font-weight: 600;">${log.action || '—'}</td>
            <td style="padding: 12px 20px; color: var(--ztsdx-cyan);" title="${log.actor || ''}">${actor}</td>
            <td style="padding: 12px 20px; color: var(--text-secondary);" title="${log.resource || ''}">${resource}</td>
            <td style="padding: 12px 20px; color: ${resultColor}; font-weight: 600;">${log.result || '—'}</td>
            <td style="padding: 12px 20px; color: #52c41a;" title="${log.hash || ''}">${hash}</td>
          </tr>
        `;
      }).join('');
    } catch (error) {
      console.error('Failed to load audit logs', error);
      document.getElementById('audit-table-body').innerHTML = `
        <tr><td colspan="6" style="padding: 40px; text-align: center; color: #ff4d4f;">
          ❌ Failed to load audit ledger: ${error.message}
        </td></tr>`;
    }
  },

  async verifyChain() {
    const statusDiv = document.getElementById('chain-status');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = `<div class="card" style="padding: 16px; border-left: 4px solid var(--ztsdx-cyan);">⏳ Verifying chain integrity...</div>`;

    try {
      const result = await window.api.verifyAudit();
      const valid = result.valid;
      const color = valid ? '#52c41a' : '#ff4d4f';
      const icon  = valid ? '✅' : '❌';

      statusDiv.innerHTML = `
        <div class="card" style="padding: 16px; border-left: 4px solid ${color}; background: rgba(${valid ? '82,196,26' : '255,77,79'},0.05);">
          <strong style="color: ${color};">${icon} Chain ${valid ? 'VALID' : 'COMPROMISED'}</strong>
          &nbsp;·&nbsp; ${result.total_logs} logs verified
          ${result.error ? `<div style="color: #ff4d4f; margin-top: 8px; font-size: 0.9rem;">Error: ${result.error}</div>` : ''}
        </div>
      `;
    } catch (error) {
      statusDiv.innerHTML = `<div class="card" style="padding: 16px; border-left: 4px solid #ff4d4f;">❌ Verification failed: ${error.message}</div>`;
    }
  }
};
