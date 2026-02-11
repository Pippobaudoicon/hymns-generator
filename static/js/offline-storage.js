/**
 * Offline Storage Manager using IndexedDB
 * Stores hymns data and history for offline access
 */

class OfflineStorageManager {
  constructor() {
    this.dbName = 'HymnsDB';
    this.dbVersion = 1;
    this.db = null;
  }

  /**
   * Initialize IndexedDB
   */
  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('[Offline Storage] Failed to open database:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('[Offline Storage] Database opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Store for hymns data
        if (!db.objectStoreNames.contains('hymns')) {
          const hymnsStore = db.createObjectStore('hymns', { keyPath: 'number' });
          hymnsStore.createIndex('category', 'category', { unique: false });
          hymnsStore.createIndex('title', 'title', { unique: false });
          console.log('[Offline Storage] Created hymns store');
        }

        // Store for ward history
        if (!db.objectStoreNames.contains('history')) {
          const historyStore = db.createObjectStore('history', { keyPath: 'id', autoIncrement: true });
          historyStore.createIndex('ward_id', 'ward_id', { unique: false });
          historyStore.createIndex('date', 'date', { unique: false });
          console.log('[Offline Storage] Created history store');
        }

        // Store for wards
        if (!db.objectStoreNames.contains('wards')) {
          db.createObjectStore('wards', { keyPath: 'id' });
          console.log('[Offline Storage] Created wards store');
        }

        // Store for categories and tags
        if (!db.objectStoreNames.contains('metadata')) {
          db.createObjectStore('metadata', { keyPath: 'key' });
          console.log('[Offline Storage] Created metadata store');
        }
      };
    });
  }

  /**
   * Store hymns in IndexedDB
   */
  async storeHymns(hymns) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['hymns'], 'readwrite');
      const store = transaction.objectStore('hymns');

      let stored = 0;
      hymns.forEach(hymn => {
        // Normalize hymn data - use songNumber if number is not present
        const hymnNumber = hymn.number || hymn.songNumber;
        
        // Ensure hymn has a number field (required for keyPath)
        if (hymn && hymnNumber) {
          // Create normalized hymn object with 'number' field for IndexedDB
          const normalizedHymn = {
            ...hymn,
            number: hymnNumber,
            category: hymn.category || hymn.bookSectionTitle
          };
          
          const request = store.put(normalizedHymn);
          request.onsuccess = () => stored++;
          request.onerror = (e) => {
            console.warn(`[Offline Storage] Failed to store hymn ${hymnNumber}:`, e.target.error);
          };
        } else {
          console.warn('[Offline Storage] Skipping hymn without number:', hymn);
        }
      });

      transaction.oncomplete = () => {
        console.log(`[Offline Storage] Stored ${stored} hymns`);
        resolve(stored);
      };

      transaction.onerror = () => {
        console.error('[Offline Storage] Failed to store hymns:', transaction.error);
        reject(transaction.error);
      };
    });
  }

  /**
   * Get all hymns from IndexedDB
   */
  async getAllHymns() {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['hymns'], 'readonly');
      const store = transaction.objectStore('hymns');
      const request = store.getAll();

      request.onsuccess = () => {
        console.log(`[Offline Storage] Retrieved ${request.result.length} hymns`);
        resolve(request.result);
      };

      request.onerror = () => {
        console.error('[Offline Storage] Failed to get hymns:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get hymns by category
   */
  async getHymnsByCategory(category) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['hymns'], 'readonly');
      const store = transaction.objectStore('hymns');
      const index = store.index('category');
      const request = index.getAll(category);

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Store ward history
   */
  async storeHistory(historyEntry) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['history'], 'readwrite');
      const store = transaction.objectStore('history');
      const request = store.add(historyEntry);

      request.onsuccess = () => {
        console.log('[Offline Storage] Stored history entry');
        resolve(request.result);
      };

      request.onerror = () => {
        console.error('[Offline Storage] Failed to store history:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Store ward metadata (name, etc)
   */
  async storeWardMetadata(wardData) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['wards'], 'readwrite');
      const store = transaction.objectStore('wards');
      const request = store.put(wardData);

      request.onsuccess = () => {
        console.log('[Offline Storage] Stored ward metadata');
        resolve(request.result);
      };

      request.onerror = () => {
        console.error('[Offline Storage] Failed to store ward metadata:', request.error);
        reject(request.error);
      };
    });
  }

  /**
   * Get ward metadata by ID
   */
  async getWardMetadata(wardId) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['wards'], 'readonly');
      const store = transaction.objectStore('wards');
      const request = store.get(wardId);

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get ward history
   */
  async getWardHistory(wardId) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['history'], 'readonly');
      const store = transaction.objectStore('history');
      const index = store.index('ward_id');
      const request = index.getAll(wardId);

      request.onsuccess = () => {
        // Sort by date descending
        const results = request.result.sort((a, b) => new Date(b.date) - new Date(a.date));
        resolve(results);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get all history entries
   */
  async getAllHistory() {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['history'], 'readonly');
      const store = transaction.objectStore('history');
      const request = store.getAll();

      request.onsuccess = () => {
        // Sort by date descending
        const results = request.result.sort((a, b) => new Date(b.date) - new Date(a.date));
        resolve(results);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Store wards
   */
  async storeWards(wards) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['wards'], 'readwrite');
      const store = transaction.objectStore('wards');

      let stored = 0;
      wards.forEach(ward => {
        const request = store.put(ward);
        request.onsuccess = () => stored++;
      });

      transaction.oncomplete = () => {
        console.log(`[Offline Storage] Stored ${stored} wards`);
        resolve(stored);
      };

      transaction.onerror = () => {
        reject(transaction.error);
      };
    });
  }

  /**
   * Get all wards
   */
  async getWards() {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['wards'], 'readonly');
      const store = transaction.objectStore('wards');
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Store metadata (categories, tags, etc.)
   */
  async storeMetadata(key, data) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['metadata'], 'readwrite');
      const store = transaction.objectStore('metadata');
      const request = store.put({ key, data, timestamp: Date.now() });

      request.onsuccess = () => {
        console.log(`[Offline Storage] Stored metadata: ${key}`);
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get metadata
   */
  async getMetadata(key) {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction(['metadata'], 'readonly');
      const store = transaction.objectStore('metadata');
      const request = store.get(key);

      request.onsuccess = () => {
        resolve(request.result ? request.result.data : null);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Clear all offline data
   */
  async clearAll() {
    if (!this.db) await this.init();

    const stores = ['hymns', 'history', 'wards', 'metadata'];
    const promises = stores.map(storeName => {
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.clear();

        request.onsuccess = () => {
          console.log(`[Offline Storage] Cleared ${storeName}`);
          resolve();
        };

        request.onerror = () => reject(request.error);
      });
    });

    return Promise.all(promises);
  }
}

// Initialize and export
const offlineStorage = new OfflineStorageManager();

// Auto-initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    offlineStorage.init().catch(err => {
      console.error('[Offline Storage] Initialization failed:', err);
    });
  });
} else {
  offlineStorage.init().catch(err => {
    console.error('[Offline Storage] Initialization failed:', err);
  });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = offlineStorage;
}