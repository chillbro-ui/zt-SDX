// =========================================================================
// ZT-SDX Enterprise — API Client
// All calls go through the gateway-api at port 8000
// =========================================================================

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : `http://${window.location.hostname}:8000`;

const USE_MOCK = false; // Set to true to run fully offline without backend

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.accessToken  = sessionStorage.getItem('access_token');
        this.refreshToken = sessionStorage.getItem('refresh_token');
    }

    setTokens(access, refresh) {
        this.accessToken  = access;
        this.refreshToken = refresh;
        if (access)  sessionStorage.setItem('access_token',  access);
        else         sessionStorage.removeItem('access_token');
        if (refresh) sessionStorage.setItem('refresh_token', refresh);
        else         sessionStorage.removeItem('refresh_token');
    }

    clearTokens() {
        this.setTokens(null, null);
    }

    // ── Core request method ───────────────────────────────────────────────

    async request(endpoint, options = {}) {
        if (USE_MOCK) return this._handleMock(endpoint, options);

        const url = `${this.baseUrl}${endpoint}`;
        const headers = new Headers(options.headers || {});

        if (this.accessToken && !options.noAuth) {
            headers.set('Authorization', `Bearer ${this.accessToken}`);
        }

        // Only set JSON content-type for string bodies (not FormData)
        if (!options.isMultipart && !headers.has('Content-Type') && options.body && typeof options.body === 'string') {
            headers.set('Content-Type', 'application/json');
        }

        const config = { ...options, headers };

        try {
            let response = await fetch(url, config);

            // Auto-refresh on 401
            if (response.status === 401 && this.refreshToken && !options._retry) {
                const refreshed = await this._refreshTokens();
                if (refreshed) {
                    config._retry = true;
                    headers.set('Authorization', `Bearer ${this.accessToken}`);
                    response = await fetch(url, config);
                } else {
                    this.clearTokens();
                    window.dispatchEvent(new CustomEvent('auth-expired'));
                    throw new Error('Session expired. Please log in again.');
                }
            }

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                const msg = err.detail || `HTTP ${response.status}`;
                throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
            }

            return response.status !== 204 ? await response.json() : null;
        } catch (error) {
            console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, error);
            throw error;
        }
    }

    async _refreshTokens() {
        try {
            const response = await fetch(`${this.baseUrl}/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });
            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access_token, data.refresh_token);
                return true;
            }
            return false;
        } catch { return false; }
    }

    // ── Auth ──────────────────────────────────────────────────────────────

    async login(email, password, deviceFingerprint = null) {
        // Gateway /login expects a JSON body (LoginRequest Pydantic model)
        const data = await this.request('/login', {
            method: 'POST',
            noAuth: true,
            body: JSON.stringify({
                email,
                password,
                device_fingerprint: deviceFingerprint || null
            })
        });
        this.setTokens(data.access_token, data.refresh_token);
        return data;
    }

    async verifyOtp(challengeId, otp) {
        // Gateway /verify-otp expects a JSON body (VerifyOtpRequest)
        const data = await this.request('/verify-otp', {
            method: 'POST',
            noAuth: true,
            body: JSON.stringify({ challenge_id: challengeId, otp })
        });
        this.setTokens(data.access_token, data.refresh_token);
        return data;
    }

    async register(email, password) {
        // /auth/register is on auth-service directly (not exposed on gateway)
        // It returns { id, email, role, status } — no tokens
        // We call it then immediately login to get tokens
        const AUTH_URL = this.baseUrl.replace(':8000', ':8001');
        const params = new URLSearchParams({ email, password, role: 'SUPER_ADMIN', department: 'IT Security' });
        const response = await fetch(`${AUTH_URL}/auth/register?${params}`, { method: 'POST' });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            const msg = err.detail || `Registration failed (HTTP ${response.status})`;
            throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
        }
        // Registration succeeded — now login to get tokens
        return this.login(email, password, null);
    }

    logout() {
        return this.request('/logout', { method: 'POST' }).finally(() => this.clearTokens());
    }

    getMe() {
        return this.request('/me');
    }

    // ── Provisioning ──────────────────────────────────────────────────────

    provision(orgId, email, roleName, departmentName) {
        return this.request('/provision', {
            method: 'POST',
            body: JSON.stringify({ org_id: orgId, email, role_name: roleName, department_name: departmentName })
        });
    }

    activate(activationCode, password) {
        return this.request('/activate', {
            method: 'POST',
            noAuth: true,
            body: JSON.stringify({ activation_code: activationCode, password })
        });
    }

    // ── Files ─────────────────────────────────────────────────────────────

    async uploadFile(file, sensitivity = 'INTERNAL') {
        const formData = new FormData();
        formData.append('file', file);
        return this.request(`/upload?sensitivity=${sensitivity}`, {
            method: 'POST',
            body: formData,
            isMultipart: true
        });
    }

    getFiles() {
        return this.request('/files');
    }

    getFileDetails(fileId) {
        return this.request(`/files/${fileId}`);
    }

    async getFileDownloadUrl(fileId) {
        // Gateway streams the file directly — open in new tab
        return { download_url: `${this.baseUrl}/files/${fileId}/download?token=${this.accessToken}` };
    }

    deleteFile(fileId) {
        return this.request(`/files/${fileId}`, { method: 'DELETE' });
    }

    updateFileStatus(fileId, status) {
        // Internal endpoint on file-service via gateway — patch risk/status
        return this.request(`/files/${fileId}/risk?risk_score=0&status=${status}`, { method: 'PATCH' });
    }

    // ── Users ─────────────────────────────────────────────────────────────

    getUsers() {
        // Gateway doesn't expose /users directly — call auth-service via provision list
        // We return the current user's org users via /me and provision endpoint
        // For now, return a wrapped response from the auth-service directly
        return fetch(`http://localhost:8001/auth/users`, {
            headers: { Authorization: `Bearer ${this.accessToken}` }
        }).then(r => r.json()).catch(() => ({ users: [] }));
    }

    updateUserRole(userId, newRole) {
        // Not exposed on gateway — call auth-service directly
        return fetch(`http://localhost:8001/auth/users/${userId}/role`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${this.accessToken}`
            },
            body: JSON.stringify({ role: newRole })
        }).then(r => r.json());
    }

    provisionUser(email, role, orgId = null, departmentName = 'General') {
        return this.request('/provision', {
            method: 'POST',
            body: JSON.stringify({
                org_id: orgId || '',
                email,
                role_name: role,
                department_name: departmentName
            })
        });
    }

    // ── Shares ────────────────────────────────────────────────────────────

    createShare(fileId, recipientEmail, options = {}) {
        return this.request('/shares', {
            method: 'POST',
            body: JSON.stringify({
                file_id: fileId,
                recipient_email: recipientEmail,
                expiry_hours: options.expiry_hours || 24,
                max_downloads: options.max_downloads || 1,
                device_lock: options.device_lock || false,
                watermark: options.watermark !== false
            })
        });
    }

    getShares() {
        // Gateway doesn't have a GET /shares — call file-service directly
        return fetch(`http://localhost:8003/files/shares`, {
            headers: { Authorization: `Bearer ${this.accessToken}` }
        }).then(r => r.json()).catch(() => ({ shares: [] }));
    }

    downloadSharedFile(shareToken) {
        return this.request(`/shares/${shareToken}`, { noAuth: true });
    }

    revokeShare(shareId) {
        return this.request(`/shares/${shareId}`, { method: 'DELETE' });
    }

    // ── Audit ─────────────────────────────────────────────────────────────

    getAuditEvents(limit = 100, offset = 0) {
        return this.request(`/audit/events?limit=${limit}&offset=${offset}`);
    }

    verifyAudit() {
        return this.request('/audit/verify');
    }

    // ── Alerts ────────────────────────────────────────────────────────────

    getAlerts(limit = 100, offset = 0) {
        return this.request(`/alerts?limit=${limit}&offset=${offset}`);
    }

    getRiskAlerts(limit = 50) {
        return this.request(`/risk/alerts?limit=${limit}`);
    }

    getUserRiskProfile(userId) {
        return this.request(`/risk/user/${userId}`);
    }

    // ── Organizations ─────────────────────────────────────────────────────

    createOrg(orgData) {
        return this.request('/orgs', {
            method: 'POST',
            body: JSON.stringify(orgData)
        });
    }

    getOrgs() {
        return this.request('/orgs');
    }

    getOrgDetails(orgId) {
        return this.request(`/orgs/${orgId}`);
    }

    getOrgDepartments(orgId) {
        return this.request(`/orgs/${orgId}/departments`);
    }

    addOrgDepartment(orgId, name) {
        return this.request(`/orgs/${orgId}/departments`, {
            method: 'POST',
            body: JSON.stringify({ name })
        });
    }

    // ── Policies ──────────────────────────────────────────────────────────

    getPolicies() {
        return fetch(`http://localhost:8002/policy/`, {
            headers: { Authorization: `Bearer ${this.accessToken}` }
        }).then(r => r.json()).catch(() => ({ policies: [] }));
    }

    seedPolicies() {
        return fetch(`http://localhost:8002/policy/seed`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${this.accessToken}` }
        }).then(r => r.json());
    }

    // ── Mock fallback (kept for offline dev) ─────────────────────────────

    async _handleMock(endpoint, options) {
        console.log(`[MOCK] ${options.method || 'GET'} ${endpoint}`);
        await new Promise(r => setTimeout(r, 400));

        let body = {};
        if (options.body && typeof options.body === 'string') {
            try { body = JSON.parse(options.body); } catch(e) {}
        }

        if (endpoint.startsWith('/login') && options.method === 'POST') {
            const mockUser = { id: 'u1', email: body.email || 'admin@zt.dev', role: 'SUPER_ADMIN', department: 'IT', clearance_level: 5 };
            return { access_token: 'mock_token', refresh_token: 'mock_refresh', token_type: 'bearer', expires_in: 900, otp_required: false, risk_score: 0, risk_level: 'LOW', user: mockUser };
        }
        if (endpoint === '/me') return { id: 'u1', email: 'admin@zt.dev', role: 'SUPER_ADMIN', department: 'IT', clearance_level: 5 };
        if (endpoint === '/files') return { files: [] };
        if (endpoint.startsWith('/upload')) return { file: { id: 'f1', filename: 'test.pdf', sha256: 'abc123', status: 'QUARANTINED' }, message: 'Upload successful. DLP scan queued.' };
        if (endpoint === '/alerts') return [];
        if (endpoint.startsWith('/audit')) return [];
        if (endpoint === '/orgs') return { organizations: [] };
        if (endpoint === '/shares') return { shares: [] };
        return { message: 'Mock OK' };
    }
}

// Singleton
window.api = new ApiClient();
