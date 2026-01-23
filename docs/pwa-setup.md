# Progressive Web App (PWA) Setup Guide

This document explains the PWA implementation for the Selettore Inni application.

## Overview

The application has been configured as a Progressive Web App (PWA), enabling:
- **Installability**: Users can install the app on their devices
- **Offline functionality**: Core features work without internet connection
- **App-like experience**: Runs in standalone mode without browser UI
- **Fast loading**: Assets are cached for instant loading
- **Auto-updates**: New versions are automatically detected and applied

## Components

### 1. Web App Manifest (`static/manifest.json`)

Defines the app's metadata and appearance:
- **Name**: "Selettore Inni - Chiesa di Gesù Cristo"
- **Short name**: "Selettore Inni"
- **Display mode**: Standalone (full-screen, no browser UI)
- **Theme color**: #003f87 (church blue)
- **Icons**: Multiple sizes for different devices
- **Shortcuts**: Quick access to main features

### 2. Service Worker (`static/sw.js`)

Handles offline functionality and caching:
- **Precaching**: Essential files cached on install
- **Runtime caching**: API responses cached dynamically
- **Network strategies**:
  - Static assets: Cache-first
  - API calls: Network-first with cache fallback
- **Auto-updates**: Detects and applies new versions

### 3. PWA Manager (`static/js/pwa.js`)

JavaScript class managing PWA features:
- Service worker registration
- Install prompt handling
- Update notifications
- Cache management

## Installation

### For Users

#### Android (Chrome/Edge)
1. Open the app in Chrome or Edge
2. Tap the menu (⋮) → "Install app" or "Add to Home screen"
3. Follow the prompts
4. App icon appears on home screen

#### iOS (Safari)
1. Open the app in Safari
2. Tap the Share button (□↑)
3. Scroll and tap "Add to Home Screen"
4. Tap "Add"
5. App icon appears on home screen

#### Desktop (Chrome/Edge)
1. Open the app in Chrome or Edge
2. Look for the install icon (⊕) in the address bar
3. Click "Install"
4. App opens in its own window

### For Developers

#### Prerequisites
1. **HTTPS**: Required for service workers (except localhost)
2. **Icons**: Generate all required icon sizes
3. **Valid manifest**: Ensure manifest.json is properly configured

#### Setup Steps

1. **Generate Icons**
   ```bash
   cd static/icons
   # Follow instructions in static/icons/README.md
   ```

2. **Test Locally**
   ```bash
   # Start the development server
   python app.py
   
   # Open in browser
   open http://localhost:8000
   ```

3. **Verify PWA**
   - Open Chrome DevTools (F12)
   - Go to Application tab
   - Check Manifest section
   - Check Service Workers section
   - Run Lighthouse audit (PWA category)

## Features

### Offline Support

The app works offline with cached data:
- **Static assets**: HTML, CSS, JavaScript files
- **API responses**: Recent hymn selections and ward data
- **Graceful degradation**: Shows appropriate messages when offline

### Install Prompt

A floating "Install App" button appears for users who haven't installed:
- Positioned at bottom-right
- Dismissible
- Only shows when installation is available

### Update Notifications

When a new version is available:
- Notification appears at top-right
- User can update immediately or later
- Page reloads after update

### App Shortcuts

Quick actions from the app icon:
1. **Seleziona Inni**: Go to main hymn selector
2. **Amministrazione**: Access admin panel (if authorized)

## Caching Strategy

### Precached Assets (Installed Immediately)
- `/` (root)
- `/static/index.html`
- `/static/login.html`
- `/static/admin.html`
- All CSS files
- All JavaScript files
- Manifest file

### Runtime Cached (Cached on First Use)
- API responses (`/api/*`)
- Additional static assets
- User-specific data

### Cache Invalidation
- Old caches automatically deleted on update
- Manual cache clearing available via PWA manager

## Configuration

### Manifest Settings

Edit `static/manifest.json` to customize:

```json
{
  "name": "Your App Name",
  "short_name": "Short Name",
  "theme_color": "#003f87",
  "background_color": "#ffffff",
  "display": "standalone"
}
```

### Service Worker Settings

Edit `static/sw.js` to customize:

