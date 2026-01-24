/**
 * API Module - Handles all API calls with authentication
 */

const API_BASE_URL = '/api/v1';

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
export async function authenticatedFetch(url, options = {}) {
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
     * Fetch all wards (with offline fallback)
     */
    async getWards() {
        try {
            const response = await authenticatedFetch(`${API_BASE_URL}/wards`);
            if (!response.ok) {
                throw new Error('Failed to fetch wards');
            }
            const wards = await response.json();
            
            // Store in IndexedDB for offline use
            if (typeof offlineStorage !== 'undefined') {
                offlineStorage.storeWards(wards).catch(err =>
                    console.warn('Failed to cache wards:', err)
                );
            }
            
            return wards;
        } catch (error) {
            // Try offline storage if network fails
            if (!navigator.onLine && typeof offlineStorage !== 'undefined') {
                console.log('[API] Offline: Loading wards from IndexedDB');
                const cachedWards = await offlineStorage.getWards();
                if (cachedWards && cachedWards.length > 0) {
                    return cachedWards;
                }
            }
            throw error;
        }
    },

    /**
     * Get hymns with smart selection (with offline fallback)
     */
    async getHymns(wardId, primaDomenica, domenicaFestiva, tipoFestivita) {
        let url;
        
        if (wardId) {
            // Smart selection with ward history (prefer id)
            url = `${API_BASE_URL}/get_hymns_smart?ward_id=${encodeURIComponent(wardId)}&prima_domenica=${primaDomenica}&domenica_festiva=${domenicaFestiva}`;
        } else {
            // Simple random selection without history
            url = `${API_BASE_URL}/get_hymns?prima_domenica=${primaDomenica}&domenica_festiva=${domenicaFestiva}`;
        }
        
        if (domenicaFestiva && tipoFestivita) {
            url += `&tipo_festivita=${tipoFestivita}`;
        }

        try {
            const response = await authenticatedFetch(url);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Errore nel recupero degli inni');
            }

            const data = await response.json();
            
            // Store hymns in IndexedDB for offline use
            if (typeof offlineStorage !== 'undefined' && data.hymns) {
                offlineStorage.storeHymns(data.hymns).catch(err =>
                    console.warn('Failed to cache hymns:', err)
                );
            }
            
            return data;
        } catch (error) {
            // Try offline storage if network fails
            if (!navigator.onLine && typeof offlineStorage !== 'undefined') {
                console.log('[API] Offline: Generating hymns from IndexedDB');
                return this.getOfflineHymns(primaDomenica, domenicaFestiva, tipoFestivita);
            }
            throw error;
        }
    },

    /**
     * Generate hymns offline from cached data
     */
    async getOfflineHymns(primaDomenica, domenicaFestiva, tipoFestivita) {
        if (typeof offlineStorage === 'undefined') {
            throw new Error('Offline storage not available');
        }

        const allHymns = await offlineStorage.getAllHymns();
        
        if (!allHymns || allHymns.length === 0) {
            throw new Error('Nessun inno disponibile offline. Sincronizza i dati quando sei online.');
        }

        // Simple random selection from cached hymns
        const shuffled = allHymns.sort(() => 0.5 - Math.random());
        const selected = shuffled.slice(0, 3);

        return {
            hymns: selected,
            offline: true,
            message: 'Inni selezionati dalla cache offline'
        };
    },

    /**
     * Swap a hymn
     */
    async swapHymn(position, currentHymnNumber, wardId, domenicaFestiva, tipoFestivita, newHymnNumber = null) {
        const response = await authenticatedFetch(`${API_BASE_URL}/swap_hymn`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                position,
                current_hymn_number: currentHymnNumber,
                ward_id: wardId,
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
    async getAvailableHymns(position, category, wardId, domenicaFestiva, tipoFestivita) {
        let url = `${API_BASE_URL}/get_available_hymns?position=${position}&category=${encodeURIComponent(category)}&ward_id=${encodeURIComponent(wardId)}`;
        
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
     * Get ward history (with offline fallback)
     */
    async getWardHistory(wardId, limit = 20) {
        try {
            const response = await authenticatedFetch(`${API_BASE_URL}/ward_history/${encodeURIComponent(wardId)}?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error('Errore nel caricamento');
            }
            
            const data = await response.json();
            
            // Store in IndexedDB for offline use
            if (typeof offlineStorage !== 'undefined' && data.history && data.history.length > 0) {
                // Store ward metadata
                offlineStorage.storeWardMetadata({
                    id: wardId,
                    name: data.ward_name
                }).catch(err => console.warn('Failed to cache ward metadata:', err));
                
                for (const entry of data.history) {
                    offlineStorage.storeHistory({
                        ward_id: wardId,
                        date: entry.date,
                        hymns: entry.hymns,
                        prima_domenica: entry.prima_domenica,
                        domenica_festiva: entry.domenica_festiva,
                        tipo_festivita: entry.tipo_festivita
                    }).catch(err => console.warn('Failed to cache history entry:', err));
                }
            }
            
            return data;
        } catch (error) {
            // Try offline storage if network fails
            if (!navigator.onLine && typeof offlineStorage !== 'undefined') {
                console.log('[API] Offline: Loading history from IndexedDB');
                const cachedHistory = await offlineStorage.getWardHistory(wardId);
                if (cachedHistory && cachedHistory.length > 0) {
                    // Try to get ward name from cache
                    let wardName = 'Rione';
                    try {
                        const wardMetadata = await offlineStorage.getWardMetadata(wardId);
                        if (wardMetadata) {
                            wardName = wardMetadata.name;
                        }
                    } catch (e) {
                        console.warn('Could not retrieve cached ward name:', e);
                    }
                    
                    // Transform to match API format
                    return {
                        ward_id: wardId,
                        ward_name: wardName,
                        history: cachedHistory.map(entry => ({
                            date: entry.date,
                            hymns: entry.hymns,
                            prima_domenica: entry.prima_domenica,
                            domenica_festiva: entry.domenica_festiva,
                            tipo_festivita: entry.tipo_festivita
                        })),
                        total_selections: cachedHistory.length
                    };
                }
            }
            throw error;
        }
    },

    /**
     * Delete a ward selection from history
     */
    async deleteWardSelection(wardId, selectionDate) {
        const response = await authenticatedFetch(`${API_BASE_URL}/ward_history/${encodeURIComponent(wardId)}?selection_date=${selectionDate}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Errore durante l\'eliminazione');
        }
        
        return response.json();
    }
};