/**
 * Main Application Module
 * Coordinates between API and UI modules
 */

import { api } from '/static/js/api.js';
import { ui } from '/static/js/ui.js';

// Application state
const state = {
    currentHymns: [],
    currentSelectionParams: {},
    selectedPosition: null,
    availableHymns: [],
    currentHistoryWard: null,
    isHistoricalView: false,
    historicalDate: null
};

/**
 * Initialize the application
 */
async function init() {
    await loadWardsDropdown();
    setupEventListeners();
}

/**
 * Load wards into dropdown
 */
async function loadWardsDropdown() {
    const wardSelect = document.getElementById('wardName');
    try {
        const wards = await api.getWards();
        wards.forEach(ward => {
            const option = document.createElement('option');
            option.value = ward;
            option.textContent = ward;
            wardSelect.appendChild(option);
        });
    } catch (error) {
        console.warn('Could not load wards:', error);
    }
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Show/hide festivity type based on checkbox
    document.getElementById('domenicaFestiva').addEventListener('change', function() {
        document.getElementById('festivitaGroup').style.display = this.checked ? 'block' : 'none';
    });

    // Get hymns button
    document.querySelector('.btn-primary').addEventListener('click', getHymns);

    // View history button
    document.querySelector('.btn-secondary').addEventListener('click', viewHistory);

    // Modal close button
    document.querySelector('.modal-close').addEventListener('click', () => ui.showModal(false));

    // Close modal when clicking outside
    document.getElementById('hymnModal').addEventListener('click', function(e) {
        if (e.target === this) {
            ui.showModal(false);
        }
    });

    // Close history panel when clicking overlay
    document.getElementById('historyOverlay').addEventListener('click', closeHistoryPanel);

    // Hymn search input
    document.getElementById('hymnSearch').addEventListener('input', filterHymnList);

    // History tabs
    document.querySelectorAll('.history-tab').forEach(tab => {
        tab.addEventListener('click', () => switchHistoryTab(tab.dataset.tab));
    });

    // Keyboard support for closing panels
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (document.getElementById('historyPanel').classList.contains('show')) {
                closeHistoryPanel();
            } else if (document.getElementById('hymnModal').classList.contains('show')) {
                ui.showModal(false);
            }
        }
    });

    // Event delegation for dynamically created elements
    document.addEventListener('click', handleDynamicClicks);
}

/**
 * Handle clicks on dynamically created elements
 */
function handleDynamicClicks(e) {
    const target = e.target;

    // Swap random button
    if (target.classList.contains('random') && target.classList.contains('btn-swap')) {
        const position = parseInt(target.dataset.position);
        const category = target.dataset.category;
        swapRandom(position, category);
    }

    // Choose hymn button
    if (target.classList.contains('choose') && target.classList.contains('btn-swap')) {
        const position = parseInt(target.dataset.position);
        const category = target.dataset.category;
        openHymnSelector(position, category);
    }

    // Hymn list item click
    if (target.closest('.hymn-list-item:not(.current)')) {
        const item = target.closest('.hymn-list-item');
        const hymnNumber = parseInt(item.dataset.hymnNumber);
        if (hymnNumber) {
            selectHymn(hymnNumber);
        }
    }

    // Ward list item click
    if (target.closest('.ward-list-item')) {
        const item = target.closest('.ward-list-item');
        const wardName = item.dataset.wardName;
        if (wardName) {
            loadWardHistory(wardName);
        }
    }

    // History selection header click
    if (target.closest('.history-selection-header')) {
        const header = target.closest('.history-selection-header');
        const index = parseInt(header.dataset.selectionIndex);
        if (!isNaN(index)) {
            ui.toggleHistorySelection(index);
        }
    }

    // History back button
    if (target.closest('#historyBackBtn')) {
        goBackToWardsList();
    }

    // Load history button
    if (target.closest('.btn-load-history')) {
        const btn = target.closest('.btn-load-history');
        loadHistoricalSelection(btn);
    }
}

/**
 * Get hymns based on form inputs
 */
async function getHymns() {
    const wardName = document.getElementById('wardName').value.trim();
    const primaDomenica = document.getElementById('primaDomenica').checked;
    const domenicaFestiva = document.getElementById('domenicaFestiva').checked;
    const tipoFestivita = document.getElementById('tipoFestivita').value;

    if (domenicaFestiva && !tipoFestivita) {
        alert('Per favore seleziona il tipo di festività');
        return;
    }

    ui.showLoading('resultsSection', 'Caricamento inni');

    try {
        const data = await api.getHymns(wardName, primaDomenica, domenicaFestiva, tipoFestivita);
        state.currentHymns = data.hymns;
        state.currentSelectionParams = { wardName, primaDomenica, domenicaFestiva, tipoFestivita };
        ui.displayHymns(data.hymns, wardName, primaDomenica, domenicaFestiva, tipoFestivita);
    } catch (error) {
        ui.showError('resultsSection', error.message);
    }
}