```javascript
const CACHE_NAME = 'selettore-inni-v1'; // Update version to force cache refresh
const PRECACHE_ASSETS = [
  // Add/remove files to precache
];
```

### PWA Manager Settings

The PWA manager automatically handles:
- Service worker registration
- Install prompts
- Update notifications
- Cache management

## Testing

### Local Testing

1. **Service Worker**
   ```javascript
   // Check if service worker is registered
   navigator.serviceWorker.getRegistration().then(reg => {
     console.log('SW registered:', reg);
   });
   ```

2. **Cache**
   ```javascript
   // Check cached files
   caches.keys().then(names => {
     console.log('Cache names:', names);
   });
   ```

3. **Offline Mode**
   - Open DevTools → Network tab
   - Check "Offline" checkbox
   - Reload page and test functionality

### Lighthouse Audit

1. Open Chrome DevTools (F12)
2. Go to Lighthouse tab
3. Select "Progressive Web App" category
4. Click "Generate report"
5. Review and fix any issues

### Mobile Testing

Test on actual devices:
- Android: Chrome, Samsung Internet, Edge
- iOS: Safari
- Desktop: Chrome, Edge, Firefox

## Troubleshooting

### Service Worker Not Registering

**Problem**: Service worker fails to register

**Solutions**:
- Ensure HTTPS (or localhost)
- Check browser console for errors
- Verify `sw.js` path is correct
- Clear browser cache and reload

### Install Prompt Not Showing

**Problem**: Install button doesn't appear

**Solutions**:
- Ensure all PWA criteria are met (Lighthouse audit)
- Check if already installed
- Try different browser
- Verify manifest.json is valid

### Offline Mode Not Working

**Problem**: App doesn't work offline

**Solutions**:
- Check service worker is active
- Verify files are cached (DevTools → Application → Cache Storage)
- Check network strategy in `sw.js`
- Clear cache and reinstall

### Updates Not Applying

**Problem**: New version doesn't load

**Solutions**:
- Increment `CACHE_NAME` in `sw.js`
- Force update: DevTools → Application → Service Workers → Update
- Clear all caches
- Uninstall and reinstall app

## Best Practices

### Development

1. **Version Control**: Update `CACHE_NAME` with each deployment
2. **Testing**: Test offline functionality before deploying
3. **Icons**: Use high-quality, recognizable icons
4. **Performance**: Keep precache list minimal

### Deployment

1. **HTTPS**: Always use HTTPS in production
2. **CDN**: Consider CDN for static assets
3. **Monitoring**: Monitor service worker errors
4. **Updates**: Plan update strategy (immediate vs. on-next-visit)

### User Experience

1. **Install Prompt**: Don't be too aggressive with install prompts
2. **Offline UI**: Show clear offline indicators
3. **Updates**: Notify users of updates but don't force reload
4. **Performance**: Optimize for fast loading

## Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep service worker and PWA libraries updated
2. **Test Across Devices**: Regularly test on different devices/browsers
3. **Monitor Analytics**: Track installation and usage metrics
4. **Update Icons**: Refresh icons if branding changes

### Version Updates

When deploying a new version:

1. Update `CACHE_NAME` in `sw.js`:
   ```javascript
   const CACHE_NAME = 'selettore-inni-v2'; // Increment version
   ```

2. Test locally:
   ```bash
   python app.py
   # Test in browser
   ```

3. Deploy to production

4. Verify update notification appears for existing users

## Resources

### Documentation
- [MDN PWA Guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Google PWA Documentation](https://web.dev/progressive-web-apps/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

### Tools
- [PWA Builder](https://www.pwabuilder.com/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Workbox](https://developers.google.com/web/tools/workbox) (advanced service worker library)

### Testing
- [PWA Testing Checklist](https://web.dev/pwa-checklist/)
- [Can I Use - Service Workers](https://caniuse.com/serviceworkers)

## Support

For issues or questions:
1. Check browser console for errors
2. Run Lighthouse audit
3. Review this documentation
4. Check service worker status in DevTools

## Future Enhancements

Potential improvements:
- [ ] Background sync for offline actions
- [ ] Push notifications for updates
- [ ] Advanced caching strategies
- [ ] Periodic background sync
- [ ] Share target API integration
- [ ] File handling API