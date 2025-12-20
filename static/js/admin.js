/**
 * Admin Panel JavaScript
 */

// Check authentication on load
if (!requireAuth()) {
    throw new Error('Not authenticated');
}

// State
let currentUser = null;
let areasData = [];
let stakesData = [];
let wardsData = [];
let usersData = [];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    try {
        currentUser = authService.getUser();
        if (!currentUser) {
            currentUser = await authService.fetchCurrentUser();
        }
        
        initializeUI();
        setupNavigation();
        await loadDashboardData();
    } catch (error) {
        console.error('Init error:', error);
        authService.logout();
    }
});

/**
 * Initialize UI with user data
 */
function initializeUI() {
    // Show menu toggle on mobile
    const isMobile = window.innerWidth <= 768;
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.style.display = isMobile ? 'flex' : 'none';
    }
    
    // Set user info in nav
    document.getElementById('currentUserDisplay').textContent = 
        currentUser.full_name || currentUser.username;
    
    // Set welcome message
    document.getElementById('welcomeUserName').textContent = 
        currentUser.full_name || currentUser.username;
    
    const roleSpan = document.getElementById('welcomeUserRole');
    roleSpan.textContent = authService.getRoleDisplayName(currentUser.role);
    roleSpan.className = `role-badge ${currentUser.role}`;
    
    // Show/hide nav items based on role
    document.querySelectorAll('.nav-item[data-role]').forEach(item => {
        const allowedRoles = item.dataset.role.split(',');
        if (!allowedRoles.includes(currentUser.role)) {
            item.classList.add('hidden');
        }
    });
}

/**
 * Toggle mobile sidebar menu
 */
function toggleMobileMenu() {
    const sidebar = document.querySelector('.admin-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

/**
 * Close mobile menu when clicking a nav item
 */
function closeMobileMenu() {
    const sidebar = document.querySelector('.admin-sidebar');
    if (sidebar && window.innerWidth <= 768) {
        sidebar.classList.remove('open');
    }
}

/**
 * Handle window resize to show/hide menu toggle
 */
window.addEventListener('resize', () => {
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
    }
    
    // Close mobile menu on resize to desktop
    if (window.innerWidth > 768) {
        const sidebar = document.querySelector('.admin-sidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
    }
});

/**
 * Setup sidebar navigation
 */
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (item.classList.contains('hidden')) return;
            
            // Close mobile menu when item is clicked
            closeMobileMenu();
            
            // Update active state
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            // Show section
            const sectionId = item.dataset.section;
            document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
            document.getElementById(`section-${sectionId}`).classList.add('active');
            
            // Load section data
            loadSectionData(sectionId);
        });
    });
}

/**
 * Load data for a section
 */
async function loadSectionData(section) {
    switch (section) {
        case 'dashboard':
            await loadDashboardData();
            break;
        case 'users':
            await loadUsers();
            break;
        case 'areas':
            await loadAreas();
            break;
        case 'stakes':
            await loadStakes();
            break;
        case 'wards':
            await loadWards();
            break;
    }
}

/**
 * Load dashboard statistics
 */