/**
 * Swap hymn with random selection
 */
async function swapRandom(position, category) {
    const { wardName, primaDomenica, domenicaFestiva, tipoFestivita } = state.currentSelectionParams;
    
    // If no ward is selected, regenerate all hymns and pick the one at the position
    if (!wardName) {
        try {
            const data = await api.getHymns('', primaDomenica, domenicaFestiva, tipoFestivita);
            // Replace only the hymn at the specified position
            state.currentHymns[position - 1] = data.hymns[position - 1];
            ui.displayHymns(
                state.currentHymns,
                wardName,
                primaDomenica,
                domenicaFestiva,
                tipoFestivita
            );
        } catch (error) {
            alert(`Errore: ${error.message}`);
        }
        return;
    }
    
    // Ward-based smart selection
    const currentHymnNumber = state.currentHymns[position - 1].number || state.currentHymns[position - 1].songNumber;
    
    try {
        const newHymn = await api.swapHymn(position, currentHymnNumber, wardName, domenicaFestiva, tipoFestivita);
        state.currentHymns[position - 1] = newHymn;
        ui.displayHymns(
            state.currentHymns,
            wardName,
            primaDomenica,
            domenicaFestiva,
            tipoFestivita
        );
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

/**
 * Open hymn selector modal
 */
async function openHymnSelector(position, category) {
    state.selectedPosition = position;
    const { wardName, domenicaFestiva, tipoFestivita } = state.currentSelectionParams;
    
    document.getElementById('modalTitle').textContent = `Seleziona Inno (Posizione ${position})`;
    document.getElementById('hymnSearch').value = '';
    ui.showLoading('hymnList', 'Caricamento inni disponibili');
    ui.showModal(true);
    
    try {
        const data = await api.getAvailableHymns(position, category, wardName, domenicaFestiva, tipoFestivita);
        state.availableHymns = data.hymns || [];
        const currentHymnNumber = state.currentHymns[position - 1].number || state.currentHymns[position - 1].songNumber;
        ui.displayHymnList(state.availableHymns, currentHymnNumber);
    } catch (error) {
        ui.showError('hymnList', error.message);
    }
}

/**
 * Filter hymn list based on search
 */
function filterHymnList() {
    const searchTerm = document.getElementById('hymnSearch').value.toLowerCase();
    const filtered = state.availableHymns.filter(hymn => {
        const number = (hymn.number || hymn.songNumber).toString();
        const title = hymn.title.toLowerCase();
        return number.includes(searchTerm) || title.includes(searchTerm);
    });
    const currentHymnNumber = state.currentHymns[state.selectedPosition - 1].number || 
                             state.currentHymns[state.selectedPosition - 1].songNumber;
    ui.displayHymnList(filtered, currentHymnNumber);
}

/**
 * Select a specific hymn
 */
async function selectHymn(hymnNumber) {
    const { wardName, domenicaFestiva, tipoFestivita } = state.currentSelectionParams;
    const currentHymnNumber = state.currentHymns[state.selectedPosition - 1].number || 
                             state.currentHymns[state.selectedPosition - 1].songNumber;
    
    ui.showModal(false);
    
    try {
        const newHymn = await api.swapHymn(
            state.selectedPosition, 
            currentHymnNumber, 
            wardName, 
            domenicaFestiva, 
            tipoFestivita, 
            hymnNumber
        );
        state.currentHymns[state.selectedPosition - 1] = newHymn;
        ui.displayHymns(
            state.currentHymns, 
            wardName, 
            state.currentSelectionParams.primaDomenica, 
            domenicaFestiva, 
            tipoFestivita
        );
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

/**
 * View history - open history panel
 */
function viewHistory() {
    ui.showHistoryPanel(true);
    
    const wardName = document.getElementById('wardName').value.trim();
    if (wardName) {
        loadWardHistory(wardName);
    } else {
        switchHistoryTab('wards');
        loadWardsList();
    }
}

/**
 * Close history panel
 */
function closeHistoryPanel() {
    ui.showHistoryPanel(false);
    state.currentHistoryWard = null;
}

/**
 * Switch history tab
 */
function switchHistoryTab(tab) {
    ui.setActiveHistoryTab(tab);
    ui.updateHistoryPanelTitle('Cronologia Inni', true);

    if (tab === 'wards') {
        loadWardsList();
    } else if (tab === 'recent') {
        loadRecentSelections();
    }
}

/**
 * Load wards list in history panel
 */
async function loadWardsList() {
    ui.showLoading('historyPanelContent', 'Caricamento rioni');

    try {
        const wards = await api.getWards();
        ui.displayWardsList(wards);
    } catch (error) {
        ui.showError('historyPanelContent', error.message);
    }
}

/**
 * Load ward history
 */
async function loadWardHistory(wardName) {
    state.currentHistoryWard = wardName;
    ui.updateHistoryPanelTitle(`📜 ${wardName}`, false);
    ui.showLoading('historyPanelContent', 'Caricamento cronologia');

    try {
        const data = await api.getWardHistory(wardName);
        ui.displayWardHistory(data);
        
        // Expand the first selection by default
        if (data.history.length > 0) {
            setTimeout(() => ui.toggleHistorySelection(0), 100);
        }
    } catch (error) {
        ui.showError('historyPanelContent', error.message);
    }
}

/**
 * Go back to wards list from ward history
 */
function goBackToWardsList() {
    state.currentHistoryWard = null;
    ui.updateHistoryPanelTitle('📜 Cronologia Inni', true);
    loadWardsList();
}

/**
 * Load recent selections across all wards
 */
async function loadRecentSelections() {
    ui.showLoading('historyPanelContent', 'Caricamento selezioni recenti');

    try {
        const wards = await api.getWards();
        
        if (wards.length === 0) {
            ui.displayRecentSelections([]);
            return;
        }

        // Fetch history for all wards and combine
        const allSelections = [];
        for (const ward of wards) {
            try {
                const data = await api.getWardHistory(ward, 5);
                data.history.forEach(sel => {
                    allSelections.push({
                        ...sel,
                        ward_name: ward
                    });
                });
            } catch (e) {
                console.warn(`Failed to load history for ${ward}:`, e);
            }
        }

        // Sort by date descending and take top 15
        allSelections.sort((a, b) => new Date(b.date) - new Date(a.date));
        const recentSelections = allSelections.slice(0, 15);

        ui.displayRecentSelections(recentSelections);
    } catch (error) {
        ui.showError('historyPanelContent', error.message);
    }
}

/**
 * Load historical selection into main form
 */
async function loadHistoricalSelection(button) {
    const id = button.dataset.id;
    const selectionDate = button.dataset.selectionDate;
    const wardName = button.dataset.wardName;
    const primaDomenica = button.dataset.primaDomenica === 'true';
    const domenicaFestiva = button.dataset.domenicaFestiva === 'true';
    const tipoFestivita = button.dataset.tipoFestivita || '';

    // Close history panel
    ui.showHistoryPanel(false);

    // Update form fields to match the historical selection
    document.getElementById('wardName').value = wardName;
    document.getElementById('primaDomenica').checked = primaDomenica;
    document.getElementById('domenicaFestiva').checked = domenicaFestiva;
    document.getElementById('tipoFestivita').value = tipoFestivita;
    document.getElementById('festivitaGroup').style.display = domenicaFestiva ? 'block' : 'none';

    // Load the hymns for that date
    ui.showLoading('resultsSection', 'Caricamento inni dalla cronologia');

    try {
        const data = await api.getWardHistory(wardName, 50); // Get history (API limit is 50)
        const selection = data.history.find(s => s.date === selectionDate);
        
        if (!selection) {
            throw new Error('Selezione non trovata');
        }

        // Fetch full hymn data including audio URLs for each hymn
        const hymnPromises = selection.hymns.map(async (h) => {
            try {
                // Fetch the full hymn data by number to get audio URL
                const response = await fetch(`/api/v1/get_hymn?number=${h.hymn_number}`);
                if (response.ok) {
                    const fullHymn = await response.json();
                    return fullHymn || {
                        number: h.hymn_number,
                        title: h.hymn_title,
                        category: h.hymn_category,
                        audio_url: null,
                        composers: [],
                        authors: []
                    };
                }
            } catch (error) {
                console.warn(`Failed to fetch full data for hymn ${h.hymn_number}:`, error);
            }
            // Fallback to basic data if fetch fails
            return {
                number: h.hymn_number,
                title: h.hymn_title,
                category: h.hymn_category,
                audio_url: null,
                composers: [],
                authors: []
            };
        });

        const hymns = await Promise.all(hymnPromises);

        // Update state
        state.currentHymns = hymns;
        state.currentSelectionParams = { wardName, primaDomenica, domenicaFestiva, tipoFestivita };
        state.isHistoricalView = true;
        state.historicalDate = selectionDate;

        // Display hymns with historical flag
        ui.displayHymns(hymns, wardName, primaDomenica, domenicaFestiva, tipoFestivita, true, selectionDate);
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        ui.showError('resultsSection', error.message);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', init);