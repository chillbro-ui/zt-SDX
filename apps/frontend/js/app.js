// =========================================================================
// ZT-SDX Enterprise — Main App Controller
// =========================================================================

const App = {
  init() {
    // Initialize Routing
    Router.init();
    
    // Setup Theme Toggle
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const isDark = document.body.classList.contains('theme-dark');
        if (isDark) {
          document.body.classList.remove('theme-dark');
          document.body.classList.add('theme-light');
        } else {
          document.body.classList.remove('theme-light');
          document.body.classList.add('theme-dark');
        }
      });
    }

    // For Demo: Auto-login as Super Admin if we hit a protected route directly
    // and aren't logged in (to save time during development)
    if (window.location.hash !== '#home' && window.location.hash !== '#login' && !window.api.accessToken) {
       // MockData.login('ciso@ztsdx.io', 'pass'); // Uncomment to enable auto-login during dev
    }

    // Logout logic
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try { await window.api.logout(); } catch(e) {}
            sessionStorage.removeItem('current_user');
            window.location.hash = '#home';
            window.location.reload();
        });
    }

    this.renderSidebar();
    this.updateUserDropdown();
  },

  renderSidebar() {
    const nav = document.getElementById('sidebar-nav');
    if (!nav) return;

    const userStr = sessionStorage.getItem('current_user');
    const user = userStr ? JSON.parse(userStr) : { role: 'EMPLOYEE' };
    const role = user.role;

    // RBAC Permissions matching hierarchy-and-login-flow.md
    const isPlatformAdmin = role === 'PLATFORM_ADMIN';
    const canSeeFiles = role !== 'AUDITOR' && !isPlatformAdmin;
    const canShare = ['SUPER_ADMIN', 'DEPT_HEAD', 'MANAGER', 'EMPLOYEE'].includes(role) && !isPlatformAdmin;
    const canSeeSecurity = ['SUPER_ADMIN', 'SECURITY_ADMIN', 'AUDITOR'].includes(role) && !isPlatformAdmin;
    const canSeeAdmin = ['SUPER_ADMIN', 'SECURITY_ADMIN', 'DEPT_HEAD'].includes(role) && !isPlatformAdmin;

    // Define sidebar items (Visibility restricted by role)
    const menu = [
      { type: 'divider', label: 'Global Infrastructure', show: isPlatformAdmin },
      { id: 'dashboard', icon: '🌍', label: 'Tenant Registry', show: isPlatformAdmin },
      
      { id: 'dashboard', icon: '📊', label: 'Dashboard', show: !isPlatformAdmin },
      { id: 'upload', icon: '📤', label: 'Upload Data', show: canSeeFiles },
      { id: 'files', icon: '📁', label: 'File Vault', show: canSeeFiles },
      { id: 'shares', icon: '🔗', label: 'Share Centre', show: canShare },
      { type: 'divider', label: 'Security & Compliance', show: canSeeSecurity },
      { id: 'alerts', icon: '🛡️', label: 'Alerts Center', show: ['SUPER_ADMIN', 'SECURITY_ADMIN'].includes(role) },
      { id: 'audit', icon: '📜', label: 'Audit Ledger', show: ['SUPER_ADMIN', 'SECURITY_ADMIN', 'AUDITOR'].includes(role) },
      { id: 'policies', icon: '⚖️', label: 'Policy Studio', show: ['SUPER_ADMIN'].includes(role) },
      { type: 'divider', label: 'Administration', show: canSeeAdmin },
      { id: 'admin-users', icon: '👥', label: 'IAM / Employees', show: ['SUPER_ADMIN', 'SECURITY_ADMIN', 'DEPT_HEAD'].includes(role) },
      { id: 'admin-org', icon: '⚙️', label: 'Org Settings', show: ['SUPER_ADMIN'].includes(role) },
      { id: 'analytics', icon: '📈', label: 'Risk Analytics', show: ['SUPER_ADMIN', 'SECURITY_ADMIN'].includes(role) }
    ];

    let html = '';
    menu.filter(item => item.show).forEach(item => {
      if (item.type === 'divider') {
        html += `<div class="nav-group-label">${item.label}</div>`;
      } else {
        html += `<a href="#${item.id}" data-nav="${item.id}"><span class="icon">${item.icon}</span> ${item.label}</a>`;
      }
    });

    nav.innerHTML = html;
  },

  updateSidebarActive(routePath) {
    const links = document.querySelectorAll('#sidebar-nav a');
    links.forEach(l => l.classList.remove('active'));
    const active = document.querySelector(`#sidebar-nav a[data-nav="${routePath}"]`);
    if (active) active.classList.add('active');
  },

  updateUserDropdown() {
    const userStr = sessionStorage.getItem('current_user');
    if (!userStr) return;
    const user = JSON.parse(userStr);
    
    document.getElementById('user-name').innerText = user.email.split('@')[0];
    document.getElementById('user-role').innerText = user.role.replace('_', ' ');
    document.getElementById('user-avatar').innerText = user.email.charAt(0).toUpperCase();
    document.getElementById('trust-score').innerText = user.trust_score || '100'; // Default score if not set
  }
};

// Boot up
document.addEventListener('DOMContentLoaded', () => {
  // Expose globally
  window.App = App;

  // Handle auto-logout when token expires
  window.addEventListener('auth-expired', () => {
      sessionStorage.removeItem('current_user');
      window.location.hash = '#login';
  });

  App.init();
});
