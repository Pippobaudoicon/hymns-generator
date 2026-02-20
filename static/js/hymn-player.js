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
    shuffleType: null, // null | 'all' | 'page'
    audioPlayer: null,
    searchFilter: null,
    isLoading: false
};

/**
 * Sync state from URL query parameters
 */
function loadFromURL() {
    const params = new URLSearchParams(window.location.search);
    state.currentPage = parseInt(params.get('page')) || 1;
    const size = parseInt(params.get('size'));
    if ([25, 50, 100, 1000].includes(size)) state.pageSize = size;
    state.filters.search = params.get('q') || '';
    state.filters.category = params.get('cat') || '';
    state.filters.tag = params.get('tag') || '';
    state.viewMode = params.get('view') === 'list' ? 'list' : 'grid';
}

/**
 * Update the URL to reflect current state (without reloading)
 */
function updateURL() {
    const params = new URLSearchParams();
    if (state.currentPage > 1) params.set('page', state.currentPage);
    if (state.pageSize !== 50) params.set('size', state.pageSize);
    if (state.filters.search) params.set('q', state.filters.search);
    if (state.filters.category) params.set('cat', state.filters.category);
    if (state.filters.tag) params.set('tag', state.filters.tag);
    if (state.viewMode !== 'grid') params.set('view', state.viewMode);
    const url = params.toString() ? `?${params}` : window.location.pathname;
    history.replaceState(null, '', url);
}

/**
 * Initialize the application
 */
async function init() {
    // Load state from URL before anything else
    loadFromURL();

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

    // Apply URL state to UI controls
    applyStateToUI();

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
 * Apply loaded state values to UI controls
 */
function applyStateToUI() {
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === state.viewMode);
    });

    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) pageSizeSelect.value = state.pageSize;

    if (state.searchFilter && typeof state.searchFilter.setValues === 'function') {
        state.searchFilter.setValues(state.filters);
    }
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

        if (typeof state.searchFilter.setValues === 'function') {
            state.searchFilter.setValues(state.filters);
        }
    } catch (error) {
        console.error('Error loading filter options:', error);
        showNotification('Errore nel caricamento dei filtri', 'error');
    }
}

/**
 * Handle page number click via event delegation
 */
function handlePageNumberClick(e) {
    const btn = e.target.closest('.pagination-page-btn');
    if (!btn) return;
    const page = parseInt(btn.dataset.page);
    if (page !== state.currentPage) {
        state.currentPage = page;
        loadHymns();
    }
}

/**
 * Setup event listeners (called once at init)
 */
function setupEventListeners() {
    // View toggle buttons
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Page size selector
    document.getElementById('pageSizeSelect').addEventListener('change', (e) => {
        state.pageSize = parseInt(e.target.value);
        state.currentPage = 1;
        loadHymns();
    });

    // First / Last / Prev / Next page buttons
    document.getElementById('firstPageTop').addEventListener('click', () => goToPage(1));
    document.getElementById('lastPageTop').addEventListener('click', () => goToPage(state.totalPages));
    document.getElementById('firstPageBottom').addEventListener('click', () => goToPage(1));
    document.getElementById('lastPageBottom').addEventListener('click', () => goToPage(state.totalPages));

    document.getElementById('prevPageTop').addEventListener('click', () => {
        if (state.currentPage > 1) { state.currentPage--; loadHymns(); }
    });
    document.getElementById('nextPageTop').addEventListener('click', () => {
        if (state.currentPage < state.totalPages) { state.currentPage++; loadHymns(); }
    });
    document.getElementById('prevPageBottom').addEventListener('click', () => {
        if (state.currentPage > 1) { state.currentPage--; loadHymns(); }
    });
    document.getElementById('nextPageBottom').addEventListener('click', () => {
        if (state.currentPage < state.totalPages) { state.currentPage++; loadHymns(); }
    });

    // Shuffle buttons
    document.getElementById('randomPlayBtn').addEventListener('click', playRandomHymn);
    document.getElementById('pageShuffleBtn').addEventListener('click', playPageShuffleHymn);

    // Page number click — event delegation avoids attaching listeners to dynamically generated buttons
    document.getElementById('pageNumbersTop').addEventListener('click', handlePageNumberClick);
    document.getElementById('pageNumbersBottom').addEventListener('click', handlePageNumberClick);

}

