// =========================================================================
// ZT-SDX Enterprise — Home / Landing Page
// =========================================================================

window.Home = {
  render() {
    return `
      <style>
        .landing-page { padding-top: 80px; position: relative; }
        
        /* Top Navigation Bar */
        .landing-nav {
            position: fixed;
            top: 0; left: 0; right: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            background: rgba(10, 15, 30, 0.85);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            transition: opacity 0.4s ease, transform 0.4s ease;
        }
        .landing-nav.hidden {
            opacity: 0;
            pointer-events: none;
            transform: translateY(-20px);
        }
        .nav-logo { font-size: 1.5rem; font-weight: 800; color: var(--ztsdx-cyan); letter-spacing: 1px; }
        .nav-actions { display: flex; gap: 15px; }

        /* Shared Sections */
        .landing-section { padding: 100px 20px; max-width: 1100px; margin: 0 auto; }
        .hero-title { font-size: 4rem; font-weight: 800; line-height: 1.1; margin-bottom: 20px; background: linear-gradient(90deg, #F8FAFC 0%, var(--ztsdx-cyan) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .section-title { font-size: 2.5rem; font-weight: 700; color: var(--text-primary); margin-bottom: 20px; text-align: center; }
        .section-subtitle { font-size: 1.15rem; color: var(--text-secondary); text-align: center; max-width: 700px; margin: 0 auto 60px; line-height: 1.6; }
        
        /* Grids */
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; }
        
        /* Cards */
        .feature-card { background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); padding: 35px; border-radius: 16px; transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .feature-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,240,255,0.1); border-color: var(--ztsdx-cyan); }
        .feature-icon { font-size: 2.5rem; margin-bottom: 20px; }
        .feature-title { font-size: 1.3rem; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; }
        .feature-desc { font-size: 0.95rem; color: var(--text-secondary); line-height: 1.6; }

        .problem-card { border-left: 4px solid #ff4d4f; background: rgba(255,77,79,0.03); }
      </style>

      <div class="landing-page fade-in">
        
        <!-- TOP NAVIGATION -->
        <nav class="landing-nav" id="landing-navbar">
            <div class="nav-logo">ZT-SDX</div>
            <div class="nav-actions">
                <button class="btn btn-secondary" onclick="window.location.hash='#login'">Sign In</button>
                <button class="btn btn-primary" onclick="window.location.hash='#signup'">Register Organization</button>
            </div>
        </nav>

        <!-- 1. HERO -->
        <section class="landing-section" style="text-align: center; padding-top: 100px; padding-bottom: 80px;">
          <h1 class="hero-title">Secure Your Business,<br>Trust No One.</h1>
          <p style="font-size: 1.25rem; color: var(--text-secondary); max-width: 650px; margin: 0 auto 40px; line-height: 1.6;">
            Zero-Trust Document Exchange. Enterprise-grade security built for MSMEs. Every file is encrypted, every access is audited.
          </p>
        </section>

        <!-- 2. THE PROBLEM -->
        <section class="landing-section" style="background: rgba(255,255,255,0.01); border-top: 1px solid var(--border-subtle); border-bottom: 1px solid var(--border-subtle);">
          <h2 class="section-title">The Hidden Costs of Sharing</h2>
          <p class="section-subtitle">Unsecured sharing over email and WhatsApp exposes your business to massive risks.</p>
          
          <div class="grid-3">
            <div class="feature-card problem-card">
              <div class="feature-icon">💸</div>
              <h3 class="feature-title">Financial Loss</h3>
              <p class="feature-desc">A single data breach costs an average of <strong>$120K for SMBs</strong>. The damage goes beyond immediate fines.</p>
            </div>
            <div class="feature-card problem-card">
              <div class="feature-icon">👻</div>
              <h3 class="feature-title">No Audit Trail</h3>
              <p class="feature-desc">When a leak happens, there's absolutely no way to prove who accessed what, when, or from where.</p>
            </div>
            <div class="feature-card problem-card">
              <div class="feature-icon">🚧</div>
              <h3 class="feature-title">Static Controls</h3>
              <p class="feature-desc">Passwords are easily stolen. Legacy systems never adapt to changing user risk or suspicious device behavior.</p>
            </div>
          </div>
        </section>

        <!-- 3. THE SOLUTION -->
        <section class="landing-section">
          <h2 class="section-title">Why ZT-SDX Wins</h2>
          <p class="section-subtitle">We bridge the gap between weak consumer tools and unaffordable enterprise suites.</p>
          
          <div class="grid-2">
            <div class="feature-card">
              <div class="feature-icon">🛡️</div>
              <h3 class="feature-title">Dynamic Risk-Based Access</h3>
              <p class="feature-desc">Access permissions adapt in real-time based on live user behavior, location, and device trust.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">📜</div>
              <h3 class="feature-title">Tamper-Proof Audit Logs</h3>
              <p class="feature-desc">Every action is recorded using hash-chain integrity. Logs are cryptographically secure and immutable.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">🔍</div>
              <h3 class="feature-title">DLP Scanning Engine</h3>
              <p class="feature-desc">Background workers scan sensitive content and quarantine malicious payloads before they are encrypted.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">⏳</div>
              <h3 class="feature-title">Time-Limited Share Tokens</h3>
              <p class="feature-desc">Share files externally with expiring links. Access revokes automatically when the window closes.</p>
            </div>
          </div>
        </section>

        <!-- 4. BOTTOM CTA -->
        <section class="landing-section" style="text-align: center; padding-top: 100px; padding-bottom: 120px; border-top: 1px solid var(--border-subtle);">
          <h2 style="font-size: 3rem; font-weight: 800; color: var(--text-primary); margin-bottom: 20px;">Built to Scale With You.</h2>
          <p style="font-size: 1.2rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto 40px;">
            Stop gambling with your sensitive data. Deploy your secure workspace today.
          </p>
          <div style="display:flex; gap: 20px; justify-content: center;">
            <button class="btn btn-secondary" onclick="window.location.hash='#login'" style="font-size: 1.2rem; padding: 16px 36px; border-radius: 8px;">Sign In</button>
            <button class="btn btn-primary" onclick="window.location.hash='#signup'" style="font-size: 1.2rem; padding: 16px 36px; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,240,255,0.2);">Register Organization</button>
          </div>
        </section>

      </div>
    `;
  },

  afterRender() {
    const navbar = document.getElementById('landing-navbar');
    if (!navbar) return;

    // Remove existing listener if the page is re-rendered
    if (this._scrollListener) {
        window.removeEventListener('scroll', this._scrollListener);
    }

    this._scrollListener = () => {
        if (!document.body.contains(navbar)) return;
        
        // Fade out navbar after scrolling down 150px
        if (window.scrollY > 150) {
            navbar.classList.add('hidden');
        } else {
            navbar.classList.remove('hidden');
        }
    };

    window.addEventListener('scroll', this._scrollListener);
  },

  // Cleanup when navigating away
  destroy() {
    if (this._scrollListener) {
        window.removeEventListener('scroll', this._scrollListener);
        this._scrollListener = null;
    }
  }
};
