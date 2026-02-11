/**
 * Search and Filter Component
 * Reusable search and filtering functionality for hymns
 */

export class SearchFilter {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            showCategoryFilter: true,
            showTagFilter: true,
            placeholder: 'Cerca per numero, titolo, compositore o autore...',
            onSearch: null,
            onFilterChange: null,
            ...options
        };
        
        this.filters = {
            search: '',
            category: '',
            tag: ''
        };
        
        this.categories = [];
        this.tags = [];
        
        this.init();
    }

    init() {
        this.createUI();
        this.attachEventListeners();
    }

    createUI() {
        const html = `
            <div class="search-filter">
                <div class="search-filter-search">
                    <svg class="search-filter-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                    </svg>
                    <input 
                        type="text" 
                        class="search-filter-input" 
                        id="searchInput"
                        placeholder="${this.options.placeholder}"
                        autocomplete="off"
                    >
                    <button class="search-filter-clear" id="clearSearch" style="display: none;" title="Cancella">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                
                ${this.options.showCategoryFilter ? `
                    <div class="search-filter-group">
                        <label for="categoryFilter" class="search-filter-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                            </svg>
                            Categoria
                        </label>
                        <select class="search-filter-select" id="categoryFilter">
                            <option value="">Tutte le categorie</option>
                        </select>
                    </div>
                ` : ''}
                
                ${this.options.showTagFilter ? `
                    <div class="search-filter-group">
                        <label for="tagFilter" class="search-filter-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
                                <line x1="7" y1="7" x2="7.01" y2="7"></line>
                            </svg>
                            Tag
                        </label>
                        <select class="search-filter-select" id="tagFilter">
                            <option value="">Tutti i tag</option>
                        </select>
                    </div>
                ` : ''}
                
                <button class="search-filter-reset" id="resetFilters" style="display: none;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="1 4 1 10 7 10"></polyline>
                        <polyline points="23 20 23 14 17 14"></polyline>
                        <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                    </svg>
                    Ripristina filtri
                </button>
            </div>
        `;
        
        this.container.innerHTML = html;
        
        // Get references to elements
        this.elements = {
            searchInput: this.container.querySelector('#searchInput'),
            searchIcon: this.container.querySelector('.search-filter-icon'),
            clearSearch: this.container.querySelector('#clearSearch'),
            categoryFilter: this.container.querySelector('#categoryFilter'),
            tagFilter: this.container.querySelector('#tagFilter'),
            resetFilters: this.container.querySelector('#resetFilters')
        };
    }

    attachEventListeners() {
        // Search input with debounce
        let searchTimeout;
        this.elements.searchInput.addEventListener('input', (e) => {
            const value = e.target.value.trim();
            
            // Update UI immediately (no debounce)
            this.filters.search = value;
            this.updateSearchIcon();
            this.updateClearButton();
            this.updateResetButton();
            
            // Debounce the actual search trigger
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.triggerSearch();
            }, 300);
        });
        
        // Clear search button
        if (this.elements.clearSearch) {
            this.elements.clearSearch.addEventListener('click', () => {
                this.elements.searchInput.value = '';
                this.filters.search = '';
                this.updateSearchIcon();
                this.updateClearButton();
                this.updateResetButton();
                this.triggerSearch();
            });
        }
        
        // Category filter
        if (this.elements.categoryFilter) {
            this.elements.categoryFilter.addEventListener('change', (e) => {
                this.filters.category = e.target.value;
                this.updateResetButton();
                this.triggerFilterChange();
            });
        }
        
        // Tag filter
        if (this.elements.tagFilter) {
            this.elements.tagFilter.addEventListener('change', (e) => {
                this.filters.tag = e.target.value;
                this.updateResetButton();
                this.triggerFilterChange();
            });
        }
        
        // Reset filters button
        if (this.elements.resetFilters) {
            this.elements.resetFilters.addEventListener('click', () => {
                this.resetFilters();
            });
        }
    }

    setCategories(categories) {
        this.categories = categories;
        if (this.elements.categoryFilter) {
            // Clear existing options except first
            this.elements.categoryFilter.innerHTML = '<option value="">Tutte le categorie</option>';
            
            // Add category options
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                this.elements.categoryFilter.appendChild(option);
            });
        }
    }

    setTags(tags) {
        this.tags = tags;
        if (this.elements.tagFilter) {
            // Clear existing options except first
            this.elements.tagFilter.innerHTML = '<option value="">Tutti i tag</option>';
            
            // Add tag options
            tags.forEach(tag => {
                const option = document.createElement('option');
                option.value = tag;
                option.textContent = tag;
                this.elements.tagFilter.appendChild(option);
            });
        }
    }

    getFilters() {
        return { ...this.filters };
    }

    resetFilters() {
        this.filters = {
            search: '',
            category: '',
            tag: ''
        };
        
        this.elements.searchInput.value = '';
        if (this.elements.categoryFilter) {
            this.elements.categoryFilter.value = '';
        }
        if (this.elements.tagFilter) {
            this.elements.tagFilter.value = '';
        }
        
        this.updateSearchIcon();
        this.updateClearButton();
        this.updateResetButton();
        this.triggerFilterChange();
    }

    updateSearchIcon() {
        if (this.elements.searchIcon) {
            this.elements.searchIcon.style.display = this.filters.search ? 'none' : 'block';
        }
    }

    updateClearButton() {
        if (this.elements.clearSearch) {
            this.elements.clearSearch.style.display = this.filters.search ? 'flex' : 'none';
        }
    }

    updateResetButton() {
        if (this.elements.resetFilters) {
            const hasFilters = this.filters.search || this.filters.category || this.filters.tag;
            this.elements.resetFilters.style.display = hasFilters ? 'flex' : 'none';
        }
    }

    triggerSearch() {
        if (this.options.onSearch) {
            this.options.onSearch(this.filters);
        }
    }

    triggerFilterChange() {
        if (this.options.onFilterChange) {
            this.options.onFilterChange(this.filters);
        }
    }

    setSearchValue(value) {
        this.elements.searchInput.value = value;
        this.filters.search = value;
        this.updateSearchIcon();
        this.updateClearButton();
        this.updateResetButton();
    }

    setCategoryValue(value) {
        if (this.elements.categoryFilter) {
            this.elements.categoryFilter.value = value;
            this.filters.category = value;
            this.updateResetButton();
        }
    }

    setTagValue(value) {
        if (this.elements.tagFilter) {
            this.elements.tagFilter.value = value;
            this.filters.tag = value;
            this.updateResetButton();
        }
    }

    destroy() {
        this.container.innerHTML = '';
    }
}

export default SearchFilter;