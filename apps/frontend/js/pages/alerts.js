window.Alerts = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Alerts Center</h1>
            <p style="color: var(--text-secondary); margin-top: 5px;">Real-time AI anomaly detection and policy violations.</p>
          </div>
          <div id="alert-count-badge" class="trust-indicator" style="background: rgba(255,77,79,0.1); border-color: rgba(255,77,79,0.3); color: #ff4d4f; font-weight: bold;">
            <span class="dot" style="background: #ff4d4f; box-shadow: 0 0 8px #ff4d4f;"></span> Loading...
          </div>
        </header>

        <!-- Risk Alerts from risk-service -->
        <div style="margin-bottom: 32px;">
          <h2 style="color: var(--ztsdx-cyan); font-size: 1.2rem; font-weight: 600; margin-bottom: 16px;">🤖 ML Risk Alerts</h2>
          <div id="risk-alerts-list">
            <div class="card" style="padding: 30px; text-align: center; color: var(--text-muted);">⏳ Loading risk alerts...</div>
          </div>
        </div>

        <!-- System Alerts from alert-service -->
        <div>
          <h2 style="color: var(--text-primary); font-size: 1.2rem; font-weight: 600; margin-bottom: 16px;">🛡️ System Alerts</h2>
          <div id="system-alerts-list">
            <div class="card" style="padding: 30px; text-align: center; color: var(--text-muted);">⏳ Loading system alerts...</div>
          </div>
        </div>
      </div>
    `;
  },

  async afterRender() {
    // Load both alert sources in parallel
    const [riskAlerts, systemAlerts] = await Promise.allSettled([
      window.api.getRiskAlerts(50),
      window.api.getAlerts(50)
    ]);

    // ── Risk Alerts ───────────────────────────────────────────────────────
    const riskList = document.getElementById('risk-alerts-list');
    const riskData = riskAlerts.status === 'fulfilled' ? riskAlerts.value : [];
    const riskArr  = Array.isArray(riskData) ? riskData : (riskData.alerts || []);

    if (riskArr.length === 0) {
      riskList.innerHTML = `<div class="card" style="padding: 30px; text-align: center; color: var(--text-muted);">
        <div style="font-size: 2rem; margin-bottom: 8px;">✅</div>
        No ML risk alerts detected.
      </div>`;
    } else {
      riskList.innerHTML = riskArr.map(a => {
        const severityColor = { CRITICAL: '#ff4d4f', HIGH: '#ff4d4f', MEDIUM: '#faad14', LOW: '#52c41a' }[a.severity] || '#faad14';
        const severityIcon  = { CRITICAL: '🚨', HIGH: '⚠️', MEDIUM: '⚡', LOW: 'ℹ️' }[a.severity] || '⚠️';
        const time = a.created_at ? new Date(a.created_at).toLocaleString() : 'Just now';
        return `
          <div class="card" style="padding: 20px; border-left: 4px solid ${severityColor}; margin-bottom: 12px; background: rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <h3 style="color: ${severityColor}; margin: 0; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
                ${severityIcon} ${a.alert_type.replace(/_/g, ' ')}
                <span style="background: rgba(255,255,255,0.05); color: var(--text-muted); padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 400;">${a.severity}</span>
              </h3>
              <span style="color: var(--text-muted); font-size: 0.8rem; white-space: nowrap; margin-left: 16px;">${time}</span>
            </div>
            <p style="color: var(--text-primary); margin: 10px 0 0; font-size: 0.95rem;">${a.description}</p>
            <div style="margin-top: 8px; font-size: 0.85rem; color: var(--text-muted);">
              User: <span style="color: var(--ztsdx-cyan);">${a.user_id}</span>
              &nbsp;·&nbsp; Score delta: <span style="color: ${severityColor};">+${a.score_delta}</span>
            </div>
          </div>
        `;
      }).join('');
    }

    // ── System Alerts ─────────────────────────────────────────────────────
    const sysList = document.getElementById('system-alerts-list');
    const sysData = systemAlerts.status === 'fulfilled' ? systemAlerts.value : [];
    const sysArr  = Array.isArray(sysData) ? sysData : (sysData.alerts || []);

    if (sysArr.length === 0) {
      sysList.innerHTML = `<div class="card" style="padding: 30px; text-align: center; color: var(--text-muted);">
        <div style="font-size: 2rem; margin-bottom: 8px;">✅</div>
        No system alerts.
      </div>`;
    } else {
      sysList.innerHTML = sysArr.map(a => {
        const severityColor = { CRITICAL: '#ff4d4f', HIGH: '#ff4d4f', MEDIUM: '#faad14', LOW: '#52c41a' }[a.severity] || '#faad14';
        const time = a.created_at ? new Date(a.created_at).toLocaleString() : 'Just now';
        return `
          <div class="card" style="padding: 20px; border-left: 4px solid ${severityColor}; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between;">
              <h3 style="color: ${severityColor}; margin: 0; font-size: 1rem;">${a.type || a.alert_type || 'ALERT'}</h3>
              <span style="color: var(--text-muted); font-size: 0.8rem;">${time}</span>
            </div>
            <p style="color: var(--text-primary); margin: 10px 0 0; font-size: 0.95rem;">${a.details || a.description || ''}</p>
          </div>
        `;
      }).join('');
    }

    // Update badge
    const total = riskArr.length + sysArr.length;
    const badge = document.getElementById('alert-count-badge');
    if (badge) {
      badge.innerHTML = `<span class="dot" style="background: #ff4d4f; box-shadow: 0 0 8px #ff4d4f;"></span> ${total} Alert${total !== 1 ? 's' : ''}`;
    }
  }
};
