// =========================================================================
// ZT-SDX Enterprise — Routing Engine
// Simple hash-based router for Vanilla JS SPA
// =========================================================================

const Router = {
  routes: {
    // PUBLIC ROUTES
    'home': { layout: 'public', render: () => (window.Home ? window.Home.render() : '<h2>Home Page Missing</h2>'), component: 'Home' },
    'login': { layout: 'public', render: () => (window.Login ? window.Login.render() : '<h2>Login Page Missing</h2>') },
    'activate': { layout: 'public', render: () => '<h2>Employee Activation Placeholder</h2>' },

    // ONBOARDING WIZARD
    'signup': { layout: 'wizard', render: () => (window.Signup ? window.Signup.render() : '<h2>Signup Missing</h2>') },

    // PROTECTED DASHBOARD ROUTES
    'dashboard': { layout: 'dashboard', render: () => (window.Dashboard ? window.Dashboard.render() : '<h2>Dashboard Missing</h2>'), component: 'Dashboard', protected: true },
    'upload': { layout: 'dashboard', render: () => (window.Upload ? window.Upload.render() : '<h2>Upload Missing</h2>'), component: 'Upload', protected: true },
    'files': { layout: 'dashboard', render: () => (window.Files ? window.Files.render() : '<h2>Files Missing</h2>'), component: 'Files', protected: true },
    'shares': { layout: 'dashboard', render: () => (window.Shares ? window.Shares.render() : '<h2>Shares Missing</h2>'), component: 'Shares', protected: true },
    'alerts': { layout: 'dashboard', render: () => (window.Alerts ? window.Alerts.render() : '<h2>Alerts Missing</h2>'), component: 'Alerts', protected: true },
    'audit': { layout: 'dashboard', render: () => (window.Audit ? window.Audit.render() : '<h2>Audit Missing</h2>'), component: 'Audit', protected: true },
    'policies': { layout: 'dashboard', render: () => (window.Policies ? window.Policies.render() : '<h2>Policies Missing</h2>'), component: 'Policies', protected: true },

    // ADMINISTRATION ROUTES
    'admin-users': { layout: 'dashboard', render: () => (window.AdminUsers ? window.AdminUsers.render() : '<h2>Users Missing</h2>'), component: 'AdminUsers', protected: true },
    'admin-org': { layout: 'dashboard', render: () => (window.AdminOrg ? window.AdminOrg.render() : '<h2>Org Settings Missing</h2>'), component: 'AdminOrg', protected: true },
    'analytics': { layout: 'dashboard', render: () => (window.Analytics ? window.Analytics.render() : '<h2>Analytics Missing</h2>'), component: 'Analytics', protected: true },
  },

  init() {
    window.addEventListener('hashchange', () => this.navigate());
    // Auto-navigate on load
    if (!window.location.hash) {
      window.location.hash = '#home';
    } else {
      this.navigate();
    }
  },

  navigate() {
    let path = window.location.hash.substring(1);
    if (!path || !this.routes[path]) path = 'home';
    
    const route = this.routes[path];

    // Auth Guard
    if (route.protected && !window.api.accessToken) {
      console.warn('Unauthorized access attempt to', path);
      window.location.hash = '#login';
      return;
    }

    // Role Guard
    if (route.protected) {
        const userStr = sessionStorage.getItem('current_user');
        const role = userStr ? JSON.parse(userStr).role : 'EMPLOYEE';
        
        // Enforce RBAC rules per documentation
        if (['upload', 'files'].includes(path) && role === 'AUDITOR') {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'shares' && !['SUPER_ADMIN', 'DEPT_HEAD', 'MANAGER', 'EMPLOYEE'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'alerts' && !['SUPER_ADMIN', 'SECURITY_ADMIN'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'audit' && !['SUPER_ADMIN', 'SECURITY_ADMIN', 'AUDITOR'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'policies' && !['SUPER_ADMIN'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'admin-users' && !['SUPER_ADMIN', 'SECURITY_ADMIN', 'DEPT_HEAD'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'admin-org' && !['SUPER_ADMIN'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
        if (path === 'analytics' && !['SUPER_ADMIN', 'SECURITY_ADMIN'].includes(role)) {
             window.location.hash = '#dashboard'; return;
        }
    }

    // Toggle Layouts
    document.getElementById('layout-public').style.display = route.layout === 'public' ? 'block' : 'none';
    document.getElementById('layout-wizard').style.display = route.layout === 'wizard' ? 'flex' : 'none';
    document.getElementById('layout-dashboard').style.display = route.layout === 'dashboard' ? 'flex' : 'none';

    // Render Content
    const targetDiv = document.getElementById(`view-${route.layout}`);
    if (targetDiv) {
      targetDiv.innerHTML = route.render();
      
      // Execute post-render data fetching if component has it
      if (route.component && window[route.component] && window[route.component].afterRender) {
          window[route.component].afterRender();
      }

      // Update topbar title if in dashboard
      if (route.layout === 'dashboard') {
        const title = path.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
        document.getElementById('topbar-title').innerText = title;
        App.updateSidebarActive(path);
      }
    }
  }
};
