# Offline Functionality Guide

This document explains how the offline functionality works in the Selettore Inni PWA.

## Overview

The application now supports full offline functionality, allowing users to:
- Access the app without internet connection
- View previously loaded hymns data
- Use core features offline
- Automatically sync when connection is restored

## How It Works

### 1. Service Worker Caching

The service worker ([`static/sw.js`](../static/sw.js)) implements a multi-tier caching strategy:

#### **App Shell Cache** (`selettore-inni-v1`)
Precached on installation:
- HTML pages (index, login, admin)
- CSS stylesheets
- JavaScript files
- PWA manifest

#### **Hymns Data Cache** (`selettore-inni-hymns-v1`)
Cached on first use and periodically synced:
- `/api/v1/categories` - Hymn categories
- `/api/v1/tags` - Hymn tags
- `/api/v1/stats` - Collection statistics
- `/api/v1/wards` - Ward information
- Hymn selection requests

#### **Runtime Cache** (`selettore-inni-runtime-v1`)
Dynamically cached:
- API responses
- User-specific data
- Additional resources

### 2. Offline Sync Manager

The offline sync manager ([`static/js/offline-sync.js`](../static/js/offline-sync.js)) handles:

#### **Automatic Syncing**
- Runs on page load (after 2 seconds)
- Syncs once per day automatically
- Syncs when network is restored

#### **Pre-caching Strategy**
```javascript
// Critical endpoints cached immediately
const endpoints = [
  '/api/v1/categories',
  '/api/v1/tags',
  '/api/v1/stats',
  '/api/v1/wards'
];

// Common hymn requests also cached
const commonRequests = [
  '/api/v1/get_hymns?prima_domenica=false',
  '/api/v1/get_hymns?prima_domenica=true'
];
```

### 3. Network Strategies

#### **API Requests: Network First, Cache Fallback**
```
1. Try network request
2. If successful, cache response
3. If network fails, serve from cache
4. If no cache, return offline error
```

#### **Static Assets: Cache First, Network Fallback**
```
1. Check cache first
2. If found, serve immediately
3. If not cached, fetch from network
4. Cache for future use
```

## User Experience

### Offline Indicator

When offline, a banner appears at the top:
```
⚠️ Modalità Offline - Alcuni dati potrebbero non essere aggiornati
```

### Sync Notifications

After successful sync:
```
✓ Dati sincronizzati per uso offline
```

### Offline Behavior

**What Works Offline:**
- ✅ View app interface
- ✅ Access previously loaded hymns
- ✅ View cached ward information
- ✅ Browse categories and tags
- ✅ Use basic navigation

**What Requires Connection:**
- ❌ Login/authentication
- ❌ New hymn selections (not previously cached)
- ❌ Admin panel operations
- ❌ Real-time data updates

## Implementation Details

### Service Worker Registration

```javascript
// Automatic registration in pwa.js
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js', {
    scope: '/'
  });
}
```

### Cache Management

```javascript
// Check cache status
const status = await offlineSyncManager.getCacheStatus();
console.log(status);
// {
//   supported: true,
//   cached: true,
//   itemCount: 15,
//   lastSync: "2024-01-23T10:00:00.000Z"
// }

// Force sync now
await offlineSyncManager.forceSyncNow();

// Clear offline cache
await offlineSyncManager.clearOfflineCache();
```

### Offline Detection

```javascript
// Listen for online/offline events
window.addEventListener('online', () => {
  console.log('Network restored');
  offlineSyncManager.syncHymnsData();
});

window.addEventListener('offline', () => {
  console.log('Network lost');
  // Show offline indicator
});

// Check current status
if (navigator.onLine) {
  console.log('Online');
} else {
  console.log('Offline');
}
```

## Configuration

### Sync Frequency

Edit [`static/js/offline-sync.js`](../static/js/offline-sync.js):

```javascript
needsSync() {
  if (!this.lastSyncTime) return true;
  
  // Change sync interval (default: 1 day)
  const oneDayAgo = new Date();
  oneDayAgo.setDate(oneDayAgo.getDate() - 1); // Change -1 to desired days
  
  return this.lastSyncTime < oneDayAgo;
}
```

