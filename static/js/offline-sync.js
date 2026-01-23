/**
 * Offline Sync Manager
 * Pre-caches hymns data for offline availability
 */

class OfflineSyncManager {
  constructor() {
    this.isSyncing = false;
    this.lastSyncTime = this.getLastSyncTime();
  }

  /**
   * Get the last sync timestamp from localStorage
   */
  getLastSyncTime() {
    const stored = localStorage.getItem('hymns_last_sync');
    return stored ? new Date(stored) : null;
  }

  /**
   * Set the last sync timestamp
   */
  setLastSyncTime() {
    localStorage.setItem('hymns_last_sync', new Date().toISOString());
    this.lastSyncTime = new Date();
  }

  /**
   * Check if sync is needed (once per day)
   */
  needsSync() {
    if (!this.lastSyncTime) return true;
    
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    return this.lastSyncTime < oneDayAgo;
  }

  /**
   * Pre-cache critical hymns data for offline use
   */
  async syncHymnsData() {
    if (this.isSyncing) {
      console.log('[Offline Sync] Sync already in progress');
      return;
    }

    if (!this.needsSync()) {
      console.log('[Offline Sync] Sync not needed yet');
      return;
    }

    this.isSyncing = true;
    console.log('[Offline Sync] Starting hymns data sync...');

    try {
      // Endpoints to pre-cache
      const endpoints = [
        '/api/v1/categories',
        '/api/v1/tags',
        '/api/v1/stats',
        '/api/v1/wards'
      ];

      // Fetch all endpoints to populate cache
      const promises = endpoints.map(endpoint =>
        fetch(endpoint)
          .then(response => {
            if (response.ok) {
              console.log(`[Offline Sync] Cached: ${endpoint}`);
              return response.json();
            }
            throw new Error(`Failed to fetch ${endpoint}`);
          })
          .catch(err => {
            console.warn(`[Offline Sync] Failed to cache ${endpoint}:`, err);
          })
      );

      await Promise.all(promises);

      // Also pre-cache some common hymn requests
      await this.cacheCommonHymnRequests();

      this.setLastSyncTime();
      console.log('[Offline Sync] Sync completed successfully');
      
      // Notify user
      this.showSyncNotification('success');
      
    } catch (error) {
      console.error('[Offline Sync] Sync failed:', error);
      this.showSyncNotification('error');
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Cache common hymn selection requests
   */
  async cacheCommonHymnRequests() {
    try {
      // Get a basic hymn selection to populate cache
      const basicRequests = [
        '/api/v1/get_hymns?prima_domenica=false&domenica_festiva=false',
        '/api/v1/get_hymns?prima_domenica=true&domenica_festiva=false'
      ];

      for (const url of basicRequests) {
        try {
          const response = await fetch(url);
          if (response.ok) {
            await response.json();
            console.log(`[Offline Sync] Cached hymn request: ${url}`);
          }
        } catch (err) {
          console.warn(`[Offline Sync] Failed to cache: ${url}`, err);
        }
      }
    } catch (error) {
      console.warn('[Offline Sync] Failed to cache common requests:', error);
    }
  }

  /**
   * Show sync notification to user
   */
  showSyncNotification(status) {
    // Only show if there's a notification container
    const container = document.getElementById('sync-notification');
    if (!container) return;

    const message = status === 'success' 
      ? '✓ Dati sincronizzati per uso offline'
      : '⚠ Sincronizzazione fallita';

    container.textContent = message;
    container.className = `sync-notification ${status}`;
    container.style.display = 'block';

    // Hide after 3 seconds
    setTimeout(() => {
      container.style.display = 'none';
    }, 3000);
  }

  /**
   * Force sync now
   */
  async forceSyncNow() {
    this.lastSyncTime = null;
    await this.syncHymnsData();
  }

  /**
   * Clear offline cache
   */
  async clearOfflineCache() {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      const hymnsCaches = cacheNames.filter(name => 
        name.includes('hymns') || name.includes('runtime')
      );
      
      for (const cacheName of hymnsCaches) {
        await caches.delete(cacheName);
        console.log(`[Offline Sync] Cleared cache: ${cacheName}`);
      }
      
      localStorage.removeItem('hymns_last_sync');
      this.lastSyncTime = null;
      
      console.log('[Offline Sync] Offline cache cleared');
    }
  }

  /**
   * Get cache status information
   */
  async getCacheStatus() {
    if (!('caches' in window)) {
      return { supported: false };
    }

    try {
      const cacheNames = await caches.keys();
      const hymnsCache = cacheNames.find(name => name.includes('hymns'));
      
      if (!hymnsCache) {
        return { 
          supported: true, 
          cached: false,
          lastSync: this.lastSyncTime
        };
      }

      const cache = await caches.open(hymnsCache);
      const keys = await cache.keys();
      
      return {
        supported: true,
        cached: true,
        itemCount: keys.length,
        lastSync: this.lastSyncTime,
        cacheName: hymnsCache
      };
    } catch (error) {
      console.error('[Offline Sync] Error getting cache status:', error);
      return { supported: true, cached: false, error: error.message };
    }
  }
}

// Initialize offline sync manager
const offlineSyncManager = new OfflineSyncManager();

// Auto-sync on page load (after a short delay to not block initial render)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => offlineSyncManager.syncHymnsData(), 2000);
  });
} else {
  setTimeout(() => offlineSyncManager.syncHymnsData(), 2000);
}

// Sync when coming back online
window.addEventListener('online', () => {
  console.log('[Offline Sync] Network restored, syncing...');
  offlineSyncManager.syncHymnsData();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = offlineSyncManager;
}