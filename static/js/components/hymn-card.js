/**
 * Hymn Card Component
 * Reusable component for displaying hymn information
 */

export class HymnCard {
    /**
     * Create a hymn card element
     * @param {Object} hymn - Hymn data object
     * @param {Object} options - Display options
     * @param {boolean} options.showAudio - Show audio play button
     * @param {boolean} options.showSelect - Show select button
     * @param {boolean} options.showInfo - Show info button
     * @param {Function} options.onPlay - Callback when play button clicked
     * @param {Function} options.onSelect - Callback when select button clicked
     * @param {Function} options.onInfo - Callback when info button clicked
     * @returns {HTMLElement} The hymn card element
     */
    static create(hymn, options = {}) {
        const {
            showAudio = true,
            showSelect = false,
            showInfo = true,
            onPlay = null,
            onSelect = null,
            onInfo = null
        } = options;

        // Normalize hymn data (handle both camelCase and snake_case)
        const hymnNumber = hymn.number || hymn.songNumber;
        const hymnCategory = hymn.category || hymn.bookSectionTitle;

        const card = document.createElement('div');
        card.className = 'hymn-card';
        card.dataset.hymnNumber = hymnNumber;

        // Card header with number and title
        const header = document.createElement('div');
        header.className = 'hymn-card-header';
        
        const number = document.createElement('div');
        number.className = 'hymn-card-number';
        number.textContent = `#${hymnNumber || '?'}`;
        
        const title = document.createElement('h3');
        title.className = 'hymn-card-title';
        title.textContent = hymn.title || 'Untitled';
        
        header.appendChild(number);
        header.appendChild(title);

        // Card body with metadata
        const body = document.createElement('div');
        body.className = 'hymn-card-body';

        // Category
        const category = document.createElement('div');
        category.className = 'hymn-card-category';
        category.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <span>${hymnCategory || 'Unknown'}</span>
        `;

        // Composers (if available)
        if (hymn.composers && hymn.composers.length > 0 && hymn.composers[0]) {
            const composers = document.createElement('div');
            composers.className = 'hymn-card-meta';
            const composerNames = hymn.composers.filter(c => c && c.trim()).join(', ');
            if (composerNames) {
                composers.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18V5l12-2v13"></path>
                        <circle cx="6" cy="18" r="3"></circle>
                        <circle cx="18" cy="16" r="3"></circle>
                    </svg>
                    <span>${composerNames}</span>
                `;
                body.appendChild(composers);
            }
        }

        // Authors (if available)
        if (hymn.authors && hymn.authors.length > 0 && hymn.authors[0]) {
            const authors = document.createElement('div');
            authors.className = 'hymn-card-meta';
            const authorNames = hymn.authors.filter(a => a && a.trim()).join(', ');
            if (authorNames) {
                authors.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    <span>${authorNames}</span>
                `;
                body.appendChild(authors);
            }
        }

        body.insertBefore(category, body.firstChild);

        // Tags (if available)
        if (hymn.tags && hymn.tags.length > 0) {
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'hymn-card-tags';
            hymn.tags.slice(0, 3).forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'hymn-card-tag';
                tagEl.textContent = tag;
                tagsContainer.appendChild(tagEl);
            });
            body.appendChild(tagsContainer);
        }

        // Card footer with action buttons
        const footer = document.createElement('div');
        footer.className = 'hymn-card-footer';

        // Play button (if audio available and enabled)
        if (showAudio && hymn.audio_url) {
            const playBtn = document.createElement('button');
            playBtn.className = 'hymn-card-btn hymn-card-btn-play';
            playBtn.title = 'Riproduci';
            playBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
            `;
            if (onPlay) {
                playBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    onPlay(hymn);
                });
            }
            footer.appendChild(playBtn);
        } else if (showAudio && !hymn.audio_url) {
            const noAudioBtn = document.createElement('button');
            noAudioBtn.className = 'hymn-card-btn hymn-card-btn-disabled';
            noAudioBtn.title = 'Audio non disponibile';
            noAudioBtn.disabled = true;
            noAudioBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <line x1="23" y1="9" x2="17" y2="15"></line>
                    <line x1="17" y1="9" x2="23" y2="15"></line>
                </svg>
            `;
            footer.appendChild(noAudioBtn);
        }

        // Select button (if enabled)
        if (showSelect) {
            const selectBtn = document.createElement('button');
            selectBtn.className = 'hymn-card-btn hymn-card-btn-select';
            selectBtn.title = 'Seleziona';
            selectBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            `;
            if (onSelect) {
                selectBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    onSelect(hymn);
                });
            }
            footer.appendChild(selectBtn);
        }

        // Info button (if enabled)
        if (showInfo) {
            const infoBtn = document.createElement('button');
            infoBtn.className = 'hymn-card-btn hymn-card-btn-info';
            infoBtn.title = 'Dettagli';
            infoBtn.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
            `;
            if (onInfo) {
                infoBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    onInfo(hymn);
                });
            }
            footer.appendChild(infoBtn);
        }

        // Assemble card
        card.appendChild(header);
        card.appendChild(body);
        if (footer.children.length > 0) {
            card.appendChild(footer);
        }

        return card;
    }

    /**
     * Create a compact hymn list item (for lists instead of grids)
     * @param {Object} hymn - Hymn data object
     * @param {Object} options - Display options
     * @returns {HTMLElement} The hymn list item element
     */
    static createListItem(hymn, options = {}) {
        const {
            showAudio = true,
            showInfo = true,
            onPlay = null,
            onSelect = null,
            onInfo = null
        } = options;

        // Normalize hymn data
        const hymnNumber = hymn.number || hymn.songNumber;
        const hymnCategory = hymn.category || hymn.bookSectionTitle;

        const item = document.createElement('div');
        item.className = 'hymn-list-item';
        item.dataset.hymnNumber = hymnNumber;

        const content = document.createElement('div');
        content.className = 'hymn-list-item-content';

        const number = document.createElement('div');
        number.className = 'hymn-list-item-number';
        number.textContent = hymnNumber;

        const info = document.createElement('div');
        info.className = 'hymn-list-item-info';

        const title = document.createElement('div');
        title.className = 'hymn-list-item-title';
        title.textContent = hymn.title;

        const meta = document.createElement('div');
        meta.className = 'hymn-list-item-meta';
        meta.textContent = hymnCategory;

        info.appendChild(title);
        info.appendChild(meta);

        content.appendChild(number);
        content.appendChild(info);

        const actions = document.createElement('div');
        actions.className = 'hymn-list-item-actions';

        if (showAudio && hymn.audio_url) {
            const playBtn = document.createElement('button');
            playBtn.className = 'hymn-list-item-btn';
            playBtn.title = 'Riproduci';
            playBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
            `;
            if (onPlay) {
                playBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    onPlay(hymn);
                });
            }
            actions.appendChild(playBtn);
        }

        if (onSelect) {
            const selectBtn = document.createElement('button');
            selectBtn.className = 'hymn-list-item-btn';
            selectBtn.title = 'Seleziona';
            selectBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            `;
            selectBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                onSelect(hymn);
            });
            actions.appendChild(selectBtn);
        }

        // Info button (if enabled)
        if (showInfo && onInfo) {
            const infoBtn = document.createElement('button');
            infoBtn.className = 'hymn-list-item-btn';
            infoBtn.title = 'Dettagli';
            infoBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
            `;
            infoBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                onInfo(hymn);
            });
            actions.appendChild(infoBtn);
        }

        item.appendChild(content);
        if (actions.children.length > 0) {
            item.appendChild(actions);
        }

        return item;
    }
}

// Export for use in other modules
export default HymnCard;