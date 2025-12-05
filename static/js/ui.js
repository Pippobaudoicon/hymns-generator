/**
 * UI Module - Handles all UI rendering and manipulation
 */

export const ui = {
    /**
     * Show loading state
     */
    showLoading(elementId, message = 'Caricamento') {
        const element = document.getElementById(elementId);
        element.innerHTML = `<div class="loading">${message}</div>`;
        if (elementId === 'resultsSection') {
            element.classList.add('show');
        }
    },

    /**
     * Show error message
     */
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        element.innerHTML = `
            <div class="error-message">
                <strong>Errore:</strong> ${message}
            </div>
        `;
    },

    /**
     * Display hymns in the results section
     */
    displayHymns(hymns, wardName, primaDomenica, domenicaFestiva, tipoFestivita) {
        const today = new Date().toLocaleDateString('it-IT', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });

        let html = `
            <div class="results-header">
                <h2>Inni Selezionati</h2>
                <div class="date-info">${today}</div>
            </div>
            <div class="ward-info">
                ${wardName ? `<strong>Rione:</strong> ${wardName}` : '<em>Selezione casuale (senza rione)</em>'}
                ${primaDomenica ? ' • <strong>Prima Domenica</strong>' : ''}
                ${domenicaFestiva ? ` • <strong>Domenica Festiva (${tipoFestivita})</strong>` : ''}
            </div>
        `;

        hymns.forEach((hymn, index) => {
            const hymnNumber = hymn.number || hymn.songNumber;
            const hymnCategory = hymn.category || hymn.bookSectionTitle;
            
            let metaInfo = [];
            if (hymn.composers && hymn.composers.length > 0) {
                metaInfo.push(`Compositore: ${hymn.composers.join(', ')}`);
            }
            if (hymn.authors && hymn.authors.length > 0) {
                metaInfo.push(`Autore: ${hymn.authors.join(', ')}`);
            }
            
            // Always show swap buttons (both for ward and random selection)
            html += `
                <div class="hymn-card" id="hymn-card-${index + 1}">
                    <span class="hymn-position">${index + 1}</span>
                    <span class="hymn-number">#${hymnNumber}</span>
                    <div class="hymn-title">${hymn.title}</div>
                    <span class="hymn-category">${hymnCategory}</span>
                    ${metaInfo.length > 0 ? `<div class="hymn-meta">${metaInfo.join(' • ')}</div>` : ''}
                    ${hymn.audio_url ? `
                        <div class="hymn-audio">
                            <audio controls preload="none">
                                <source src="${hymn.audio_url}" type="audio/mpeg">
                                Il tuo browser non supporta l'elemento audio.
                            </audio>
                        </div>
                    ` : ''}
                    <div class="hymn-actions">
                        <button class="btn-swap random" data-position="${index + 1}" data-category="${hymnCategory}">Altro casuale</button>
                        ${wardName ? `<button class="btn-swap choose" data-position="${index + 1}" data-category="${hymnCategory}">Scegli inno</button>` : ''}
                    </div>
                </div>
            `;
        });

        document.getElementById('resultsSection').innerHTML = html;
    },

    /**
     * Display hymn list in modal
     */
    displayHymnList(hymns, currentHymnNumber) {
        const hymnList = document.getElementById('hymnList');
        
        if (hymns.length === 0) {
            hymnList.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">Nessun inno disponibile</p>';
            return;
        }
        
        let html = '';
        hymns.forEach(hymn => {
            const hymnNumber = hymn.number || hymn.songNumber;
            const hymnCategory = hymn.category || hymn.bookSectionTitle;
            const isCurrent = hymnNumber === currentHymnNumber;
            
            html += `
                <div class="hymn-list-item ${isCurrent ? 'current' : ''}" 
                     data-hymn-number="${hymnNumber}"
                     style="${isCurrent ? 'opacity: 0.5; cursor: default;' : ''}">
                    <span class="hymn-number">#${hymnNumber}</span>
                    <span class="hymn-title">${hymn.title}</span>
                    <div class="hymn-category">${hymnCategory}${isCurrent ? ' (attuale)' : ''}</div>
                </div>
            `;
        });
        
        hymnList.innerHTML = html;
    },

    /**
     * Display ward list in history panel
     */
    displayWardsList(wards) {
        const content = document.getElementById('historyPanelContent');
        
        if (wards.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/>
                    </svg>
                    <h3>Nessun rione trovato</h3>
                    <p>Inizia a generare inni per creare la cronologia.</p>
                </div>
            `;
            return;
        }

        let html = '<div class="ward-list">';
        wards.forEach(ward => {
            const initial = ward.charAt(0).toUpperCase();
            html += `
                <div class="ward-list-item" data-ward-name="${ward.replace(/'/g, "\\'")}">
                    <div class="ward-icon">${initial}</div>
                    <div class="ward-name">${ward}</div>
                    <span class="ward-arrow">›</span>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    },

    /**
     * Display ward history in panel
     */
    displayWardHistory(data) {
        const content = document.getElementById('historyPanelContent');

        let html = `
            <button class="history-back-btn" id="historyBackBtn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 12H5M12 19l-7-7 7-7"/>
                </svg>
                Tutti i rioni
            </button>
            <div class="history-ward-title">
                <h3>${data.ward_name}</h3>
                <span>${data.total_selections} selezioni salvate</span>
            </div>
        `;

        if (data.history.length === 0) {
            html += `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                        <line x1="16" y1="2" x2="16" y2="6"/>
                        <line x1="8" y1="2" x2="8" y2="6"/>
                        <line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    <h3>Nessuna cronologia</h3>
                    <p>Non ci sono selezioni salvate per questo rione.</p>
                </div>
            `;
        } else {
            data.history.forEach((selection, index) => {
                const date = new Date(selection.date).toLocaleDateString('it-IT', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric'
                });

                html += `
                    <div class="history-selection-group">
                        <div class="history-selection-header" data-selection-index="${index}">
                            <div>
                                <div class="history-selection-date">${date}</div>
                                <div class="history-selection-badges">
                                    ${selection.prima_domenica ? '<span class="history-badge prima">Prima Domenica</span>' : ''}
                                    ${selection.domenica_festiva ? `<span class="history-badge festiva">${selection.tipo_festivita || 'Festiva'}</span>` : ''}
                                </div>
                            </div>
                            <svg class="toggle-arrow" id="arrow-${index}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6,9 12,15 18,9"/>
                            </svg>
                        </div>
                        <div class="history-selection-hymns" id="hymns-${index}">
                `;

                selection.hymns.forEach(hymn => {
                    html += `
                        <div class="history-hymn-item">
                            <div class="history-hymn-position">${hymn.position}</div>
                            <div class="history-hymn-info">
                                <div class="history-hymn-number">#${hymn.hymn_number}</div>
                                <div class="history-hymn-title">${hymn.hymn_title}</div>
                                <div class="history-hymn-category">${hymn.hymn_category}</div>
                            </div>
                        </div>
                    `;
                });

                html += `
                        </div>
                    </div>
                `;
            });
        }

        content.innerHTML = html;
    },

    /**
     * Display recent selections across all wards
     */
    displayRecentSelections(selections) {
        const content = document.getElementById('historyPanelContent');
        
        if (selections.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12,6 12,12 16,14"/>
                    </svg>
                    <h3>Nessuna selezione recente</h3>
                    <p>Inizia a generare inni per creare la cronologia.</p>
                </div>
            `;
            return;
        }

        let html = '';
        selections.forEach((selection, index) => {
            const date = new Date(selection.date).toLocaleDateString('it-IT', {
                weekday: 'short',
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });

            html += `
                <div class="history-selection-group">
                    <div class="history-selection-header" data-selection-index="${index}">
                        <div>
                            <div class="history-selection-date">${selection.ward_name} - ${date}</div>
                            <div class="history-selection-badges">
                                ${selection.prima_domenica ? '<span class="history-badge prima">1ª Dom</span>' : ''}
                                ${selection.domenica_festiva ? `<span class="history-badge festiva">${selection.tipo_festivita || 'Festiva'}</span>` : ''}
                            </div>
                        </div>
                        <svg class="toggle-arrow" id="arrow-${index}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6,9 12,15 18,9"/>
                        </svg>
                    </div>
                    <div class="history-selection-hymns" id="hymns-${index}">
            `;

            selection.hymns.forEach(hymn => {
                html += `
                    <div class="history-hymn-item">
                        <div class="history-hymn-position">${hymn.position}</div>
                        <div class="history-hymn-info">
                            <div class="history-hymn-number">#${hymn.hymn_number}</div>
                            <div class="history-hymn-title">${hymn.hymn_title}</div>
                            <div class="history-hymn-category">${hymn.hymn_category}</div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        content.innerHTML = html;
    },

    /**
     * Toggle history selection expansion
     */
    toggleHistorySelection(index) {
        const hymnsDiv = document.getElementById(`hymns-${index}`);
        const arrow = document.getElementById(`arrow-${index}`);
        
        if (hymnsDiv && arrow) {
            hymnsDiv.classList.toggle('expanded');
            arrow.classList.toggle('expanded');
        }
    },

    /**
     * Show/hide modal
     */
    showModal(show = true) {
        const modal = document.getElementById('hymnModal');
        if (show) {
            modal.classList.add('show');
        } else {
            modal.classList.remove('show');
        }
    },

    /**
     * Show/hide history panel
     */
    showHistoryPanel(show = true) {
        const overlay = document.getElementById('historyOverlay');
        const panel = document.getElementById('historyPanel');
        
        if (show) {
            overlay.classList.add('show');
            panel.classList.add('show');
            document.body.style.overflow = 'hidden';
        } else {
            overlay.classList.remove('show');
            panel.classList.remove('show');
            document.body.style.overflow = '';
        }
    },

    /**
     * Update history panel title and tabs visibility
     */
    updateHistoryPanelTitle(title, showTabs = true) {
        document.getElementById('historyPanelTitle').textContent = title;
        document.getElementById('historyTabs').style.display = showTabs ? 'flex' : 'none';
    },

    /**
     * Set active history tab
     */
    setActiveHistoryTab(tabName) {
        document.querySelectorAll('.history-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
    }
};