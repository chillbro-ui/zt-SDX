window.Files = {
  render() {
    return `
      <div class="files-page fade-in">
        <header style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">File Vault</h1>
            <p style="color: var(--text-secondary); font-size: 1.05rem; margin-top: 5px;">Securely manage and share your sensitive documents.</p>
          </div>
          <button class="btn btn-primary" onclick="window.location.hash='#upload'" style="display: flex; align-items: center; gap: 8px;">
            📤 Upload New File
          </button>
        </header>

        <div class="card" style="padding: 0; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
          <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead style="background: var(--bg-secondary); border-bottom: 1px solid var(--border-subtle);">
              <tr>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">Document</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">Classification</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">Status</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">Size</th>
                <th style="padding: 16px 24px; text-align: right; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">Actions</th>
              </tr>
            </thead>
            <tbody id="files-table-body">
              <tr><td colspan="5" style="padding: 60px; text-align: center; color: var(--text-muted);">
                <div style="font-size: 2rem; margin-bottom: 10px;">⏳</div>
                <div>Decrypting secure vault...</div>
              </td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async afterRender() {
    try {
      const data = await window.api.getFiles();
      const tbody = document.getElementById('files-table-body');
      
      if (!data || !data.files || data.files.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="padding: 60px; text-align: center; color: var(--text-muted);">
            <div style="font-size: 3rem; margin-bottom: 10px;">📭</div>
            <div style="font-size: 1.1rem; color: var(--text-primary);">Your vault is empty</div>
            <div style="margin-top: 5px;">Upload a file to get started.</div>
        </td></tr>`;
        return;
      }

      const userStr = sessionStorage.getItem('current_user');
      const role = userStr ? JSON.parse(userStr).role : 'EMPLOYEE';
      const isAdmin = ['SUPER_ADMIN', 'SECURITY_ADMIN'].includes(role);
      const canDelete = ['SUPER_ADMIN', 'SECURITY_ADMIN'].includes(role);

      let html = '';
      data.files.forEach(file => {
        // Status Badge Logic
        let statusBadge = `<span style="padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; background: rgba(82, 196, 26, 0.15); color: #52c41a; font-weight: 600; border: 1px solid rgba(82, 196, 26, 0.3); white-space: nowrap;">ACTIVE</span>`;
        if (file.status === 'QUARANTINED') {
            statusBadge = `<span style="padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; background: rgba(255, 77, 79, 0.15); color: #ff4d4f; font-weight: 600; border: 1px solid rgba(255, 77, 79, 0.3); white-space: nowrap;">QUARANTINED</span>`;
        } else if (file.status === 'SCANNING') {
            statusBadge = `<span style="padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; background: rgba(250, 173, 20, 0.15); color: #faad14; font-weight: 600; border: 1px solid rgba(250, 173, 20, 0.3); white-space: nowrap;">SCANNING</span>`;
        } else if (file.status === 'BLOCKED') {
            statusBadge = `<span style="padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; background: rgba(255, 77, 79, 0.15); color: #ff4d4f; font-weight: 600; border: 1px solid rgba(255, 77, 79, 0.3); white-space: nowrap;">BLOCKED</span>`;
        } else if (file.status === 'PENDING_APPROVAL') {
            statusBadge = `<span style="padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; background: rgba(0, 240, 255, 0.15); color: var(--ztsdx-cyan); font-weight: 700; border: 1px solid rgba(0, 240, 255, 0.5); white-space: nowrap; box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);"><span style="animation: pulse 1.5s infinite; display: inline-block; margin-right: 4px;">⏳</span> PENDING REVIEW</span>`;
        }

        // Sensitivity Badge Logic
        let sensColor = 'var(--text-secondary)';
        let sensLabel = file.sensitivity || 'INTERNAL';
        if (sensLabel === 'RESTRICTED') sensColor = '#ff4d4f';
        else if (sensLabel === 'CONFIDENTIAL') sensColor = '#faad14';
        
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        const dateStr = file.created_at ? new Date(file.created_at).toLocaleDateString() : 'Just now';

        html += `
          <tr style="border-bottom: 1px solid var(--border-subtle); transition: background 0.2s;" onmouseover="this.style.background='var(--bg-secondary)'" onmouseout="this.style.background='transparent'">
            <td style="padding: 16px 24px; display: flex; align-items: center; gap: 15px; max-width: 350px;">
                <span style="font-size: 1.8rem;">📄</span>
                <div style="min-width: 0;">
                    <div style="font-weight: 600; color: var(--text-primary); font-size: 1.05rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${file.filename}">${file.filename}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Added ${dateStr}</div>
                </div>
            </td>
            <td style="padding: 16px 24px;">
                <div style="color: ${sensColor}; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
                    ${sensLabel === 'RESTRICTED' ? '🚨' : (sensLabel === 'CONFIDENTIAL' ? '⚠️' : 'ℹ️')}
                    ${sensLabel}
                </div>
            </td>
            <td style="padding: 16px 24px;">${statusBadge}</td>
            <td style="padding: 16px 24px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;">${sizeMb}</td>
            <td style="padding: 16px 24px; text-align: right; display: flex; justify-content: flex-end; gap: 8px;">
                ${(file.status === 'PENDING_APPROVAL' && isAdmin) ? `
                    <button class="btn btn-secondary" onclick="window.Files.setStatus('${file.id}', 'ACTIVE')" title="Approve File" style="color: #52c41a; font-size: 0.85rem; padding: 6px 12px;">✅ Approve</button>
                    <button class="btn btn-secondary" onclick="window.Files.setStatus('${file.id}', 'BLOCKED')" title="Reject File" style="color: #ff4d4f; font-size: 0.85rem; padding: 6px 12px;">❌ Reject</button>
                ` : ''}
                ${file.status === 'ACTIVE' ? `<button class="btn btn-ghost" onclick="window.Files.download('${file.id}')" title="Download secure copy">⬇️</button>` : ''}
                ${file.status === 'ACTIVE' ? `<button class="btn btn-ghost" onclick="window.Files.shareFile('${file.id}')" title="Create share link">🔗</button>` : ''}
                ${canDelete ? `<button class="btn btn-ghost" onclick="window.Files.deleteFile('${file.id}')" title="Delete from vault" style="color: #ff4d4f;">🗑️</button>` : ''}
            </td>
          </tr>
        `;
      });
      
      tbody.innerHTML = html;
    } catch (error) {
        console.error("Failed to load files", error);
        document.getElementById('files-table-body').innerHTML = `<tr><td colspan="5" style="padding: 40px; text-align: center; color: #ff4d4f; font-weight: 500;">❌ Failed to load vault data. Please try refreshing.</td></tr>`;
    }
  },

  async setStatus(fileId, status) {
      try {
          await window.api.updateFileStatus(fileId, status);
          this.afterRender();
      } catch (error) {
          await Modal.error('Failed to update status: ' + error.message);
      }
  },

  async download(fileId) {
      try {
          const data = await window.api.getFileDownloadUrl(fileId);
          if (data && data.download_url) {
              window.open(data.download_url, '_blank');
          } else {
              await Modal.alert('Could not retrieve download link. File might be blocked by policy.', { title: 'Download Blocked', icon: '🔒' });
          }
      } catch (error) {
          await Modal.error('Download blocked: ' + error.message);
      }
  },

  async deleteFile(fileId) {
      const confirmed = await Modal.confirm(
          'Are you sure you want to permanently delete this file from the vault? This action cannot be undone and will be logged in the audit ledger.',
          { title: 'Delete File', icon: '🗑️', confirmText: 'Delete Permanently', danger: true }
      );
      if (!confirmed) return;
      
      try {
          await window.api.deleteFile(fileId);
          this.afterRender();
      } catch (error) {
          await Modal.error('Delete failed: ' + error.message);
      }
  },

  async shareFile(fileId) {
      const email = await Modal.prompt('Enter the recipient email address to generate a secure, time-limited share token.', {
          title: 'Create Share Link', icon: '🔗', placeholder: 'e.g. vendor@external.com', confirmText: 'Next'
      });
      if (!email) return;
      
      const hours = await Modal.prompt('How many hours should this link remain active?', {
          title: 'Set Expiry Window', icon: '⏳', placeholder: 'Hours', defaultValue: '24', confirmText: 'Create Link'
      });
      
      try {
          await window.api.request('/shares', {
              method: 'POST',
              body: JSON.stringify({ file_id: fileId, recipient_email: email, expires_hours: parseInt(hours) || 24 })
          });
          await Modal.success('Share link created successfully! View it in the Share Centre.');
      } catch (error) {
          await Modal.error('Failed to create share: ' + error.message);
      }
  }
};

// Auto-refresh the view when mock background jobs complete
window.addEventListener('mock-files-updated', () => {
    if (window.location.hash === '#files') {
        window.Files.afterRender();
    }
});
