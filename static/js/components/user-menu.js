/**
 * User Menu Component
 * Reusable user menu for all pages
 */

export class UserMenu {
    constructor(container, authService) {
        this.container = container;
        this.authService = authService;
        this.init();
    }

    init() {
        this.createUI();
        this.updateUserInfo();
        this.attachEventListeners();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="user-menu" id="userMenu">
                <button class="user-menu-btn" id="userMenuBtn">
                    <span class="user-avatar" id="userAvatar">?</span>
                    <span class="user-name" id="userName">Utente</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
                <div class="user-dropdown" id="userDropdown">
                    <div class="user-dropdown-header">
                        <div class="user-email" id="userEmail"></div>
                        <div class="user-role" id="userRole"></div>
                    </div>
                    <a href="/admin" class="user-dropdown-item" id="adminLink" style="display: none;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
                        Amministrazione
                    </a>
                    <a href="#" class="user-dropdown-item logout" id="logoutLink">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                            <polyline points="16 17 21 12 16 7"></polyline>
                            <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                        Esci
                    </a>
                </div>
            </div>
        `;

        this.elements = {
            menuBtn: this.container.querySelector('#userMenuBtn'),
            dropdown: this.container.querySelector('#userDropdown'),
            avatar: this.container.querySelector('#userAvatar'),
            userName: this.container.querySelector('#userName'),
            userEmail: this.container.querySelector('#userEmail'),
            userRole: this.container.querySelector('#userRole'),
            adminLink: this.container.querySelector('#adminLink'),
            logoutLink: this.container.querySelector('#logoutLink')
        };
    }

    updateUserInfo() {
        const user = this.authService.getUser();
        if (user) {
            this.elements.avatar.textContent = this.authService.getUserInitials();
            this.elements.userName.textContent = user.full_name || user.username;
            this.elements.userEmail.textContent = user.email || '';
            this.elements.userRole.textContent = this.authService.getRoleDisplayName(user.role);
            
            // Show admin link for managers and superadmins
            if (this.authService.hasAnyRole(['superadmin', 'area_manager', 'stake_manager'])) {
                this.elements.adminLink.style.display = 'flex';
            }
        }
    }

    attachEventListeners() {
        // Toggle dropdown
        this.elements.menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Logout
        this.elements.logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.logout();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.closeDropdown();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeDropdown();
            }
        });
    }

    toggleDropdown() {
        this.elements.dropdown.classList.toggle('show');
    }

    closeDropdown() {
        this.elements.dropdown.classList.remove('show');
    }

    logout() {
        this.authService.logout();
        window.location.href = '/login';
    }

    destroy() {
        this.container.innerHTML = '';
    }
}

export default UserMenu;