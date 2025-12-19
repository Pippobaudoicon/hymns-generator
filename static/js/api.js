/**
 * API Module - Handles all API calls with authentication
 */

const API_BASE_URL = 'api/v1';

/**
 * Get auth headers from authService
 */
function getAuthHeaders() {
    // authService is loaded globally before this module
    if (typeof authService !== 'undefined' && authService.getToken()) {
        return {
            'Authorization': `Bearer ${authService.getToken()}`
        };
    }
    return {};
}

/**
 * Make authenticated fetch request
 */
async function authenticatedFetch(url, options = {}) {
    const headers = {
        ...options.headers,
        ...getAuthHeaders()
    };
    
    const response = await fetch(url, { ...options, headers });
    
    // If unauthorized, redirect to login
    if (response.status === 401) {
        if (typeof authService !== 'undefined') {
            authService.logout();
        } else {
            window.location.href = '/static/login.html';
        }
        throw new Error('Session expired');
    }
    
    return response;
}

export const api = {
    /**
     * Fetch all wards
     */
    async getWards() {
        const response = await authenticatedFetch(`${API_BASE_URL}/wards`);
        if (!response.ok) {
            throw new Error('Failed to fetch wards');
        }
        return response.json();
    },

    /**
     * Get hymns with smart selection
     */
    async getHymns(wardName, primaDomenica, domenicaFestiva, tipoFestivita) {
        let url;
        
        if (wardName) {
            // Smart selection with ward history
            url = `${API_BASE_URL}/get_hymns_smart?ward_name=${encodeURIComponent(wardName)}&prima_domenica=${primaDomenica}&domenica_festiva=${domenicaFestiva}`;
        } else {
            // Simple random selection without history
            url = `${API_BASE_URL}/get_hymns?prima_domenica=${primaDomenica}&domenica_festiva=${domenicaFestiva}`;
        }
        
        if (domenicaFestiva && tipoFestivita) {
            url += `&tipo_festivita=${tipoFestivita}`;
        }

        const response = await authenticatedFetch(url);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Errore nel recupero degli inni');
        }

        return response.json();
    },

    /**
     * Swap a hymn
     */
    async swapHymn(position, currentHymnNumber, wardName, domenicaFestiva, tipoFestivita, newHymnNumber = null) {
        const response = await authenticatedFetch(`${API_BASE_URL}/swap_hymn`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                position,
                current_hymn_number: currentHymnNumber,
                ward_name: wardName,
                domenica_festiva: domenicaFestiva,
                tipo_festivita: tipoFestivita || null,
                new_hymn_number: newHymnNumber
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Errore nel cambio inno');
        }
        
        return response.json();
    },

    /**
     * Get available hymns for a position
     */
    async getAvailableHymns(position, category, wardName, domenicaFestiva, tipoFestivita) {
        let url = `${API_BASE_URL}/get_available_hymns?position=${position}&category=${encodeURIComponent(category)}&ward_name=${encodeURIComponent(wardName)}`;
        
        if (domenicaFestiva) {
            url += `&domenica_festiva=true`;
            if (tipoFestivita) {
                url += `&tipo_festivita=${tipoFestivita}`;
            }
        }
        
        const response = await authenticatedFetch(url);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Errore nel recupero inni');
        }
        
        return response.json();
    },

    /**
     * Get ward history
     */
    async getWardHistory(wardName, limit = 20) {
        const response = await authenticatedFetch(`${API_BASE_URL}/ward_history/${encodeURIComponent(wardName)}?limit=${limit}`);
        
        if (!response.ok) {
            throw new Error('Errore nel caricamento');
        }
        
        return response.json();
    }
};