### Cache Version

Update cache version to force refresh:

```javascript
// In static/sw.js
const CACHE_NAME = 'selettore-inni-v2'; // Increment version
const HYMNS_CACHE = 'selettore-inni-hymns-v2';
```

### Additional Endpoints

Add more endpoints to pre-cache:

```javascript
// In static/sw.js
const CRITICAL_API_ENDPOINTS = [
  '/api/v1/categories',
  '/api/v1/tags',
  '/api/v1/stats',
  '/api/v1/wards',
  '/api/v1/your-new-endpoint' // Add here
];
```

## Testing Offline Functionality

### Chrome DevTools

1. Open DevTools (F12)
2. Go to **Network** tab
3. Check **Offline** checkbox
4. Reload page
5. Verify app still works

### Service Worker Testing

1. Open DevTools (F12)
2. Go to **Application** tab
3. Click **Service Workers**
4. Check "Offline" checkbox
5. Test functionality

### Cache Inspection

1. Open DevTools (F12)
2. Go to **Application** tab
3. Expand **Cache Storage**
4. View cached files in each cache

## Troubleshooting

### Cache Not Working

**Problem:** Offline mode doesn't work

**Solutions:**
1. Check service worker is registered:
   ```javascript
   navigator.serviceWorker.getRegistration().then(reg => {
     console.log('SW:', reg);
   });
   ```

2. Verify cache exists:
   ```javascript
   caches.keys().then(names => {
     console.log('Caches:', names);
   });
   ```

3. Clear and re-sync:
   ```javascript
   await offlineSyncManager.clearOfflineCache();
   await offlineSyncManager.forceSyncNow();
   ```

### Stale Data

**Problem:** Offline data is outdated

**Solutions:**
1. Force sync manually:
   ```javascript
   await offlineSyncManager.forceSyncNow();
   ```

2. Clear cache and reload:
   ```javascript
   await offlineSyncManager.clearOfflineCache();
   location.reload();
   ```

### Sync Not Running

**Problem:** Automatic sync doesn't happen

**Solutions:**
1. Check last sync time:
   ```javascript
   const status = await offlineSyncManager.getCacheStatus();
   console.log('Last sync:', status.lastSync);
   ```

2. Manually trigger sync:
   ```javascript
   await offlineSyncManager.syncHymnsData();
   ```

## Best Practices

### For Users

1. **First Use**: Use the app online first to populate cache
2. **Regular Sync**: Open app regularly while online to keep data fresh
3. **Offline Limitations**: Be aware some features require connection
4. **Storage**: Keep sufficient device storage for cache

### For Developers

1. **Cache Size**: Monitor cache size, don't cache too much
2. **Version Control**: Update cache version with each deployment
3. **Testing**: Always test offline functionality before deploying
4. **Error Handling**: Provide clear offline error messages
5. **Sync Strategy**: Balance between freshness and offline availability

## Performance Considerations

### Cache Size

Current cache sizes (approximate):
- App Shell: ~500 KB
- Hymns Data: ~2-5 MB
- Runtime Cache: Variable (up to 50 MB)

### Network Usage

- Initial sync: ~5 MB
- Daily sync: ~1-2 MB (only changed data)
- Background sync: Minimal

### Storage Limits

Browser storage limits:
- Chrome: ~60% of available disk space
- Firefox: ~50% of available disk space
- Safari: ~1 GB per origin

## Future Enhancements

Potential improvements:
- [ ] Background sync for offline actions
- [ ] Selective sync (user chooses what to cache)
- [ ] Compression for cached data
- [ ] Periodic background sync
- [ ] Offline queue for pending actions
- [ ] Smart cache eviction based on usage

## Resources

- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Cache API](https://developer.mozilla.org/en-US/docs/Web/API/Cache)
- [Offline Web Applications](https://web.dev/offline-cookbook/)
- [PWA Offline Patterns](https://developers.google.com/web/fundamentals/instant-and-offline/offline-cookbook)