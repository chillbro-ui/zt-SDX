window.Policies = {
  render() {
    return `
      <div class="fade-in">
        <header style="margin-bottom: 24px;">
          <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 600;">Policy Studio</h1>
          <p style="color: var(--text-secondary); margin-top: 5px;">Define data classification and zero-trust access rules.</p>
        </header>
        <div style="display: grid; grid-template-columns: 1fr; gap: 20px;">
            <div class="card" style="padding: 24px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #52c41a;">
                <div>
                    <h3 style="margin: 0; color: var(--text-primary); font-size: 1.2rem;">Global PII Protection</h3>
                    <p style="color: var(--text-secondary); margin-top: 6px; font-size: 0.95rem;">Automatically quarantine any uploaded file containing SSNs, Credit Cards, or Passwords.</p>
                </div>
                <div style="background: rgba(82, 196, 26, 0.15); color: #52c41a; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; border: 1px solid rgba(82, 196, 26, 0.3);">ACTIVE</div>
            </div>
            <div class="card" style="padding: 24px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #52c41a;">
                <div>
                    <h3 style="margin: 0; color: var(--text-primary); font-size: 1.2rem;">Strict Device Posture</h3>
                    <p style="color: var(--text-secondary); margin-top: 6px; font-size: 0.95rem;">Require Risk Score > 90 to access files classified as CONFIDENTIAL or RESTRICTED.</p>
                </div>
                <div style="background: rgba(82, 196, 26, 0.15); color: #52c41a; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; border: 1px solid rgba(82, 196, 26, 0.3);">ACTIVE</div>
            </div>
            <button class="btn btn-primary" style="padding: 20px; border: 2px dashed var(--ztsdx-cyan); background: transparent; color: var(--ztsdx-cyan); font-size: 1.1rem;">+ Create New Policy</button>
        </div>
      </div>
    `;
  }
};
