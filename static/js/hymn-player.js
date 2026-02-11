/**
 * Hymn Player Application
 * Browse and play all hymns with audio accompaniment
 */

import { api } from '/static/js/api.js';
import { HymnCard } from '/static/js/components/hymn-card.js';
import { AudioPlayer } from '/static/js/components/audio-player.js';
import { SearchFilter } from '/static/js/components/search-filter.js';
import { UserMenu } from '/static/js/components/user-menu.js';

// Application state
const state = {
    hymns: [],
    currentPage: 1,
    pageSize: 50,
    totalPages: 1,
    total: 0,
    filters: {
        search: '',
        category: '',
        tag: ''
    },
    viewMode: 'grid', // 'grid' or 'list'
    audioPlayer: null,
    searchFilter: null,
    isLoading: false
};

/**
 * Initialize the application
 */
async function init() {
    // Initialize user menu
    const userMenuContainer = document.getElementById('userMenuContainer');
    new UserMenu(userMenuContainer, authService);
    
    // Initialize search filter
    const searchFilterContainer = document.getElementById('searchFilterContainer');
    state.searchFilter = new SearchFilter(searchFilterContainer, {
        showCategoryFilter: true,
        showTagFilter: true,
        onSearch: handleSearch,
        onFilterChange: handleFilterChange
    });
    
    // Initialize audio player
    const audioPlayerContainer = document.getElementById('audioPlayerContainer');
    state.audioPlayer = new AudioPlayer(audioPlayerContainer);
    
    // Load categories and tags for filters
    await loadFilterOptions();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial hymns
    await loadHymns();
}

/**
 * Load filter options (categories and tags)
 */
async function loadFilterOptions() {
    try {
        const [categories, tags] = await Promise.all([
            api.getCategories(),
            api.getTags()
        ]);
        
        state.searchFilter.setCategories(categories);
        state.searchFilter.setTags(tags);
    } catch (error) {
        console.error('Error loading filter options:', error);
        showNotification('Errore nel caricamento dei filtri', 'error');
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // View toggle buttons
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });
    
    // Top pagination buttons
    document.getElementById('prevPageTop').addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            loadHymns();
        }
    });
    
    document.getElementById('nextPageTop').addEventListener('click', () => {
        if (state.currentPage < state.totalPages) {
            state.currentPage++;
            loadHymns();
        }
    });
    
    // Bottom pagination buttons
    document.getElementById('prevPageBottom').addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            loadHymns();
        }
    });
    
    document.getElementById('nextPageBottom').addEventListener('click', () => {
        if (state.currentPage < state.totalPages) {
            state.currentPage++;
            loadHymns();
        }
    });
}

/**
 * Handle search input
 */
function handleSearch(filters) {
    state.filters = filters;
    state.currentPage = 1; // Reset to first page
    loadHymns();
}

/**
 * Handle filter change
 */
function handleFilterChange(filters) {
    state.filters = filters;
    state.currentPage = 1; // Reset to first page
    loadHymns();
}

/**
 * Load hymns from API
 */
async function loadHymns() {
    if (state.isLoading) return;
    
    state.isLoading = true;
    showLoading(true);
    hideEmpty();
    
    try {
        const data = await api.getAllHymns(
            state.currentPage,
            state.pageSize,
            state.filters.search || null,
            state.filters.category || null,
            state.filters.tag || null
        );
        
        state.hymns = data.hymns;
        state.total = data.total;
        state.totalPages = data.total_pages;
        state.currentPage = data.page;
        
        renderHymns();
        updatePagination();
        updateResultsCount();
        
        // Show empty state if no results
        if (state.hymns.length === 0) {
            showEmpty();
        }
        
    } catch (error) {
        console.error('Error loading hymns:', error);
        showNotification(error.message || 'Errore nel caricamento degli inni', 'error');
        showEmpty();
    } finally {
        state.isLoading = false;
        showLoading(false);
    }
}

/**
 * Render hymns in grid or list view
 */
