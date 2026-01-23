// PWA Installation and Service Worker Registration
class PWAManager {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.init();
  }

  init() {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      this.isInstalled = true;
      console.log('[PWA] App is running in standalone mode');
    }

    // Register service worker
    if ('serviceWorker' in navigator) {
      this.registerServiceWorker();
    }

    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('[PWA] Install prompt available');
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });

    // Listen for app installed
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] App installed successfully');
      this.isInstalled = true;
      this.deferredPrompt = null;
      this.hideInstallButton();
    });

    // Check for updates periodically
    if ('serviceWorker' in navigator) {
      setInterval(() => {
        navigator.serviceWorker.getRegistration().then((reg) => {
          if (reg) reg.update();
        });
      }, 60000); // Check every minute
    }
  }

  async registerServiceWorker() {
    try {
      const registration = await navigator.serviceWorker.register('/static/sw.js', {
        scope: '/'
      });

      console.log('[PWA] Service Worker registered:', registration.scope);

      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('[PWA] New service worker found');

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('[PWA] New version available');
            this.showUpdateNotification();
          }
        });
      });

      // Handle controller change
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[PWA] Controller changed, reloading...');
        window.location.reload();
      });

    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }
  }

  showInstallButton() {
    // Create install button if it doesn't exist
    let installBtn = document.getElementById('pwa-install-btn');
    
    if (!installBtn) {
      installBtn = document.createElement('button');
      installBtn.id = 'pwa-install-btn';
      installBtn.className = 'pwa-install-button';
      installBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>Installa App</span>
      `;
      installBtn.onclick = () => this.promptInstall();
      
      // Add to page
      document.body.appendChild(installBtn);
      
      // Add styles if not already present
      if (!document.getElementById('pwa-styles')) {
        const style = document.createElement('style');
        style.id = 'pwa-styles';
        style.textContent = `
          .pwa-install-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #003f87;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 63, 135, 0.3);
            z-index: 1000;
            transition: all 0.3s ease;
          }
          .pwa-install-button:hover {
            background: #002f67;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 63, 135, 0.4);
          }
          .pwa-update-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 2px solid #003f87;
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1001;
            max-width: 300px;
            animation: slideIn 0.3s ease;
          }
          @keyframes slideIn {
            from {
              transform: translateX(400px);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
          .pwa-update-notification h4 {
            margin: 0 0 8px 0;
            color: #003f87;
            font-size: 16px;
          }
          .pwa-update-notification p {
            margin: 0 0 12px 0;
            color: #666;
            font-size: 14px;
          }
          .pwa-update-notification button {
            background: #003f87;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            margin-right: 8px;
          }
          .pwa-update-notification button:hover {
            background: #002f67;
          }
          .pwa-update-notification button.secondary {
            background: transparent;
            color: #003f87;
            border: 1px solid #003f87;
          }
          .pwa-update-notification button.secondary:hover {
            background: #f0f0f0;
          }
        `;
        document.head.appendChild(style);
      }
    }
  }

  hideInstallButton() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.remove();
    }
  }

  async promptInstall() {
    if (!this.deferredPrompt) {
      console.log('[PWA] Install prompt not available');
      return;
    }

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;
    
    console.log('[PWA] User choice:', outcome);
    
    if (outcome === 'accepted') {
      console.log('[PWA] User accepted the install prompt');
    } else {
      console.log('[PWA] User dismissed the install prompt');
    }
    
    this.deferredPrompt = null;
    this.hideInstallButton();
  }

  showUpdateNotification() {
    // Create update notification
    const notification = document.createElement('div');
    notification.className = 'pwa-update-notification';
    notification.innerHTML = `
      <h4>Aggiornamento Disponibile</h4>
      <p>È disponibile una nuova versione dell'app.</p>
      <button onclick="pwaManager.applyUpdate()">Aggiorna Ora</button>
      <button class="secondary" onclick="this.parentElement.remove()">Più Tardi</button>
    `;
    document.body.appendChild(notification);
  }

  applyUpdate() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then((reg) => {
        if (reg && reg.waiting) {
          reg.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
      });
    }
  }

  async clearCache() {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration && registration.active) {
        registration.active.postMessage({ type: 'CLEAR_CACHE' });
      }
    }
  }
}

// Initialize PWA Manager
const pwaManager = new PWAManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = pwaManager;
}