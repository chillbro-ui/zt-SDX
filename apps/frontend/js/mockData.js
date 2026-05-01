// =========================================================================
// ZT-SDX Enterprise — Mock Data Layer
// Simulates API responses and backend databases
// =========================================================================

const MockData = {
  // Currently authenticated user (null if logged out)
  currentUser: null,

  users: [
    { id: 'u1', name: 'Marcus Kane', email: 'ciso@ztsdx.io', role: 'SUPER_ADMIN', department: 'Executive', clearance: 5, deviceTrust: 98, riskScore: 5 },
    { id: 'u2', name: 'Elena Rostova', email: 'manager@ztsdx.io', role: 'DEPARTMENT_HEAD', department: 'Finance', clearance: 4, deviceTrust: 85, riskScore: 12 },
    { id: 'u3', name: 'James Wilson', email: 'employee@ztsdx.io', role: 'EMPLOYEE', department: 'Engineering', clearance: 3, deviceTrust: 90, riskScore: 8 },
    { id: 'u4', name: 'External Auditor', email: 'audit@partner.com', role: 'VENDOR', department: 'External', clearance: 1, deviceTrust: 50, riskScore: 65 }
  ],

  org: {
    id: 'org_7718',
    name: 'ZT-SDX Corp',
    domain: 'ztsdx.io',
    tier: 'ENTERPRISE',
    policies: {
      requireMfa: true,
      minDeviceTrust: 70,
      sessionTimeout: 60
    }
  },

  // Central initialization method (can pull from localStorage if we want persistence later)
  init() {
    // For demo purposes, we can default to unauthenticated, but setting to Admin is easier for immediate testing.
    // this.currentUser = this.users[0]; // Uncomment to auto-login as SUPER_ADMIN
  },

  // Authenticate user
  login(email, password) {
    // Mock login logic
    const user = this.users.find(u => u.email === email);
    if (user) {
      this.currentUser = user;
      return { success: true, user };
    }
    return { success: false, error: 'Invalid credentials' };
  },

  logout() {
    this.currentUser = null;
  }
};

MockData.init();