async function loadDashboardData() {
    try {
        // Load all data in parallel
        const [users, areas, stakes, wards] = await Promise.all([
            fetchData('/auth/users'),
            fetchData('/areas'),
            fetchData('/stakes'),
            fetchData('/wards')
        ]);
        
        document.getElementById('stat-users').textContent = users?.length || 0;
        document.getElementById('stat-areas').textContent = areas?.length || 0;
        document.getElementById('stat-stakes').textContent = stakes?.length || 0;
        document.getElementById('stat-wards').textContent = wards?.length || 0;
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

/**
 * Generic data fetcher
 */
async function fetchData(url) {
    try {
        const response = await authService.authenticatedFetch(url);
        if (response.ok) {
            return await response.json();
        }
        return [];
    } catch {
        return [];
    }
}

// ==================== USERS ====================

async function loadUsers() {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Caricamento...</td></tr>';
    
    try {
        usersData = await fetchData('/auth/users');
        
        if (usersData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Nessun utente trovato</td></tr>';
            return;
        }
        
        tbody.innerHTML = usersData.map(user => `
            <tr>
                <td><strong>${escapeHtml(user.username)}</strong></td>
                <td>${escapeHtml(user.email || '-')}</td>
                <td><span class="role-badge ${user.role}">${authService.getRoleDisplayName(user.role)}</span></td>
                <td><span class="status-badge ${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Attivo' : 'Disattivo'}</span></td>
                <td class="actions">
                    <button class="btn-icon" onclick="editUser(${user.id})" title="Modifica">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    ${user.role !== 'superadmin' ? `
                    <button class="btn-icon" onclick="manageUserWards(${user.id})" title="Gestisci Rioni">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                            <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                    </button>
                    ` : ''}
                    ${user.id !== currentUser.id ? `
                    <button class="btn-icon delete" onclick="deleteUser(${user.id})" title="Elimina">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                    ` : ''}
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Errore nel caricamento</td></tr>';
    }
}

function showCreateUserModal() {
    showModal('Nuovo Utente', `
        <form id="createUserForm">
            <div class="form-group">
                <label for="newUsername">Username *</label>
                <input type="text" id="newUsername" required placeholder="nome.cognome">
            </div>
            <div class="form-group">
                <label for="newEmail">Email *</label>
                <input type="email" id="newEmail" required placeholder="email@esempio.it">
            </div>
            <div class="form-group">
                <label for="newFullName">Nome Completo</label>
                <input type="text" id="newFullName" placeholder="Mario Rossi">
            </div>
            <div class="form-group">
                <label for="newPassword">Password *</label>
                <input type="password" id="newPassword" required minlength="6" placeholder="Minimo 6 caratteri">
            </div>
            <div class="form-group">
                <label for="newRole">Ruolo *</label>
                <select id="newRole" required>
                    ${getRoleOptions()}
                </select>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('createUserForm').requestSubmit()">Crea Utente</button>
        </div>
    `);
    
    document.getElementById('createUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createUser();
    });
}

async function createUser() {
    const userData = {
        username: document.getElementById('newUsername').value,
        email: document.getElementById('newEmail').value,
        full_name: document.getElementById('newFullName').value || null,
        password: document.getElementById('newPassword').value,
        role: document.getElementById('newRole').value
    };
    
    try {
        const response = await authService.authenticatedFetch('/auth/users', {
            method: 'POST',
            body: userData
        });
        
        if (response.ok) {
            closeModal();
            showToast('Utente creato con successo', 'success');
            await loadUsers();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nella creazione utente', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function editUser(userId) {
    const user = usersData.find(u => u.id === userId);
    if (!user) return;
    
    showModal('Modifica Utente', `
        <form id="editUserForm">
            <div class="form-group">
                <label for="editUsername">Username</label>
                <input type="text" id="editUsername" value="${escapeHtml(user.username)}" disabled>
            </div>
            <div class="form-group">
                <label for="editEmail">Email *</label>
                <input type="email" id="editEmail" value="${escapeHtml(user.email || '')}" required>
            </div>
            <div class="form-group">
                <label for="editFullName">Nome Completo</label>
                <input type="text" id="editFullName" value="${escapeHtml(user.full_name || '')}">
            </div>
            <div class="form-group">
                <label for="editRole">Ruolo *</label>
                <select id="editRole" required>
                    ${getRoleOptions(user.role)}
                </select>
            </div>
            <div class="form-group">
                <label>Utente Attivo</label>
                <input type="checkbox" id="editIsActive" ${user.is_active ? 'checked' : ''}> 
            </div>
            <div class="form-group">
                <label for="editPassword">Nuova Password (lascia vuoto per non cambiare)</label>
                <input type="password" id="editPassword" minlength="6">
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('editUserForm').requestSubmit()">Salva</button>
        </div>
    `);
    
    document.getElementById('editUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateUser(userId);
    });
}

async function updateUser(userId) {
    const userData = {
        email: document.getElementById('editEmail').value,
        full_name: document.getElementById('editFullName').value || null,
        role: document.getElementById('editRole').value,
        is_active: document.getElementById('editIsActive').checked
    };
    
    const newPassword = document.getElementById('editPassword').value;
    if (newPassword) {
        userData.password = newPassword;
    }
    
    try {
        const response = await authService.authenticatedFetch(`/auth/users/${userId}`, {
            method: 'PUT',
            body: userData
        });
        
        if (response.ok) {
            closeModal();
            showToast('Utente aggiornato con successo', 'success');
            await loadUsers();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'aggiornamento', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm('Sei sicuro di voler eliminare questo utente?')) return;
    
    try {
        const response = await authService.authenticatedFetch(`/auth/users/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Utente eliminato con successo', 'success');
            await loadUsers();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'eliminazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function manageUserWards(userId) {
    const user = usersData.find(u => u.id === userId);
    if (!user) return;
    
    // Load wards
    wardsData = await fetchData('/wards');
    const userWardIds = user.ward_ids || [];
    
    showModal(`Rioni di ${user.username}`, `
        <form id="userWardsForm">
            <div class="form-group">
                <label>Seleziona Rioni</label>
                <div class="checkbox-list">
                    ${wardsData.map(ward => `
                        <div class="checkbox-item">
                            <input type="checkbox" id="ward_${ward.id}" value="${ward.id}" 
                                ${userWardIds.includes(ward.id) ? 'checked' : ''}>
                            <label for="ward_${ward.id}">${escapeHtml(ward.name)}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('userWardsForm').requestSubmit()">Salva</button>
        </div>
    `);
    
    document.getElementById('userWardsForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateUserWards(userId);
    });
}

async function updateUserWards(userId) {
    const selectedWards = [];
    document.querySelectorAll('#userWardsForm input[type="checkbox"]:checked').forEach(cb => {
        selectedWards.push(parseInt(cb.value));
    });
    
    try {
        const response = await authService.authenticatedFetch(`/auth/users/${userId}/wards`, {
            method: 'PUT',
            body: { ward_ids: selectedWards }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Rioni aggiornati con successo', 'success');
            await loadUsers();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'aggiornamento', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

function getRoleOptions(selectedRole = null) {
    const roles = [];
    
    // Filter available roles based on current user's role
    if (currentUser.role === 'superadmin') {
        roles.push('superadmin', 'area_manager', 'stake_manager', 'ward_user');
    } else if (currentUser.role === 'area_manager') {
        roles.push('stake_manager', 'ward_user');
    } else if (currentUser.role === 'stake_manager') {
        roles.push('ward_user');
    }
    
    return roles.map(role => 
        `<option value="${role}" ${role === selectedRole ? 'selected' : ''}>${authService.getRoleDisplayName(role)}</option>`
    ).join('');
}

// ==================== AREAS ====================

async function loadAreas() {
    const tbody = document.getElementById('areasTableBody');
    tbody.innerHTML = '<tr><td colspan="4" class="loading">Caricamento...</td></tr>';
    
    try {
        areasData = await fetchData('/areas');
        
        if (areasData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="loading">Nessuna area trovata</td></tr>';
            return;
        }
        
        tbody.innerHTML = areasData.map(area => `
            <tr>
                <td><strong>${escapeHtml(area.name)}</strong></td>
                <td>${area.stakes?.length || 0}</td>
                <td>${formatDate(area.created_at)}</td>
                <td class="actions">
                    <button class="btn-icon" onclick="editArea(${area.id})" title="Modifica">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn-icon delete" onclick="deleteArea(${area.id})" title="Elimina">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">Errore nel caricamento</td></tr>';
    }
}

function showCreateAreaModal() {
    showModal('Nuova Area', `
        <form id="createAreaForm">
            <div class="form-group">
                <label for="newAreaName">Nome Area *</label>
                <input type="text" id="newAreaName" required>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('createAreaForm').requestSubmit()">Crea Area</button>
        </div>
    `);
    
    document.getElementById('createAreaForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createArea();
    });
}

async function createArea() {
    const name = document.getElementById('newAreaName').value;
    
    try {
        const response = await authService.authenticatedFetch('/areas', {
            method: 'POST',
            body: { name }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Area creata con successo', 'success');
            await loadAreas();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nella creazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function editArea(areaId) {
    const area = areasData.find(a => a.id === areaId);
    if (!area) return;
    
    showModal('Modifica Area', `
        <form id="editAreaForm">
            <div class="form-group">
                <label for="editAreaName">Nome Area *</label>
                <input type="text" id="editAreaName" value="${escapeHtml(area.name)}" required>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('editAreaForm').requestSubmit()">Salva</button>
        </div>
    `);
    
    document.getElementById('editAreaForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateArea(areaId);
    });
}

async function updateArea(areaId) {
    const name = document.getElementById('editAreaName').value;
    
    try {
        const response = await authService.authenticatedFetch(`/areas/${areaId}`, {
            method: 'PUT',
            body: { name }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Area aggiornata con successo', 'success');
            await loadAreas();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'aggiornamento', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function deleteArea(areaId) {
    if (!confirm('Sei sicuro di voler eliminare questa area? Verranno eliminati anche tutti i pali e rioni associati.')) return;
    
    try {
        const response = await authService.authenticatedFetch(`/areas/${areaId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Area eliminata con successo', 'success');
            await loadAreas();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'eliminazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

// ==================== STAKES ====================

async function loadStakes() {
    const tbody = document.getElementById('stakesTableBody');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Caricamento...</td></tr>';
    
    try {
        stakesData = await fetchData('/stakes');
        areasData = await fetchData('/areas');
        
        if (stakesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">Nessun palo trovato</td></tr>';
            return;
        }
        
        tbody.innerHTML = stakesData.map(stake => {
            const area = areasData.find(a => a.id === stake.area_id);
            return `
                <tr>
                    <td><strong>${escapeHtml(stake.name)}</strong></td>
                    <td>${area ? escapeHtml(area.name) : '-'}</td>
                    <td>${stake.wards?.length || 0}</td>
                    <td>${formatDate(stake.created_at)}</td>
                    <td class="actions">
                        <button class="btn-icon" onclick="editStake(${stake.id})" title="Modifica">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="btn-icon delete" onclick="deleteStake(${stake.id})" title="Elimina">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Errore nel caricamento</td></tr>';
    }
}

function showCreateStakeModal() {
    showModal('Nuovo Palo', `
        <form id="createStakeForm">
            <div class="form-group">
                <label for="newStakeName">Nome Palo *</label>
                <input type="text" id="newStakeName" required>
            </div>
            <div class="form-group">
                <label for="newStakeArea">Area *</label>
                <select id="newStakeArea" required>
                    <option value="">Seleziona un'area</option>
                    ${areasData.map(a => `<option value="${a.id}">${escapeHtml(a.name)}</option>`).join('')}
                </select>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('createStakeForm').requestSubmit()">Crea Palo</button>
        </div>
    `);
    
    document.getElementById('createStakeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createStake();
    });
}

async function createStake() {
    const name = document.getElementById('newStakeName').value;
    const area_id = parseInt(document.getElementById('newStakeArea').value);
    
    try {
        const response = await authService.authenticatedFetch('/stakes', {
            method: 'POST',
            body: { name, area_id }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Palo creato con successo', 'success');
            await loadStakes();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nella creazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function editStake(stakeId) {
    const stake = stakesData.find(s => s.id === stakeId);
    if (!stake) return;
    
    showModal('Modifica Palo', `
        <form id="editStakeForm">
            <div class="form-group">
                <label for="editStakeName">Nome Palo *</label>
                <input type="text" id="editStakeName" value="${escapeHtml(stake.name)}" required>
            </div>
            <div class="form-group">
                <label for="editStakeArea">Area *</label>
                <select id="editStakeArea" required>
                    ${areasData.map(a => `<option value="${a.id}" ${a.id === stake.area_id ? 'selected' : ''}>${escapeHtml(a.name)}</option>`).join('')}
                </select>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('editStakeForm').requestSubmit()">Salva</button>
        </div>
    `);
    
    document.getElementById('editStakeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateStake(stakeId);
    });
}

async function updateStake(stakeId) {
    const name = document.getElementById('editStakeName').value;
    const area_id = parseInt(document.getElementById('editStakeArea').value);
    
    try {
        const response = await authService.authenticatedFetch(`/stakes/${stakeId}`, {
            method: 'PUT',
            body: { name, area_id }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Palo aggiornato con successo', 'success');
            await loadStakes();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'aggiornamento', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function deleteStake(stakeId) {
    if (!confirm('Sei sicuro di voler eliminare questo palo? Verranno eliminati anche tutti i rioni associati.')) return;
    
    try {
        const response = await authService.authenticatedFetch(`/stakes/${stakeId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Palo eliminato con successo', 'success');
            await loadStakes();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'eliminazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

// ==================== WARDS ====================

async function loadWards() {
    const tbody = document.getElementById('wardsTableBody');
    tbody.innerHTML = '<tr><td colspan="4" class="loading">Caricamento...</td></tr>';
    
    try {
        wardsData = await fetchData('/wards');
        stakesData = await fetchData('/stakes');
        
        if (wardsData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="loading">Nessun rione trovato</td></tr>';
            return;
        }
        
        tbody.innerHTML = wardsData.map(ward => {
            const stake = stakesData.find(s => s.id === ward.stake_id);
            return `
                <tr>
                    <td><strong>${escapeHtml(ward.name)}</strong></td>
                    <td>${stake ? escapeHtml(stake.name) : '-'}</td>
                    <td>${formatDate(ward.created_at)}</td>
                    <td class="actions">
                        <button class="btn-icon" onclick="editWard(${ward.id})" title="Modifica">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        <button class="btn-icon delete" onclick="deleteWard(${ward.id})" title="Elimina">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">Errore nel caricamento</td></tr>';
    }
}

function showCreateWardModal() {
    showModal('Nuovo Rione', `
        <form id="createWardForm">
            <div class="form-group">
                <label for="newWardName">Nome Rione *</label>
                <input type="text" id="newWardName" required>
            </div>
            <div class="form-group">
                <label for="newWardStake">Palo *</label>
                <select id="newWardStake" required>
                    <option value="">Seleziona un palo</option>
                    ${stakesData.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('')}
                </select>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('createWardForm').requestSubmit()">Crea Rione</button>
        </div>
    `);
    
    document.getElementById('createWardForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createWard();
    });
}

async function createWard() {
    const name = document.getElementById('newWardName').value;
    const stake_id = parseInt(document.getElementById('newWardStake').value);
    
    try {
        const response = await authService.authenticatedFetch('/wards', {
            method: 'POST',
            body: { name, stake_id }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Rione creato con successo', 'success');
            await loadWards();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nella creazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function editWard(wardId) {
    const ward = wardsData.find(w => w.id === wardId);
    if (!ward) return;
    
    showModal('Modifica Rione', `
        <form id="editWardForm">
            <div class="form-group">
                <label for="editWardName">Nome Rione *</label>
                <input type="text" id="editWardName" value="${escapeHtml(ward.name)}" required>
            </div>
            <div class="form-group">
                <label for="editWardStake">Palo *</label>
                <select id="editWardStake" required>
                    ${stakesData.map(s => `<option value="${s.id}" ${s.id === ward.stake_id ? 'selected' : ''}>${escapeHtml(s.name)}</option>`).join('')}
                </select>
            </div>
        </form>
    `, `
        <div style="text-align:center">
            <button type="button" class="btn-cancel" onclick="closeModal()">Annulla</button>
            <button type="button" class="btn-primary" onclick="document.getElementById('editWardForm').requestSubmit()">Salva</button>
        </div>
    `);
    
    document.getElementById('editWardForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateWard(wardId);
    });
}

async function updateWard(wardId) {
    const name = document.getElementById('editWardName').value;
    const stake_id = parseInt(document.getElementById('editWardStake').value);
    
    try {
        const response = await authService.authenticatedFetch(`/wards/${wardId}`, {
            method: 'PUT',
            body: { name, stake_id }
        });
        
        if (response.ok) {
            closeModal();
            showToast('Rione aggiornato con successo', 'success');
            await loadWards();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'aggiornamento', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

async function deleteWard(wardId) {
    if (!confirm('Sei sicuro di voler eliminare questo rione?')) return;
    
    try {
        const response = await authService.authenticatedFetch(`/wards/${wardId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Rione eliminato con successo', 'success');
            await loadWards();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Errore nell\'eliminazione', 'error');
        }
    } catch (error) {
        showToast('Errore di rete', 'error');
    }
}

// ==================== UTILITIES ====================

function showModal(title, content, footer = '') {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('modalFooter').innerHTML = footer;
    document.getElementById('adminModal').classList.add('show');
}

function closeModal() {
    document.getElementById('adminModal').classList.remove('show');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-message">${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function switchSection(sectionId) {
    // Update active state in sidebar
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.dataset.section === sectionId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Show section
    document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${sectionId}`).classList.add('active');
    
    // Load section data
    loadSectionData(sectionId);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('it-IT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch {
        return '-';
    }
}

// Close modal on click outside
document.getElementById('adminModal').addEventListener('click', (e) => {
    if (e.target.id === 'adminModal') {
        closeModal();
    }
});

// Keyboard shortcut to close modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});
