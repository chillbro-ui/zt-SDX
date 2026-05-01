window.AdminUsers = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">IAM & Employees</h1>
            <p style="color: var(--text-secondary); margin-top: 5px;">Manage users, assign roles, and view device trust scores.</p>
          </div>
          <button class="btn btn-primary" onclick="window.AdminUsers.openModal()">+ Provision Employee</button>
        </header>
        
        <div class="card" style="padding: 0; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
          <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead style="background: var(--bg-secondary); border-bottom: 1px solid var(--border-subtle);">
              <tr>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase;">Email</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase;">Department</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase;">Trust Score</th>
                <th style="padding: 16px 24px; color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase;">Role Assignment</th>
              </tr>
            </thead>
            <tbody id="users-table-body">
                <tr><td colspan="4" style="padding: 40px; text-align: center; color: var(--text-muted);">Loading users...</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Sleek Provisioning Modal Overlay -->
        <div id="provision-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 1000; align-items: center; justify-content: center;">
            <div class="card fade-in" style="width: 450px; padding: 35px; box-shadow: 0 10px 40px rgba(0,0,0,0.6); border: 1px solid var(--border-strong); background: var(--bg-elevated);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                    <h2 style="margin: 0; color: var(--text-primary); font-size: 1.6rem; display: flex; align-items: center; gap: 10px;">👤 Provision User</h2>
                    <button class="btn btn-ghost" onclick="window.AdminUsers.closeModal()" style="padding: 5px; font-size: 1.2rem; color: var(--text-muted);">&times;</button>
                </div>
                
                <div class="form-group" style="margin-bottom: 20px;">
                    <label style="color: var(--text-secondary); display: block; margin-bottom: 8px; font-weight: 600;">Employee Email Address</label>
                    <input type="email" id="prov-email" class="input" placeholder="e.g. alice@acme.com" style="width: 100%; padding: 14px; background: var(--bg-base); border: 1px solid var(--border-strong); border-radius: 8px; color: var(--text-primary); font-size: 1rem;">
                </div>
                
                <div class="form-group" style="margin-bottom: 35px;">
                    <label style="color: var(--text-secondary); display: block; margin-bottom: 8px; font-weight: 600;">Starting Role</label>
                    <select id="prov-role" class="input" style="width: 100%; padding: 14px; background: var(--bg-base); border: 1px solid var(--border-strong); border-radius: 8px; color: var(--text-primary); font-size: 1rem;">
                        <option value="EMPLOYEE">EMPLOYEE (Standard Access)</option>
                        <option value="MANAGER">MANAGER (Department Level)</option>
                        <option value="DEPT_HEAD">DEPT_HEAD (Executive Level)</option>
                        <option value="AUDITOR">AUDITOR (Read-Only Logs)</option>
                        <option value="SECURITY_ADMIN">SECURITY_ADMIN (Threat Management)</option>
                        <option value="SUPER_ADMIN">SUPER_ADMIN (Full Tenant Access)</option>
                    </select>
                </div>
                
                <button class="btn btn-primary" onclick="window.AdminUsers.submitProvision()" style="width: 100%; padding: 16px; font-size: 1.1rem; font-weight: bold; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 240, 255, 0.3);">Create User Account</button>
            </div>
        </div>
      </div>
    `;
  },

  async afterRender() {
      try {
          const data = await window.api.getUsers();
          const tbody = document.getElementById('users-table-body');
          if (!data || !data.users || data.users.length === 0) {
              tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 30px;">No users found.</td></tr>`;
              return;
          }

          let html = '';
          const roles = ['SUPER_ADMIN', 'SECURITY_ADMIN', 'DEPT_HEAD', 'MANAGER', 'EMPLOYEE', 'AUDITOR'];

          data.users.forEach(user => {
              let scoreColor = '#52c41a';
              if (user.trust_score < 90) scoreColor = 'var(--ztsdx-amber)';
              if (user.trust_score < 70) scoreColor = '#ff4d4f';

              let selectHtml = `<select class="input" onchange="window.AdminUsers.changeRole('${user.id}', this.value)" style="padding: 8px 12px; width: auto; background: var(--bg-base); border: 1px solid var(--border-strong); color: var(--text-primary); border-radius: 6px;">`;
              roles.forEach(r => {
                  const selected = r === user.role ? 'selected' : '';
                  selectHtml += `<option value="${r}" ${selected}>${r}</option>`;
              });
              selectHtml += `</select>`;

              html += `
                <tr style="border-bottom: 1px solid var(--border-subtle); transition: background 0.2s;" onmouseover="this.style.background='var(--bg-secondary)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 16px 24px; font-weight: 500; font-size: 1.05rem;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; color: var(--ztsdx-cyan);">
                                ${user.email.charAt(0).toUpperCase()}
                            </div>
                            ${user.email}
                        </div>
                    </td>
                    <td style="padding: 16px 24px; color: var(--text-secondary);">${user.department || 'Unknown'}</td>
                    <td style="padding: 16px 24px; color: ${scoreColor}; font-weight: bold; font-size: 1.1rem;">
                        ${user.trust_score}
                    </td>
                    <td style="padding: 16px 24px; display: flex; align-items: center;">
                        ${selectHtml}
                        <span id="save-msg-${user.id}" style="color: #52c41a; font-size: 0.85rem; margin-left: 12px; opacity: 0; transition: opacity 0.3s; font-weight: 600;">✓ Saved</span>
                    </td>
                </tr>
              `;
          });
          tbody.innerHTML = html;
      } catch (e) {
          console.error(e);
          document.getElementById('users-table-body').innerHTML = `<tr><td colspan="4" style="text-align: center; color: #ff4d4f;">Failed to load users.</td></tr>`;
      }
  },

  async changeRole(userId, newRole) {
      try {
          await window.api.updateUserRole(userId, newRole);
          // Show quick save flash
          const msg = document.getElementById('save-msg-' + userId);
          if (msg) {
              msg.style.opacity = '1';
              setTimeout(() => { msg.style.opacity = '0'; }, 2000);
          }
      } catch (error) {
          await Modal.error('Failed to update role: ' + error.message);
          this.afterRender(); // Re-render to reset the dropdown
      }
  },

  openModal() {
      document.getElementById('provision-modal').style.display = 'flex';
      document.getElementById('prov-email').value = '';
      document.getElementById('prov-role').value = 'EMPLOYEE';
  },

  closeModal() {
      document.getElementById('provision-modal').style.display = 'none';
  },

  async submitProvision() {
      const email = document.getElementById('prov-email').value.trim();
      const role  = document.getElementById('prov-role').value;

      if (!email || !email.includes('@')) {
          await Modal.alert('Please enter a valid email address.', { title: 'Invalid Input', icon: '⚠️' });
          return;
      }

      const userStr = sessionStorage.getItem('current_user');
      const orgId   = userStr ? JSON.parse(userStr).org_id : null;

      try {
          await window.api.provisionUser(email, role, orgId, 'General');
          this.closeModal();
          await Modal.success(`Employee provisioned. They will receive an activation code.`);
          this.afterRender();
      } catch (error) {
          await Modal.error('Failed to provision user: ' + error.message);
      }
  }
};
