window.Dashboard = {
  render() {
    const userStr = sessionStorage.getItem('current_user');
    const user = userStr ? JSON.parse(userStr) : { email: 'User', role: 'EMPLOYEE', trust_score: 85 };
    const name = user.email.split('@')[0];
    
    let dashboardContent = '';
    switch(user.role) {
        case 'SUPER_ADMIN': dashboardContent = this.renderSuperAdmin(user); break;
        case 'SECURITY_ADMIN': dashboardContent = this.renderSecurityAdmin(user); break;
        case 'DEPT_HEAD': dashboardContent = this.renderDeptHead(user); break;
        case 'MANAGER': dashboardContent = this.renderManager(user); break;
        case 'AUDITOR': dashboardContent = this.renderAuditor(user); break;
        case 'PLATFORM_ADMIN': dashboardContent = this.renderPlatformAdmin(user); break;
        default: dashboardContent = this.renderEmployee(user); break; // EMPLOYEE
    }

    return `
      <div class="dashboard-overview fade-in">
        <header style="margin-bottom: 30px;">
          <h1 style="color: var(--text-primary); font-size: 2.2rem; font-weight: 600;">Welcome back, ${name}</h1>
          <p style="color: var(--text-secondary); font-size: 1.1rem; margin-top: 5px;">Here is your personalized ${user.role.replace('_', ' ')} workspace.</p>
        </header>
        ${dashboardContent}
      </div>
    `;
  },

  renderPlatformAdmin(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Registered Tenants</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);" id="dashboard-tenant-count">...</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Active organizations hosted on ZT-SDX.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid #52c41a;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Platform Uptime</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: #52c41a;">99.99%</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Across all global regions.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid #ff4d4f;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Threats Blocked</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);">42,891</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Global quarantine statistics.</div>
          </div>
      </div>
      
      <div class="card" style="padding: 24px;">
          <h3 style="color: var(--text-primary); margin: 0 0 20px 0;">Live Tenant Registry</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;">List of all organizations provisioned on the ZT-SDX Platform.</p>
          <div style="overflow-x: auto;">
              <table style="width: 100%; border-collapse: collapse; text-align: left;">
                  <thead>
                      <tr style="border-bottom: 1px solid var(--border-subtle); color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">
                          <th style="padding: 12px 16px;">Tenant ID</th>
                          <th style="padding: 12px 16px;">Organization Name</th>
                          <th style="padding: 12px 16px;">Domain</th>
                          <th style="padding: 12px 16px;">Region</th>
                          <th style="padding: 12px 16px;">Registered Date</th>
                      </tr>
                  </thead>
                  <tbody id="tenant-table-body" style="font-size: 0.95rem;">
                      <tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">Loading tenants...</td></tr>
                  </tbody>
              </table>
          </div>
      </div>
    `;
  },

  renderSuperAdmin(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid #52c41a;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Global Trust Score</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: #52c41a;">99</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Network integrity is optimal.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Access Level</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin-top: 15px;">SUPER ADMIN</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 15px;">Full platform clearance.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-purple);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Total Files Secured</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);" id="dashboard-file-count">...</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Across all departments.</div>
          </div>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
          <div class="card" style="padding: 24px; border-left: 4px solid #ff4d4f; background: rgba(255, 77, 79, 0.02);">
              <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">🚨 Security Alerts <span style="background: rgba(255, 77, 79, 0.15); color: #ff4d4f; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; float: right;">Action Needed</span></h3>
              <p style="color: var(--text-secondary); font-size: 0.95rem;">2 active threats detected globally in the last 24 hours.</p>
              <button class="btn btn-secondary" style="margin-top: 15px;" onclick="window.location.hash='#alerts'">Review Alerts</button>
          </div>
          <div class="card" style="padding: 24px; border-left: 4px solid var(--ztsdx-cyan); background: rgba(0, 240, 255, 0.02);">
              <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">✅ Pending Approvals <span style="background: rgba(0, 240, 255, 0.15); color: var(--ztsdx-cyan); padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; float: right;">Queue Active</span></h3>
              <p style="color: var(--text-secondary); font-size: 0.95rem;">Files are waiting in the staging queue for your manual approval.</p>
              <button class="btn btn-secondary" style="margin-top: 15px;" onclick="window.location.hash='#files'">Review Queue</button>
          </div>
      </div>
    `;
  },

  renderSecurityAdmin(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid #faad14;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Global Risk Score</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: #faad14;">42/100</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Elevated risk detected.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid #ff4d4f;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Active Threats</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: #ff4d4f;">2</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Quarantined payloads.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">DLP Engine</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #52c41a; margin-top: 15px;">ONLINE</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 15px;">All uploads actively scanned.</div>
          </div>
      </div>
      <div class="card" style="padding: 24px; border-left: 4px solid var(--ztsdx-cyan);">
          <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">🛡️ Security Operations Center</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;">Review anomalous user sessions and system alerts.</p>
          <div style="display: flex; gap: 15px;">
              <button class="btn btn-primary" onclick="window.location.hash='#alerts'">Threat Alerts</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#admin-users'">User Sessions</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#analytics'">Risk Analytics</button>
          </div>
      </div>
    `;
  },

  renderDeptHead(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid #52c41a;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Dept Trust Score</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: #52c41a;">${user.trust_score || '90'}</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Department</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin-top: 15px;">${user.department || 'General'}</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-purple);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Dept Files</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);" id="dashboard-file-count">...</div>
          </div>
      </div>
      <div class="card" style="padding: 24px; border-left: 4px solid var(--ztsdx-cyan);">
          <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">🏢 Department Management</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;">Manage your team's secure workspace and external shares.</p>
          <div style="display: flex; gap: 15px;">
              <button class="btn btn-primary" onclick="window.location.hash='#files'">Department Vault</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#admin-users'">Manage Employees</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#shares'">External Shares</button>
          </div>
      </div>
    `;
  },

  renderManager(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Team Files Secured</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);" id="dashboard-file-count">...</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Fully encrypted.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-purple);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Active Share Links</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);">3</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">External vendor access.</div>
          </div>
      </div>
      <div class="card" style="padding: 24px; border-left: 4px solid #52c41a; background: rgba(82, 196, 26, 0.05);">
          <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">🛡️ Zero-Trust Workspace Active</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;">Your operational workspace is secure. All uploads are automatically scanned.</p>
          <div style="display: flex; gap: 15px;">
              <button class="btn btn-primary" onclick="window.location.hash='#upload'">📤 Upload Data</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#files'">📁 Browse Vault</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#shares'">🔗 Share Centre</button>
          </div>
      </div>
    `;
  },

  renderEmployee(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid #52c41a;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Your Trust Score</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: #52c41a;">${user.trust_score || '85'}</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Device verified.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Your Vault</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);" id="dashboard-file-count">...</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Documents secured.</div>
          </div>
      </div>
      <div class="card" style="padding: 24px; border-left: 4px solid var(--ztsdx-cyan); background: rgba(0, 240, 255, 0.05);">
          <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">Welcome to your Secure Workspace</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;">Upload sensitive files to have them encrypted and safely stored.</p>
          <div style="display: flex; gap: 15px;">
              <button class="btn btn-primary" onclick="window.location.hash='#upload'">📤 Upload File</button>
              <button class="btn btn-secondary" onclick="window.location.hash='#files'">📁 View My Files</button>
          </div>
      </div>
    `;
  },

  renderAuditor(user) {
    return `
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 30px;">
          <div class="card" style="padding: 24px; border-top: 4px solid #52c41a;">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Ledger Integrity</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #52c41a; margin-top: 15px;">100% VERIFIED</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 15px;">Blockchain synchronization intact.</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-purple);">
            <div style="color: var(--text-secondary); margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Total Logs Processed</div>
            <div style="font-size: 2.8rem; font-weight: 700; color: var(--text-primary);">24,892</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">Immutable records generated.</div>
          </div>
      </div>
      <div class="card" style="padding: 24px; border-left: 4px solid var(--ztsdx-cyan); background: rgba(0, 240, 255, 0.05);">
          <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">📜 Compliance & Auditing Mode</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;">You are currently in read-only Audit Mode. You can view the immutable ledger of all system events.</p>
          <div style="display: flex; gap: 15px;">
              <button class="btn btn-primary" onclick="window.location.hash='#audit'">View Audit Ledger</button>
          </div>
      </div>
    `;
  },

  async afterRender() {
      const userStr = sessionStorage.getItem('current_user');
      const user = userStr ? JSON.parse(userStr) : { role: 'EMPLOYEE' };

      if (user.role === 'PLATFORM_ADMIN') {
          try {
              const data = await window.api.request('/orgs', { method: 'GET' });
              const tbody = document.getElementById('tenant-table-body');
              const countElem = document.getElementById('dashboard-tenant-count');
              
              if (countElem && data && data.organizations) {
                  countElem.innerText = data.organizations.length;
              }
              
              if (tbody && data && data.organizations) {
                  if (data.organizations.length === 0) {
                      tbody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">No tenants registered yet.</td></tr>`;
                  } else {
                      tbody.innerHTML = data.organizations.map(org => `
                          <tr style="border-bottom: 1px solid var(--border-subtle);">
                              <td style="padding: 12px 16px; font-family: monospace; color: var(--ztsdx-cyan);">${org.id}</td>
                              <td style="padding: 12px 16px; font-weight: 500; color: var(--text-primary);">${org.name}</td>
                              <td style="padding: 12px 16px; color: var(--text-secondary);">${org.domain}</td>
                              <td style="padding: 12px 16px; color: var(--text-secondary);">${org.country}</td>
                              <td style="padding: 12px 16px; color: var(--text-secondary);">${new Date(org.registered_at).toLocaleDateString()}</td>
                          </tr>
                      `).join('');
                  }
              }
          } catch (e) {
              console.error("Failed to load tenants", e);
          }
          return; // Skip file fetching for platform admin
      }

      // Fetch files to update the file count badge for roles that have it
      try {
          const data = await window.api.request('/files', { method: 'GET' });
          const countElem = document.getElementById('dashboard-file-count');
          if (countElem && data && data.files) {
              countElem.innerText = data.files.length;
          }
      } catch (error) {
          const countElem = document.getElementById('dashboard-file-count');
          if (countElem) countElem.innerHTML = `<span style="font-size: 1rem; color: #ff4d4f;">Error</span>`;
      }
  }
};
