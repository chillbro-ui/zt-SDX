window.Shares = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px;">
          <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Share Centre</h1>
          <p style="color: var(--text-secondary); margin-top: 5px;">Manage outgoing share links for your files.</p>
        </header>

        <div class="card" style="padding: 0; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
          <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead style="background: var(--bg-secondary); border-bottom: 1px solid var(--border-subtle);">
              <tr>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600;">File</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600;">Recipient</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600;">Expires</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600;">Downloads Left</th>
                <th style="padding: 16px 24px; text-align: right; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600;">Actions</th>
              </tr>
            </thead>
            <tbody id="shares-table-body">
              <tr><td colspan="5" style="padding: 40px; text-align: center; color: var(--text-muted);">⏳ Loading shares...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async afterRender() {
    const userStr = sessionStorage.getItem('current_user');
    const role = userStr ? JSON.parse(userStr).role : 'EMPLOYEE';
    const canRevoke = ['SUPER_ADMIN', 'SECURITY_ADMIN', 'DEPT_HEAD', 'MANAGER'].includes(role);

    try {
      const data = await window.api.getShares();
      const tbody = document.getElementById('shares-table-body');

      // Backend returns { shares: [...] } or array directly
      const shares = Array.isArray(data) ? data : (data.shares || []);

      if (shares.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="padding: 50px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 2.5rem; margin-bottom: 10px;">🔗</div>
          <div style="font-size: 1.05rem; color: var(--text-primary);">No share links yet</div>
          <div style="margin-top: 5px;">Go to the File Vault and click 🔗 on a file to create one.</div>
        </td></tr>`;
        return;
      }

      tbody.innerHTML = shares.map(share => {
        const expiry = share.expiry ? new Date(share.expiry) : null;
        const now    = new Date();
        const expired = expiry && expiry < now;
        const expiryStr = expiry ? expiry.toLocaleString() : '—';
        const expiryColor = expired ? '#ff4d4f' : (expiry && (expiry - now) < 3600000 * 6 ? '#faad14' : '#52c41a');

        return `
          <tr style="border-bottom: 1px solid var(--border-subtle); transition: background 0.2s;"
              onmouseover="this.style.background='var(--bg-secondary)'"
              onmouseout="this.style.background='transparent'">
            <td style="padding: 16px 24px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.4rem;">📄</span>
                <span style="font-weight: 600; color: var(--text-primary);">${share.file_id?.substring(0, 8)}...</span>
              </div>
            </td>
            <td style="padding: 16px 24px; color: var(--ztsdx-cyan);">${share.recipient || '—'}</td>
            <td style="padding: 16px 24px; color: ${expiryColor}; font-weight: 600;">${expired ? 'Expired' : expiryStr}</td>
            <td style="padding: 16px 24px; color: var(--text-secondary);">${share.downloads_left ?? '—'}</td>
            <td style="padding: 16px 24px; text-align: right;">
              ${canRevoke && !expired ? `
                <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.8rem;"
                  onclick="window.Shares.revoke('${share.id}')">Revoke</button>
              ` : `<span style="color: var(--text-muted); font-size: 0.85rem;">${expired ? 'Expired' : 'View Only'}</span>`}
            </td>
          </tr>
        `;
      }).join('');
    } catch (error) {
      console.error('Failed to load shares', error);
      document.getElementById('shares-table-body').innerHTML = `
        <tr><td colspan="5" style="padding: 40px; text-align: center; color: #ff4d4f;">
          ❌ Failed to load shares: ${error.message}
        </td></tr>`;
    }
  },

  async revoke(shareId) {
    const confirmed = await Modal.confirm(
      'Are you sure you want to revoke this share link? The recipient will immediately lose access.',
      { title: 'Revoke Share Link', icon: '🔗', confirmText: 'Revoke Access', danger: true }
    );
    if (!confirmed) return;

    try {
      await window.api.revokeShare(shareId);
      this.afterRender();
    } catch (error) {
      await Modal.error('Failed to revoke: ' + error.message);
    }
  }
};
