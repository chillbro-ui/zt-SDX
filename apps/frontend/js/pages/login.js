window.Login = {
  render() {
    return `
      <div class="login-page" style="display:flex; justify-content:center; align-items:center; min-height: 100vh;">
        <div class="card" style="width: 420px; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
          <div style="text-align:center; margin-bottom: 30px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🔐</div>
            <h2 style="color: var(--ztsdx-cyan); font-weight: 700; font-size: 1.8rem;">Secure Login</h2>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 5px;">Enter your credentials to access the vault</p>
          </div>

          <!-- OTP Challenge (hidden by default) -->
          <div id="otp-section" style="display:none;">
            <div style="text-align:center; margin-bottom: 20px; padding: 16px; background: rgba(0,240,255,0.05); border: 1px solid rgba(0,240,255,0.2); border-radius: 8px;">
              <div style="font-size: 1.5rem; margin-bottom: 8px;">📱</div>
              <div style="color: var(--text-primary); font-weight: 600;">MFA Required</div>
              <div style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px;">Enter the 6-digit code sent to your device</div>
            </div>
            <div class="form-group" style="margin-bottom: 20px;">
              <label style="display:block; margin-bottom: 8px; color: var(--text-primary);">One-Time Password</label>
              <input type="text" id="otp-input" class="input" style="width:100%; padding:12px; text-align:center; font-size:1.4rem; letter-spacing:8px;" maxlength="6" placeholder="000000">
            </div>
            <button class="btn btn-primary" style="width:100%; padding:12px;" onclick="window.Login.handleOtp()">Verify OTP</button>
            <button class="btn btn-ghost" style="width:100%; margin-top:10px; color:var(--text-muted);" onclick="window.Login.resetToLogin()">← Back to Login</button>
          </div>

          <!-- Login Form -->
          <form id="login-form" onsubmit="window.Login.handleLogin(event)">
            <div class="form-group" style="margin-bottom: 20px;">
              <label style="display:block; margin-bottom: 8px; color: var(--text-primary); font-size: 0.95rem;">Work Email</label>
              <input type="email" id="login-email" class="input" style="width: 100%; padding: 12px;" required placeholder="alice@acme.com">
            </div>

            <div class="form-group" style="margin-bottom: 25px;">
              <label style="display:block; margin-bottom: 8px; color: var(--text-primary); font-size: 0.95rem;">Password</label>
              <input type="password" id="login-password" class="input" style="width: 100%; padding: 12px;" required>
            </div>

            <div id="login-error" style="color: #ff4d4f; background: rgba(255,77,79,0.1); padding: 10px; border-radius: 6px; margin-bottom: 20px; display: none; font-size: 0.9rem; border: 1px solid rgba(255,77,79,0.3);"></div>

            <button type="submit" class="btn btn-primary" style="width: 100%; padding: 12px; font-size: 1.05rem;" id="login-submit">
              Sign In
            </button>
          </form>

          <div style="text-align:center; margin-top: 25px;">
            <a href="#home" style="color: var(--text-muted); text-decoration: none; font-size: 0.9rem;">← Back to Home</a>
          </div>
        </div>
      </div>
    `;
  },

  _challengeId: null,

  async handleLogin(event) {
    event.preventDefault();

    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    const submitBtn = document.getElementById('login-submit');

    errorDiv.style.display = 'none';
    submitBtn.innerText = 'Verifying...';
    submitBtn.disabled  = true;

    try {
      const response = await window.api.login(email, password, 'browser-fp-' + navigator.userAgent.length);

      // MFA challenge required
      if (response.otp_required) {
        this._challengeId = response.challenge_id;
        // Show OTP code in dev mode (backend returns it for demo)
        if (response.otp) {
          document.getElementById('otp-input') && (document.getElementById('otp-input').value = response.otp);
        }
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('otp-section').style.display = 'block';
        return;
      }

      this._finalizeLogin(response);
    } catch (error) {
      errorDiv.innerText = error.message || 'Login failed. Please check your credentials.';
      errorDiv.style.display = 'block';
    } finally {
      submitBtn.innerText = 'Sign In';
      submitBtn.disabled  = false;
    }
  },

  async handleOtp() {
    const otp = document.getElementById('otp-input').value.trim();
    if (!otp || otp.length !== 6) {
      await Modal.alert('Please enter the 6-digit OTP code.', { title: 'Invalid OTP', icon: '⚠️' });
      return;
    }

    try {
      const response = await window.api.verifyOtp(this._challengeId, otp);
      this._finalizeLogin(response);
    } catch (error) {
      await Modal.error(error.message || 'Invalid OTP. Please try again.');
    }
  },

  _finalizeLogin(response) {
    // Normalise user object — backend shape: { id, email, role, org_id, clearance_level, status }
    const user = response.user || {};
    const normalised = {
      id:             user.id,
      email:          user.email,
      role:           user.role || 'EMPLOYEE',
      department:     user.department || 'General',
      org_id:         user.org_id || null,
      clearance_level: user.clearance_level || 1,
      // risk_score from login response (from risk-service)
      trust_score:    response.risk_score !== undefined ? Math.max(0, 100 - response.risk_score) : 85,
      risk_score:     response.risk_score || 0,
      risk_level:     response.risk_level || 'LOW',
    };

    sessionStorage.setItem('current_user', JSON.stringify(normalised));

    if (window.App && window.App.updateUserDropdown) {
      window.App.updateUserDropdown();
    }

    window.location.hash = '#dashboard';
    window.location.reload();
  },

  resetToLogin() {
    this._challengeId = null;
    document.getElementById('otp-section').style.display = 'none';
    document.getElementById('login-form').style.display  = 'block';
  }
};