/**
 * Navigate to a specific page
 */
function goToPage(page) {
    if (page < 1 || page > state.totalPages || page === state.currentPage) return;
    state.currentPage = page;
    loadHymns();
}

/**
 * Handle search input
 */
function handleSearch(filters) {
    state.filters = filters;
    state.currentPage = 1;
    loadHymns();
}

/**
 * Handle filter change
 */
function handleFilterChange(filters) {
    state.filters = filters;
    state.currentPage = 1;
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
        updateURL();

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
    container.textContent = '';

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

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Disable whichever shuffle mode is currently active (helper)
 */
function disableShuffleUI() {
    state.audioPlayer.setShuffleMode(false);
    state.shuffleType = null;
    document.getElementById('randomPlayBtn').classList.remove('active');
    document.getElementById('pageShuffleBtn').classList.remove('active');
}

/**
 * Toggle shuffle mode — fetches ALL hymns matching current filters, enables random
 * playback across the full list, and plays one immediately. Click again to disable.
 */
async function playRandomHymn() {
    const btn = document.getElementById('randomPlayBtn');
    if (state.shuffleType === 'all') {
        disableShuffleUI();
        return;
    }

    btn.disabled = true;
    try {
        const pageSize = 1000;
        const data = await api.getAllHymns(
            1, pageSize,
            state.filters.search || null,
            state.filters.category || null,
            state.filters.tag || null
        );
        const allHymns = data.hymns;
        const playable = allHymns.filter(h => h.audio_url);

        if (playable.length === 0) {
            showNotification('Nessun inno con audio disponibile', 'warning');
            return;
        }

        disableShuffleUI();
        state.audioPlayer.setShuffleMode(true);
        state.shuffleType = 'all';
        btn.classList.add('active');

        const hymn = playable[Math.floor(Math.random() * playable.length)];
        const index = allHymns.indexOf(hymn);
        state.audioPlayer.loadHymn(hymn, allHymns, index);
        state.audioPlayer.play();
        highlightPlayingHymn(hymn.number || hymn.songNumber);
    } catch (error) {
        showNotification('Errore nel caricamento degli inni', 'error');
    } finally {
        btn.disabled = false;
    }
}

/**
 * Toggle page shuffle — shuffles only the hymns on the current page.
 */
function playPageShuffleHymn() {
    const btn = document.getElementById('pageShuffleBtn');
    if (state.shuffleType === 'page') {
        disableShuffleUI();
        return;
    }

    const playable = state.hymns.filter(h => h.audio_url);
    if (playable.length === 0) {
        showNotification('Nessun inno con audio disponibile', 'warning');
        return;
    }

    disableShuffleUI();
    state.audioPlayer.setShuffleMode(true);
    state.shuffleType = 'page';
    btn.classList.add('active');

    const hymn = playable[Math.floor(Math.random() * playable.length)];
    const index = state.hymns.indexOf(hymn);
    state.audioPlayer.loadHymn(hymn, state.hymns, index);
    state.audioPlayer.play();
    highlightPlayingHymn(hymn.number || hymn.songNumber);
}

/**
 * Play a hymn
 */
function playHymn(hymn, index) {
    if (!hymn.audio_url) {
        showNotification('Audio non disponibile per questo inno', 'warning');
        return;
    }

    if (state.audioPlayer.shuffleMode) {
        // Preserve the full shuffle playlist — only update the current index
        const hymnNumber = hymn.number || hymn.songNumber;
        const shuffleIndex = state.audioPlayer.playlist.findIndex(
            h => (h.number || h.songNumber) === hymnNumber
        );
        state.audioPlayer.loadHymn(hymn, null, shuffleIndex !== -1 ? shuffleIndex : state.audioPlayer.currentIndex);
    } else {
        state.audioPlayer.loadHymn(hymn, state.hymns, index);
    }

    state.audioPlayer.play();
    highlightPlayingHymn(hymn.number || hymn.songNumber);
}

/**
 * Highlight the currently playing hymn
 */
function highlightPlayingHymn(hymnNumber) {
    document.querySelectorAll('.hymn-card, .hymn-list-item').forEach(card => {
        card.classList.remove('playing');
    });

    const currentCard = document.querySelector(`[data-hymn-number="${hymnNumber}"]`);
    if (currentCard) {
        currentCard.classList.add('playing');
    }
}

/**
 * Show hymn info modal — builds DOM nodes without innerHTML to avoid XSS
 */
function showHymnInfo(hymn) {
    const hymnNumber = hymn.number || hymn.songNumber;
    const hymnCategory = hymn.category || hymn.bookSectionTitle;

    // Overlay
    const overlay = document.createElement('div');
    overlay.className = 'hymn-info-modal-overlay';

    // Header
    const header = document.createElement('div');
    header.className = 'hymn-info-modal-header';

    const headerTitle = document.createElement('h2');
    headerTitle.textContent = `Inno #${hymnNumber || '?'}`;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'hymn-info-modal-close';
    closeBtn.textContent = '\u00d7';

    header.appendChild(headerTitle);
    header.appendChild(closeBtn);

    // Body
    const body = document.createElement('div');
    body.className = 'hymn-info-modal-body';

    const titleEl = document.createElement('h3');
    titleEl.textContent = hymn.title || 'Untitled';
    body.appendChild(titleEl);

    const addSection = (label, value) => {
        const section = document.createElement('div');
        section.className = 'hymn-info-section';
        const strong = document.createElement('strong');
        strong.textContent = label;
        section.appendChild(strong);
        const text = document.createTextNode(value);
        section.appendChild(text);
        body.appendChild(section);
    };

    addSection('Categoria: ', hymnCategory || 'Unknown');

    if (hymn.composers && hymn.composers.length > 0) {
        addSection(`Compositore${hymn.composers.length > 1 ? 'i' : ''}: `, hymn.composers.join(', '));
    }
    if (hymn.authors && hymn.authors.length > 0) {
        addSection(`Autore${hymn.authors.length > 1 ? 'i' : ''}: `, hymn.authors.join(', '));
    }

    if (hymn.tags && hymn.tags.length > 0) {
        const tagSection = document.createElement('div');
        tagSection.className = 'hymn-info-section';
        const tagLabel = document.createElement('strong');
        tagLabel.textContent = 'Tag:';
        tagSection.appendChild(tagLabel);
        const tagContainer = document.createElement('div');
        tagContainer.className = 'hymn-info-tags';
        hymn.tags.forEach(tag => {
            const span = document.createElement('span');
            span.className = 'hymn-info-tag';
            span.textContent = tag;
            tagContainer.appendChild(span);
        });
        tagSection.appendChild(tagContainer);
        body.appendChild(tagSection);
    }

    if (hymn.audio_url) {
        const playSection = document.createElement('div');
        playSection.className = 'hymn-info-section';
        const playBtn = document.createElement('button');
        playBtn.className = 'btn-primary';
        playBtn.addEventListener('click', () => {
            window.hymnPlayerApp.playHymnFromModal(hymnNumber);
        });
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('width', '18');
        svg.setAttribute('height', '18');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        const polygon = document.createElementNS(svgNS, 'polygon');
        polygon.setAttribute('points', '5 3 19 12 5 21 5 3');
        svg.appendChild(polygon);
        playBtn.appendChild(svg);
        playBtn.appendChild(document.createTextNode(' Riproduci'));
        playSection.appendChild(playBtn);
        body.appendChild(playSection);
    }

    // Assemble modal content
    const content = document.createElement('div');
    content.className = 'hymn-info-modal-content';
    content.appendChild(header);
    content.appendChild(body);

    // Assemble modal
    const modal = document.createElement('div');
    modal.className = 'hymn-info-modal';
    modal.appendChild(overlay);
    modal.appendChild(content);

    document.body.appendChild(modal);

    const closeModal = () => modal.remove();

    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);

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
            document.querySelector('.hymn-info-modal')?.remove();
        }
    }
};

