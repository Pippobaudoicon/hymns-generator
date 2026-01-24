/**
 * Dashboard Module
 * Manages the tools dashboard and navigation
 */

/**
 * Tool configuration
 * Each tool has: id, title, description, icon (SVG or emoji), url, badge (optional), disabled (optional)
 * Add new tools to this array to display them on the dashboard
 */
const tools = [
    {
        id: 'hymns-generator',
        title: 'Selettore Inni',
        description: 'Genera selezioni di inni per le riunioni domenicali. Supporta festività, prima domenica del mese e cronologia.',
        icon: 'music', // Can be 'music', 'calendar', 'users', etc. or an emoji like '🎵'
        url: '/hymns',
        badge: null, // Can be 'new', 'beta', 'coming-soon'
        disabled: false,
        // Optional: roles that can access this tool (if not specified, all authenticated users can access)
        // roles: ['superadmin', 'area_manager', 'stake_manager', 'ward_user']
    },
    // Example of future tools (commented out):
    // {
    //     id: 'calendar',
    //     title: 'Calendario Riunioni',
    //     description: 'Gestisci il calendario delle riunioni e degli eventi del rione.',
    //     icon: 'calendar',
    //     url: '/static/calendar.html',
    //     badge: 'coming-soon',
    //     disabled: true,
    // },
    // {
    //     id: 'members',
    //     title: 'Gestione Membri',
    //     description: 'Visualizza e gestisci i membri del rione e le loro chiamate.',
    //     icon: 'users',
    //     url: '/static/members.html',
    //     badge: 'coming-soon',
    //     disabled: true,
    //     roles: ['superadmin', 'area_manager', 'stake_manager']
    // },
];

/**
 * SVG icons for tools
 */
const icons = {
    music: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 18V5l12-2v13"></path>
        <circle cx="6" cy="18" r="3"></circle>
        <circle cx="18" cy="16" r="3"></circle>
    </svg>`,
    calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
        <line x1="16" y1="2" x2="16" y2="6"></line>
        <line x1="8" y1="2" x2="8" y2="6"></line>
        <line x1="3" y1="10" x2="21" y2="10"></line>
    </svg>`,
    users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        <circle cx="9" cy="7" r="4"></circle>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
    </svg>`,
    book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
    </svg>`,
    settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </svg>`,
    clipboard: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
        <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
    </svg>`,
    arrow: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="12" x2="19" y2="12"></line>
        <polyline points="12 5 19 12 12 19"></polyline>
    </svg>`,
};

/**
 * Get icon HTML for a tool
 */
function getIconHtml(iconName) {
    // Check if it's an emoji (starts with a character that's not a letter)
    if (iconName && iconName.length <= 2 && !/^[a-zA-Z]/.test(iconName)) {
        return `<span class="icon-emoji">${iconName}</span>`;
    }
    return icons[iconName] || icons.clipboard;
}

/**
 * Get badge HTML for a tool
 */
function getBadgeHtml(badge) {
    if (!badge) return '';
    
    const badgeLabels = {
        'new': 'Nuovo',
        'beta': 'Beta',
        'coming-soon': 'Prossimamente'
    };
    
    return `<span class="tool-badge ${badge}">${badgeLabels[badge] || badge}</span>`;
}

/**
 * Check if user has access to a tool based on roles
 */
function hasAccess(tool) {
    if (!tool.roles || tool.roles.length === 0) {
        return true; // No role restriction
    }
    return authService.hasAnyRole(tool.roles);
}

/**
 * Render a single tool card
 */
function renderToolCard(tool) {
    if (!hasAccess(tool)) {
        return ''; // Don't render tools the user can't access
    }
    
    const disabledClass = tool.disabled ? 'disabled' : '';
    const href = tool.disabled ? '#' : tool.url;
    const onClick = tool.disabled ? 'onclick="event.preventDefault();"' : '';
    
    return `
        <a href="${href}" class="tool-card ${disabledClass}" ${onClick} data-tool-id="${tool.id}">
            <div class="tool-card-icon">
                ${getIconHtml(tool.icon)}
            </div>
            <div class="tool-card-content">
                <h2 class="tool-card-title">${tool.title}</h2>
                <p class="tool-card-description">${tool.description}</p>
                <div class="tool-card-footer">
                    <span class="tool-card-action">
                        ${tool.disabled ? 'Prossimamente' : 'Apri strumento'}
                        ${icons.arrow}
                    </span>
                    ${getBadgeHtml(tool.badge)}
                </div>
            </div>
        </a>
    `;
}

/**
 * Render all tools
 */
function renderTools() {
    const grid = document.getElementById('toolsGrid');
    if (!grid) return;
    
    const html = tools.map(tool => renderToolCard(tool)).join('');
    grid.innerHTML = html;
}

/**
 * Initialize dashboard
 */
function init() {
    renderTools();
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for external use
export { tools, renderTools };