function renderHymns() {
    const container = document.getElementById('hymnsContainer');
    container.innerHTML = '';
    
    // Update container class based on view mode
    container.className = state.viewMode === 'grid' ? 'hymns-grid' : 'hymns-list';
    
    state.hymns.forEach((hymn, index) => {
        let card;
        
        if (state.viewMode === 'grid') {
            card = HymnCard.create(hymn, {
                showAudio: true,
                showSelect: false,
                showInfo: true,
                onPlay: (h) => playHymn(h, index),
                onInfo: (h) => showHymnInfo(h)
            });
        } else {
            card = HymnCard.createListItem(hymn, {
                showAudio: true,
                showInfo: true,
                onPlay: (h) => playHymn(h, index),
                onInfo: (h) => showHymnInfo(h)
            });
        }
        
        container.appendChild(card);
    });
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Play a hymn
 */
function playHymn(hymn, index) {
    if (!hymn.audio_url) {
        showNotification('Audio non disponibile per questo inno', 'warning');
        return;
    }
    
    // Load hymn with playlist context
    state.audioPlayer.loadHymn(hymn, state.hymns, index);
    state.audioPlayer.play();
    
    // Highlight playing hymn
    highlightPlayingHymn(hymn.number);
}

/**
 * Highlight the currently playing hymn
 */
function highlightPlayingHymn(hymnNumber) {
    // Remove previous highlights
    document.querySelectorAll('.hymn-card, .hymn-list-item').forEach(card => {
        card.classList.remove('playing');
    });
    
    // Add highlight to current hymn
    const currentCard = document.querySelector(`[data-hymn-number="${hymnNumber}"]`);
    if (currentCard) {
        currentCard.classList.add('playing');
    }
}

/**
 * Show hymn info modal
 */
function showHymnInfo(hymn) {
    // Normalize hymn data (handle both field name formats)
    const hymnNumber = hymn.number || hymn.songNumber;
    const hymnCategory = hymn.category || hymn.bookSectionTitle;
    
    // Create a simple modal with hymn details
    const modal = document.createElement('div');
    modal.className = 'hymn-info-modal';
    modal.innerHTML = `
        <div class="hymn-info-modal-overlay"></div>
        <div class="hymn-info-modal-content">
            <div class="hymn-info-modal-header">
                <h2>Inno #${hymnNumber || '?'}</h2>
                <button class="hymn-info-modal-close">&times;</button>
            </div>
            <div class="hymn-info-modal-body">
                <h3>${hymn.title || 'Untitled'}</h3>
                <div class="hymn-info-section">
                    <strong>Categoria:</strong> ${hymnCategory || 'Unknown'}
                </div>
                ${hymn.composers && hymn.composers.length > 0 ? `
                    <div class="hymn-info-section">
                        <strong>Compositore${hymn.composers.length > 1 ? 'i' : ''}:</strong> ${hymn.composers.join(', ')}
                    </div>
                ` : ''}
                ${hymn.authors && hymn.authors.length > 0 ? `
                    <div class="hymn-info-section">
                        <strong>Autore${hymn.authors.length > 1 ? 'i' : ''}:</strong> ${hymn.authors.join(', ')}
                    </div>
                ` : ''}
                ${hymn.tags && hymn.tags.length > 0 ? `
                    <div class="hymn-info-section">
                        <strong>Tag:</strong>
                        <div class="hymn-info-tags">
                            ${hymn.tags.map(tag => `<span class="hymn-info-tag">${tag}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
                ${hymn.audio_url ? `
                    <div class="hymn-info-section">
                        <button class="btn-primary" onclick="window.hymnPlayerApp.playHymnFromModal(${hymnNumber})">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="5 3 19 12 5 21 5 3"></polygon>
                            </svg>
                            Riproduci
                        </button>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal handlers
    const closeModal = () => {
        modal.remove();
    };
    
    modal.querySelector('.hymn-info-modal-close').addEventListener('click', closeModal);
    modal.querySelector('.hymn-info-modal-overlay').addEventListener('click', closeModal);
    
    // Close on escape key
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

/**
 * Play hymn from modal (exposed globally)
 */
window.hymnPlayerApp = {
    playHymnFromModal: (hymnNumber) => {
        const index = state.hymns.findIndex(h => (h.number || h.songNumber) === hymnNumber);
        if (index !== -1) {
            playHymn(state.hymns[index], index);
            // Close modal
            document.querySelector('.hymn-info-modal')?.remove();
        }
    }
};

/**
 * Switch view mode
 */
function switchView(view) {
    state.viewMode = view;
    
    // Update button states
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // Re-render hymns
    renderHymns();
}

/**
 * Update pagination UI
 */
function updatePagination() {
    // Top pagination
    const paginationTopContainer = document.getElementById('paginationTopContainer');
    const prevBtnTop = document.getElementById('prevPageTop');
    const nextBtnTop = document.getElementById('nextPageTop');
    const pageNumbersTop = document.getElementById('pageNumbersTop');
    
    // Bottom pagination
    const paginationBottomContainer = document.getElementById('paginationBottomContainer');
    const prevBtnBottom = document.getElementById('prevPageBottom');
    const nextBtnBottom = document.getElementById('nextPageBottom');
    const pageNumbersBottom = document.getElementById('pageNumbersBottom');
    
    if (state.totalPages <= 1) {
        paginationTopContainer.style.display = 'none';
        paginationBottomContainer.style.display = 'none';
        return;
    }
    
    // Update button states
    const prevDisabled = state.currentPage <= 1;
    const nextDisabled = state.currentPage >= state.totalPages;
    
    prevBtnTop.disabled = prevDisabled;
    nextBtnTop.disabled = nextDisabled;
    prevBtnBottom.disabled = prevDisabled;
    nextBtnBottom.disabled = nextDisabled;
    
    // Generate page numbers
    const pageNumbers = generatePageNumbers(state.currentPage, state.totalPages);
    
    // Update top pagination
    paginationTopContainer.style.display = 'flex';
    pageNumbersTop.innerHTML = pageNumbers;
    
    // Update bottom pagination
    paginationBottomContainer.style.display = 'flex';
    pageNumbersBottom.innerHTML = pageNumbers;
    
    // Attach click handlers to page number buttons
    document.querySelectorAll('.pagination-page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page !== state.currentPage) {
                state.currentPage = page;
                loadHymns();
            }
        });
    });
}

