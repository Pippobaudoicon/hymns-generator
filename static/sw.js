// Service Worker for Selettore Inni PWA
const CACHE_NAME = 'selettore-inni-v2';
const RUNTIME_CACHE = 'selettore-inni-runtime-v2';
const HYMNS_CACHE = 'selettore-inni-hymns-v2';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/static/index.html',
  '/static/login.html',
  '/static/admin.html',
  '/static/css/styles.css',
  '/static/css/auth.css',
  '/static/css/admin.css',
  '/static/js/app.js',
  '/static/js/auth.js',
  '/static/js/api.js',
  '/static/js/ui.js',
  '/static/js/admin.js',
  '/static/js/pwa.js',
  '/static/js/offline-storage.js',
  '/static/js/offline-sync.js',
  '/static/manifest.json'
];

// Critical API endpoints to cache for offline use
const CRITICAL_API_ENDPOINTS = [
  '/api/v1/categories',
  '/api/v1/tags',
  '/api/v1/stats',
  '/api/v1/wards'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    Promise.all([
      // Cache app shell
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[SW] Precaching app shell');
        return cache.addAll(PRECACHE_ASSETS);
      }),
      // Cache critical API endpoints
      caches.open(HYMNS_CACHE).then((cache) => {
        console.log('[SW] Precaching critical API endpoints');
        return Promise.all(
          CRITICAL_API_ENDPOINTS.map(url =>
            fetch(url)
              .then(response => cache.put(url, response))
              .catch(err => console.log('[SW] Failed to cache:', url, err))
          )
        );
      })
    ]).then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  const validCaches = [CACHE_NAME, RUNTIME_CACHE, HYMNS_CACHE];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => !validCaches.includes(cacheName))
          .map((cacheName) => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - network first, then cache fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // API requests - network first, cache fallback with special handling for hymns
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone the response before caching
          const responseClone = response.clone();
          
          // Determine which cache to use
          const cacheName = url.pathname.includes('/get_hymn') ||
                           url.pathname.includes('/categories') ||
                           url.pathname.includes('/tags') ||
                           url.pathname.includes('/stats') ||
                           url.pathname.includes('/wards')
            ? HYMNS_CACHE
            : RUNTIME_CACHE;
          
          caches.open(cacheName).then((cache) => {
            cache.put(request, responseClone);
          });
          
          return response;
        })
        .catch(() => {
          // If network fails, try cache (check both caches)
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[SW] Serving from cache:', url.pathname);
              return cachedResponse;
            }
            
            // Return offline error response
            return new Response(
              JSON.stringify({
                error: 'Offline - dati non disponibili',
                offline: true,
                message: 'Sei offline. Alcuni dati potrebbero non essere disponibili.'
              }),
              {
                headers: { 'Content-Type': 'application/json' },
                status: 503
              }
            );
          });
        })
    );
    return;
  }

  // Static assets - cache first, network fallback
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(request).then((response) => {
        // Don't cache non-successful responses
        if (!response || response.status !== 200 || response.type === 'error') {
          return response;
        }

        // Clone the response
        const responseClone = response.clone();

        caches.open(RUNTIME_CACHE).then((cache) => {
          cache.put(request, responseClone);
        });

        return response;
      });
    })
  );
});

// Handle messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-hymns') {
    event.waitUntil(
      // Implement sync logic here
      Promise.resolve()
    );
  }
});