/**
 * Switch view mode
 */
function switchView(view) {
    state.viewMode = view;

    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    updateURL();
    renderHymns();
}

/**
 * Update pagination UI
 */
function updatePagination() {
    const paginationTopContainer = document.getElementById('paginationTopContainer');
    const paginationBottomContainer = document.getElementById('paginationBottomContainer');

    if (state.totalPages <= 1) {
        paginationTopContainer.style.display = 'none';
        paginationBottomContainer.style.display = 'none';
        return;
    }

    const prevDisabled = state.currentPage <= 1;
    const nextDisabled = state.currentPage >= state.totalPages;

    ['Top', 'Bottom'].forEach(pos => {
        document.getElementById(`firstPage${pos}`).disabled = prevDisabled;
        document.getElementById(`prevPage${pos}`).disabled = prevDisabled;
        document.getElementById(`nextPage${pos}`).disabled = nextDisabled;
        document.getElementById(`lastPage${pos}`).disabled = nextDisabled;

        const input = document.getElementById(`jumpPageInput${pos}`);
        if (input) input.max = state.totalPages;
    });

    // Render page number buttons using DOM — data is all integers, no XSS risk
    renderPageNumbers('pageNumbersTop');
    renderPageNumbers('pageNumbersBottom');

    // Mobile page indicator
    updateMobilePageInfo();

    paginationTopContainer.style.display = 'flex';
    paginationBottomContainer.style.display = 'flex';
}

