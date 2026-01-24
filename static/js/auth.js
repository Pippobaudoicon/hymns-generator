/**
 * Authentication Service
 * Handles login, logout, token storage, and authenticated API calls
 */

const authService = {
    TOKEN_KEY: 'hymns_auth_token',
    USER_KEY: 'hymns_user',

    /**
     * Login with username and password
     */
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Credenziali non valide');
        }

        const data = await response.json();
        this.setToken(data.access_token);
        
        // Fetch user info
        await this.fetchCurrentUser();
        
        return data;
    },

    /**
     * Logout - clear token and user data
     */
    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        window.location.href = '/login';
    },

    /**
     * Get stored token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    /**
     * Set token
     */
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        
        // Check if token is expired (basic check)
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000 > Date.now();
        } catch {
            return false;
        }
    },

    /**
     * Get current user from storage
     */
    getUser() {
        const userStr = localStorage.getItem(this.USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    },

    /**
     * Set user in storage
     */
    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    /**
     * Fetch current user from API
     */
    async fetchCurrentUser() {
        const response = await this.authenticatedFetch('/auth/me');
        if (response.ok) {
            const user = await response.json();
            this.setUser(user);
            return user;
        }
        throw new Error('Failed to fetch user');
    },

    /**
     * Make an authenticated fetch request
     */
    async authenticatedFetch(url, options = {}) {
        const token = this.getToken();
        
        if (!token) {
            this.logout();
            throw new Error('Not authenticated');
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
        };

        // Add JSON content type for POST/PUT/PATCH with body
        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        // If unauthorized, redirect to login
        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }

        return response;
    },

    /**
     * Check if user has a specific role or higher
     */
    hasRole(requiredRole) {
        const user = this.getUser();
        if (!user) return false;

        const roleHierarchy = ['superadmin', 'area_manager', 'stake_manager', 'ward_user'];
        const userRoleIndex = roleHierarchy.indexOf(user.role);
        const requiredRoleIndex = roleHierarchy.indexOf(requiredRole);

        return userRoleIndex !== -1 && userRoleIndex <= requiredRoleIndex;
    },

    /**
     * Check if user has any of the specified roles
     */
    hasAnyRole(roles) {
        const user = this.getUser();
        if (!user) return false;
        return roles.includes(user.role);
    },

    /**
     * Get user initials for avatar
     */
    getUserInitials() {
        const user = this.getUser();
        if (!user) return '?';
        
        if (user.full_name) {
            return user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
        }
        return user.username.slice(0, 2).toUpperCase();
    },

    /**
     * Get role display name in Italian
     */
    getRoleDisplayName(role) {
        const roleNames = {
            'superadmin': 'Super Admin',
            'area_manager': 'Responsabile Area',
            'stake_manager': 'Responsabile Palo',
            'ward_user': 'Utente Rione'
        };
        return roleNames[role] || role;
    }
};

/**
 * Check authentication on page load (for protected pages)
 */
function requireAuth() {
    if (!authService.isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

/**
 * Logout function (can be called from onclick)
 */
function logout() {
    authService.logout();
}
