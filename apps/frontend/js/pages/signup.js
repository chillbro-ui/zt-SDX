window.Signup = {
  render() {
    return `
      <style>
        .signup-container {
            width: 100%; max-width: 650px;
            background: var(--bg-elevated);
            border-radius: 16px;
            box-shadow: 0 16px 40px rgba(0,0,0,0.4);
            border: 1px solid var(--border-strong);
            padding: 50px;
            margin-top: 20px;
            position: relative;
            overflow: hidden;
        }
        
        /* Step Tracker */
        .step-tracker {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 40px;
            position: relative;
        }
        .step-tracker::before {
            content: '';
            position: absolute;
            top: 50%; left: 20%; right: 20%;
            height: 2px;
            background: var(--border-strong);
            z-index: 1;
            transform: translateY(-50%);
        }
        .step-tracker .progress-line {
            position: absolute;
            top: 50%; left: 20%; width: 0%;
            height: 2px;
            background: var(--ztsdx-cyan);
            z-index: 2;
            transform: translateY(-50%);
            transition: width 0.4s ease;
        }
        .step-tracker.step2 .progress-line { width: 60%; }
        
        .step-dot {
            width: 36px; height: 36px;
            border-radius: 50%;
            background: var(--bg-surface);
            border: 2px solid var(--border-strong);
            color: var(--text-muted);
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 1rem;
            z-index: 3;
            transition: all 0.3s ease;
        }
        .step-dot.active {
            border-color: var(--ztsdx-cyan);
            background: rgba(0,240,255,0.1);
            color: var(--ztsdx-cyan);
            box-shadow: 0 0 15px rgba(0,240,255,0.2);
        }
        .step-dot.completed {
            background: var(--ztsdx-cyan);
            border-color: var(--ztsdx-cyan);
            color: #000;
        }
        
        .step-label {
            position: absolute;
            top: 45px;
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            white-space: nowrap;
            font-weight: 600;
        }
        
        /* Forms */
        .step-form {
            animation: fadeIn 0.4s ease forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }
      </style>

      <div class="signup-container fade-in">
        
        <!-- Headers -->
        <div style="text-align: center; margin-bottom: 30px;">
          <h2 style="color: var(--ztsdx-cyan); font-size: 2.2rem; margin-bottom: 10px; font-weight: 700;">Provision Tenant</h2>
          <p style="color: var(--text-secondary); font-size: 1.1rem;">Set up your secure Enterprise data vault.</p>
        </div>

        <!-- Step Indicator -->
        <div class="step-tracker" id="signup-tracker">
            <div class="progress-line"></div>
            
            <div style="position: relative; display: flex; flex-direction: column; align-items: center; margin-right: 60%;">
                <div class="step-dot active" id="dot-1">1</div>
                <div class="step-label" style="color: var(--text-primary);">Super Admin</div>
            </div>
            
            <div style="position: relative; display: flex; flex-direction: column; align-items: center;">
                <div class="step-dot" id="dot-2">2</div>
                <div class="step-label">Organization</div>
            </div>
        </div>

        <!-- Alerts -->
        <div id="signup-error" style="color: #ff4d4f; background: rgba(255,77,79,0.1); padding: 15px; border-radius: 8px; margin-bottom: 25px; display: none; font-size: 1rem; border: 1px solid rgba(255,77,79,0.3); font-weight: 500;"></div>
        <div id="signup-success" style="color: #52c41a; background: rgba(82,196,26,0.1); padding: 25px; border-radius: 8px; margin-bottom: 25px; display: none; font-size: 1.1rem; border: 1px solid rgba(82,196,26,0.3); text-align: center; font-weight: 500;"></div>

        <!-- STEP 1: Admin Account -->
        <form id="step1-form" class="step-form" onsubmit="event.preventDefault(); window.Signup.handleStep1(); return false;">
          <div class="form-group" style="margin-bottom: 25px;">
            <label>Admin Email <span style="color:#ff4d4f">*</span></label>
            <input type="email" id="admin-email" class="input" required placeholder="admin@acme.com">
          </div>

          <div class="form-group" style="margin-bottom: 35px;">
            <label>Secure Password <span style="color:#ff4d4f">*</span></label>
            <input type="password" id="admin-password" class="input" required placeholder="••••••••">
          </div>

          <button type="submit" class="btn btn-primary" style="width: 100%; padding: 16px; font-size: 1.15rem; font-weight: bold; border-radius: 8px;" id="step1-submit">
            Continue to Step 2 ➔
          </button>
        </form>

        <!-- STEP 2: Organization Details -->
        <form id="step2-form" class="step-form" style="display: none;" onsubmit="event.preventDefault(); window.Signup.handleStep2(); return false;">
          <div class="form-group" style="margin-bottom: 25px;">
            <label>Organization Name <span style="color:#ff4d4f">*</span></label>
            <input type="text" id="org-name" class="input" required placeholder="e.g. Acme Corp">
          </div>

          <div class="form-group" style="margin-bottom: 25px;">
            <label>Primary Domain <span style="color:#ff4d4f">*</span></label>
            <input type="text" id="org-domain" class="input" required placeholder="e.g. acme.com">
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 35px;">
              <div class="form-group">
                <label>Industry</label>
                <select id="org-industry" class="input">
                  <option value="Technology">Technology</option>
                  <option value="Finance">Finance & Banking</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div class="form-group">
                <label>Country Code</label>
                <input type="text" id="org-country" class="input" placeholder="US" maxlength="2">
              </div>
          </div>

          <div style="display: flex; gap: 15px;">
              <button type="button" class="btn btn-secondary" style="padding: 16px; font-size: 1.15rem; border-radius: 8px; flex: 1;" onclick="window.Signup.backToStep1()">
                Back
              </button>
              <button type="submit" class="btn btn-primary" style="padding: 16px; font-size: 1.15rem; font-weight: bold; border-radius: 8px; flex: 2; box-shadow: 0 4px 15px rgba(0, 240, 255, 0.2);" id="step2-submit">
                Create Enterprise Vault
              </button>
          </div>
        </form>
      </div>
    `;
  },

  async handleStep1() {
    const email    = document.getElementById('admin-email').value.trim();
    const password = document.getElementById('admin-password').value;
    const errorDiv  = document.getElementById('signup-error');
    const submitBtn = document.getElementById('step1-submit');

    errorDiv.style.display = 'none';
    submitBtn.innerText = 'Creating Admin...';
    submitBtn.disabled  = true;

    try {
      // Register on auth-service then auto-login to get tokens
      const response = await window.api.register(email, password);

      // Normalise user shape from login response
      const user = response.user || {};
      const normalised = {
        id:              user.id,
        email:           user.email,
        role:            user.role || 'SUPER_ADMIN',
        department:      user.department || 'IT Security',
        org_id:          user.org_id || null,
        clearance_level: user.clearance_level || 5,
        trust_score:     100,
        risk_score:      response.risk_score || 0,
        risk_level:      response.risk_level || 'LOW',
      };

      sessionStorage.setItem('current_user', JSON.stringify(normalised));

      // Advance to Step 2
      document.getElementById('step1-form').style.display = 'none';
      document.getElementById('step2-form').style.display = 'block';

      document.getElementById('signup-tracker').classList.add('step2');
      document.getElementById('dot-1').classList.remove('active');
      document.getElementById('dot-1').classList.add('completed');
      document.getElementById('dot-1').innerHTML = '✓';
      document.getElementById('dot-2').classList.add('active');
      document.querySelectorAll('.step-label')[1].style.color = 'var(--text-primary)';

    } catch (error) {
      errorDiv.innerText = error.message || 'Failed to create admin account.';
      errorDiv.style.display = 'block';
      submitBtn.innerText = 'Continue to Step 2 ➔';
      submitBtn.disabled  = false;
    }
  },

  backToStep1() {
      // Allow user to visually step back (although admin is technically created in mock state)
      document.getElementById('step2-form').style.display = 'none';
      document.getElementById('step1-form').style.display = 'block';
      
      const submitBtn = document.getElementById('step1-submit');
      submitBtn.innerText = 'Admin Created - Continue ➔';
      submitBtn.disabled = false;

      // Update Tracker Visuals
      document.getElementById('signup-tracker').classList.remove('step2');
      document.getElementById('dot-1').classList.add('active');
      document.getElementById('dot-1').classList.remove('completed');
      document.getElementById('dot-1').innerHTML = '1';
      document.getElementById('dot-2').classList.remove('active');
      document.querySelectorAll('.step-label')[1].style.color = 'var(--text-muted)';
  },

  async handleStep2() {
    const name = document.getElementById('org-name').value;
    const domain = document.getElementById('org-domain').value;
    const industry = document.getElementById('org-industry').value;
    const country = document.getElementById('org-country').value || 'US';
    
    const errorDiv = document.getElementById('signup-error');
    const successDiv = document.getElementById('signup-success');
    const submitBtn = document.getElementById('step2-submit');
    
    errorDiv.style.display = 'none';
    submitBtn.innerText = 'Provisioning Infrastructure...';
    submitBtn.disabled = true;

    try {
      // POST /orgs (Auth is automatically attached now!)
      const response = await window.api.request('/orgs', {
          method: 'POST',
          body: JSON.stringify({ name, domain, industry, country })
      });
      
      document.getElementById('step2-form').style.display = 'none';
      document.getElementById('signup-tracker').style.display = 'none';
      document.querySelector('.signup-container p').style.display = 'none';
      
      successDiv.innerHTML = `
        <div style="font-size: 3.5rem; margin-bottom: 15px;">🎉</div>
        <strong style="font-size: 1.4rem; color: var(--text-primary);">Tenant Successfully Provisioned!</strong><br><br>
        <span style="color: var(--text-secondary); line-height: 1.5; display: inline-block;">Your Super Admin account has been activated and your default departments are ready.</span><br>
        <div style="margin-top: 30px;">
            <button type="button" onclick="window.location.hash='#dashboard'; window.location.reload();" class="btn btn-primary" style="padding: 14px 28px; font-size: 1.15rem; font-weight: bold; border-radius: 8px;">Enter Secure Workspace</button>
        </div>
      `;
      successDiv.style.display = 'block';

    } catch (error) {
      errorDiv.innerText = error.message || 'Failed to register organization.';
      errorDiv.style.display = 'block';
      submitBtn.innerText = 'Create Enterprise Vault';
      submitBtn.disabled = false;
    }
  }
};