/**
 * Generate page number buttons HTML
 */
function generatePageNumbers(currentPage, totalPages) {
    const pages = [];
    const maxVisible = 7; // Maximum number of page buttons to show
    
    if (totalPages <= maxVisible) {
        // Show all pages
        for (let i = 1; i <= totalPages; i++) {
            pages.push(createPageButton(i, i === currentPage));
        }
    } else {
        // Show first page
        pages.push(createPageButton(1, currentPage === 1));
        
        // Calculate range around current page
        let startPage = Math.max(2, currentPage - 1);
        let endPage = Math.min(totalPages - 1, currentPage + 1);
        
        // Adjust range if at start or end
        if (currentPage <= 3) {
            endPage = 5;
        } else if (currentPage >= totalPages - 2) {
            startPage = totalPages - 4;
        }
        
        // Add ellipsis after first page if needed
        if (startPage > 2) {
            pages.push('<span class="pagination-ellipsis">...</span>');
        }
        
        // Add middle pages
        for (let i = startPage; i <= endPage; i++) {
            pages.push(createPageButton(i, i === currentPage));
        }
        
        // Add ellipsis before last page if needed
        if (endPage < totalPages - 1) {
            pages.push('<span class="pagination-ellipsis">...</span>');
        }
        
        // Show last page
        pages.push(createPageButton(totalPages, currentPage === totalPages));
    }
    
    return pages.join('');
}

/**
 * Create a page button HTML
 */
function createPageButton(pageNum, isActive) {
    const activeClass = isActive ? ' active' : '';
    return `<button class="pagination-btn pagination-page-btn${activeClass}" data-page="${pageNum}">${pageNum}</button>`;
}

/**
 * Update results count
 */
function updateResultsCount() {
    const resultsCount = document.getElementById('resultsCount');
    const start = (state.currentPage - 1) * state.pageSize + 1;
    const end = Math.min(state.currentPage * state.pageSize, state.total);
    
    if (state.total === 0) {
        resultsCount.textContent = 'Nessun inno trovato';
    } else {
        resultsCount.textContent = `${start}-${end} di ${state.total} inni`;
    }
}

/**
 * Show/hide loading state
 */
function showLoading(show) {
    const loadingState = document.getElementById('loadingState');
    const hymnsContainer = document.getElementById('hymnsContainer');
    
    if (show) {
        loadingState.style.display = 'flex';
        hymnsContainer.style.display = 'none';
    } else {
        loadingState.style.display = 'none';
        hymnsContainer.style.display = state.viewMode === 'grid' ? 'grid' : 'block';
    }
}

/**
 * Show/hide empty state
 */
function showEmpty() {
    document.getElementById('emptyState').style.display = 'flex';
    document.getElementById('hymnsContainer').style.display = 'none';
    document.getElementById('paginationContainer').style.display = 'none';
}

function hideEmpty() {
    document.getElementById('emptyState').style.display = 'none';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Simple notification implementation
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#28a745'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for external use
export { state, loadHymns, playHymn };