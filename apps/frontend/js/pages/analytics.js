window.Analytics = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px;">
          <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Risk Analytics</h1>
          <p style="color: var(--text-secondary); margin-top: 5px;">Enterprise-wide data exposure and risk metrics powered by ML.</p>
        </header>

        <!-- KPI Cards -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 28px;">
          <div class="card" style="padding: 24px; border-top: 4px solid #52c41a;">
            <div style="color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">Files Active</div>
            <div id="kpi-files" style="font-size: 3rem; font-weight: 700; color: var(--text-primary);">—</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid #ff4d4f;">
            <div style="color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">Files Quarantined</div>
            <div id="kpi-quarantined" style="font-size: 3rem; font-weight: 700; color: #ff4d4f;">—</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid #faad14;">
            <div style="color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">Risk Alerts</div>
            <div id="kpi-alerts" style="font-size: 3rem; font-weight: 700; color: #faad14;">—</div>
          </div>
          <div class="card" style="padding: 24px; border-top: 4px solid var(--ztsdx-cyan);">
            <div style="color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px;">Audit Events</div>
            <div id="kpi-audit" style="font-size: 3rem; font-weight: 700; color: var(--ztsdx-cyan);">—</div>
          </div>
        </div>

        <!-- Risk Alerts Table -->
        <div class="card" style="padding: 0; overflow: hidden; margin-bottom: 24px;">
          <div style="padding: 20px 24px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: var(--text-primary);">🤖 Recent ML Risk Alerts</h3>
            <button class="btn btn-secondary" style="font-size: 0.85rem; padding: 6px 14px;" onclick="window.location.hash='#alerts'">View All</button>
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <thead style="background: var(--bg-secondary);">
              <tr>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">User</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Alert Type</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Severity</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Score Delta</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Time</th>
              </tr>
            </thead>
            <tbody id="analytics-risk-table">
              <tr><td colspan="5" style="padding: 30px; text-align: center; color: var(--text-muted);">Loading...</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Recent Audit Events -->
        <div class="card" style="padding: 0; overflow: hidden;">
          <div style="padding: 20px 24px; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: var(--text-primary);">📜 Recent Audit Events</h3>
            <button class="btn btn-secondary" style="font-size: 0.85rem; padding: 6px 14px;" onclick="window.location.hash='#audit'">View Ledger</button>
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; font-family: 'JetBrains Mono', monospace;">
            <thead style="background: var(--bg-secondary);">
              <tr>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Action</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Actor</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Result</th>
                <th style="padding: 12px 20px; color: var(--text-secondary); text-align: left; font-size: 0.8rem; text-transform: uppercase;">Time</th>
              </tr>
            </thead>
            <tbody id="analytics-audit-table">
              <tr><td colspan="4" style="padding: 30px; text-align: center; color: var(--text-muted);">Loading...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async afterRender() {
    // Fetch all data in parallel
    const [filesRes, alertsRes, riskAlertsRes, auditRes] = await Promise.allSettled([
      window.api.getFiles(),
      window.api.getAlerts(100),
      window.api.getRiskAlerts(20),
      window.api.getAuditEvents(10)
    ]);

    // ── KPIs ──────────────────────────────────────────────────────────────
    if (filesRes.status === 'fulfilled') {
      const files = filesRes.value?.files || [];
      document.getElementById('kpi-files').innerText       = files.filter(f => f.status === 'ACTIVE').length;
      document.getElementById('kpi-quarantined').innerText = files.filter(f => f.status === 'QUARANTINED').length;
    }

    const riskAlerts = riskAlertsRes.status === 'fulfilled'
      ? (Array.isArray(riskAlertsRes.value) ? riskAlertsRes.value : [])
      : [];
    document.getElementById('kpi-alerts').innerText = riskAlerts.length;

    const auditLogs = auditRes.status === 'fulfilled'
      ? (Array.isArray(auditRes.value) ? auditRes.value : (auditRes.value?.logs || []))
      : [];
    document.getElementById('kpi-audit').innerText = auditLogs.length;

    // ── Risk Alerts Table ─────────────────────────────────────────────────
    const riskTbody = document.getElementById('analytics-risk-table');
    if (riskAlerts.length === 0) {
      riskTbody.innerHTML = `<tr><td colspan="5" style="padding: 20px; text-align: center; color: var(--text-muted);">No risk alerts detected.</td></tr>`;
    } else {
      riskTbody.innerHTML = riskAlerts.slice(0, 10).map(a => {
        const color = { CRITICAL: '#ff4d4f', HIGH: '#ff4d4f', MEDIUM: '#faad14', LOW: '#52c41a' }[a.severity] || '#faad14';
        const time  = a.created_at ? new Date(a.created_at).toLocaleString() : '—';
        return `
          <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="padding: 12px 20px; color: var(--ztsdx-cyan);">${a.user_id?.substring(0, 8)}...</td>
            <td style="padding: 12px 20px; color: var(--text-primary);">${a.alert_type?.replace(/_/g, ' ')}</td>
            <td style="padding: 12px 20px; color: ${color}; font-weight: 600;">${a.severity}</td>
            <td style="padding: 12px 20px; color: ${color};">+${a.score_delta}</td>
            <td style="padding: 12px 20px; color: var(--text-muted); font-size: 0.85rem;">${time}</td>
          </tr>
        `;
      }).join('');
    }

    // ── Audit Table ───────────────────────────────────────────────────────
    const auditTbody = document.getElementById('analytics-audit-table');
    if (auditLogs.length === 0) {
      auditTbody.innerHTML = `<tr><td colspan="4" style="padding: 20px; text-align: center; color: var(--text-muted);">No audit events yet.</td></tr>`;
    } else {
      auditTbody.innerHTML = auditLogs.slice(0, 8).map(log => {
        const resultColor = log.result === 'SUCCESS' ? '#52c41a' : (log.result === 'FAILURE' ? '#ff4d4f' : 'var(--text-secondary)');
        const time = log.created_at ? new Date(log.created_at).toLocaleString() : '—';
        return `
          <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="padding: 12px 20px; color: var(--text-primary); font-weight: 600;">${log.action || '—'}</td>
            <td style="padding: 12px 20px; color: var(--ztsdx-cyan);">${(log.actor || '—').substring(0, 12)}...</td>
            <td style="padding: 12px 20px; color: ${resultColor}; font-weight: 600;">${log.result || '—'}</td>
            <td style="padding: 12px 20px; color: var(--text-muted); font-size: 0.85rem;">${time}</td>
          </tr>
        `;
      }).join('');
    }
  }
};