/**
 * Render page number buttons into the given container element
 */
function renderPageNumbers(containerId) {
    const container = document.getElementById(containerId);
    container.textContent = '';

    const fragment = document.createDocumentFragment();
    const { currentPage, totalPages } = state;
    const maxVisible = 7;

    const addPageBtn = (num) => {
        const btn = document.createElement('button');
        btn.className = 'pagination-btn pagination-page-btn' + (num === currentPage ? ' active' : '');
        btn.dataset.page = num;
        btn.textContent = num;
        if (num === currentPage) btn.setAttribute('aria-current', 'page');
        fragment.appendChild(btn);
    };

    const addEllipsis = () => {
        const span = document.createElement('span');
        span.className = 'pagination-ellipsis';
        span.textContent = '...';
        fragment.appendChild(span);
    };

    if (totalPages <= maxVisible) {
        for (let i = 1; i <= totalPages; i++) addPageBtn(i);
    } else {
        addPageBtn(1);

        let startPage = Math.max(2, currentPage - 1);
        let endPage = Math.min(totalPages - 1, currentPage + 1);

        if (currentPage <= 3) {
            endPage = 5;
        } else if (currentPage >= totalPages - 2) {
            startPage = totalPages - 4;
        }

        if (startPage > 2) addEllipsis();

        for (let i = startPage; i <= endPage; i++) addPageBtn(i);

        if (endPage < totalPages - 1) addEllipsis();

        addPageBtn(totalPages);
    }

    container.appendChild(fragment);
}

/**
 * Update the mobile page indicator text inside each pagination container
 */
function updateMobilePageInfo() {
    ['Top', 'Bottom'].forEach(pos => {
        const numbersEl = document.getElementById(`pageNumbers${pos}`);
        let indicator = numbersEl.previousElementSibling;
        if (!indicator || !indicator.classList.contains('pagination-mobile-info')) {
            indicator = document.createElement('span');
            indicator.className = 'pagination-mobile-info';
            numbersEl.parentNode.insertBefore(indicator, numbersEl);
        }
        indicator.textContent = `${state.currentPage} / ${state.totalPages}`;
    });
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
    document.getElementById('paginationTopContainer').style.display = 'none';
    document.getElementById('paginationBottomContainer').style.display = 'none';
}

function hideEmpty() {
    document.getElementById('emptyState').style.display = 'none';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
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
