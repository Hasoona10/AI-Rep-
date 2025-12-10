/**
 * Dashboard API Client
 */
class DashboardAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
                ...options.headers
            }
        };

        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return response.json();
    }

    // Business data
    async getBusinessData(businessId) {
        return this.request(`/api/dashboard/business/${businessId}`);
    }

    async updateBusinessData(businessId, data) {
        return this.request(`/api/dashboard/business/${businessId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Logs
    async getLogs(businessId, limit = 100) {
        return this.request(`/api/dashboard/logs/${businessId}?limit=${limit}`);
    }

    // Reservations
    async getReservations(businessId) {
        return this.request(`/api/dashboard/reservations/${businessId}`);
    }

    async updateReservation(businessId, reservationId, data) {
        return this.request(`/api/dashboard/reservations/${businessId}/${reservationId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Auth
    async login(email, password) {
        const response = await this.request('/api/dashboard/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (response.token) {
            this.token = response.token;
            localStorage.setItem('auth_token', response.token);
        }
        
        return response;
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }
}

export default DashboardAPI;


