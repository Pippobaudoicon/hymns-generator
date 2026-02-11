/**
 * Audio Player Component
 * Reusable audio player with controls for hymn playback
 */

export class AudioPlayer {
    constructor(container) {
        this.container = container;
        this.audio = new Audio();
        this.currentHymn = null;
        this.playlist = [];
        this.currentIndex = -1;
        this.isPlaying = false;
        
        // Bind methods
        this.play = this.play.bind(this);
        this.pause = this.pause.bind(this);
        this.togglePlay = this.togglePlay.bind(this);
        this.seek = this.seek.bind(this);
        this.setVolume = this.setVolume.bind(this);
        this.next = this.next.bind(this);
        this.previous = this.previous.bind(this);
        
        this.init();
    }

    init() {
        this.createPlayerUI();
        this.attachEventListeners();
        this.setupKeyboardShortcuts();
    }

    createPlayerUI() {
        this.container.innerHTML = `
            <div class="audio-player" id="audioPlayer">
                <div class="audio-player-info">
                    <div class="audio-player-hymn-number" id="playerHymnNumber">-</div>
                    <div class="audio-player-hymn-details">
                        <div class="audio-player-hymn-title" id="playerHymnTitle">Nessun inno selezionato</div>
                        <div class="audio-player-hymn-category" id="playerHymnCategory"></div>
                    </div>
                </div>
                
                <div class="audio-player-controls">
                    <button class="audio-player-btn" id="prevBtn" title="Precedente" disabled>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="19 20 9 12 19 4 19 20"></polygon>
                            <line x1="5" y1="19" x2="5" y2="5"></line>
                        </svg>
                    </button>
                    
                    <button class="audio-player-btn audio-player-btn-play" id="playPauseBtn" title="Riproduci" disabled>
                        <svg class="play-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                        <svg class="pause-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display: none;">
                            <rect x="6" y="4" width="4" height="16"></rect>
                            <rect x="14" y="4" width="4" height="16"></rect>
                        </svg>
                    </button>
                    
                    <button class="audio-player-btn" id="nextBtn" title="Successivo" disabled>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 4 15 12 5 20 5 4"></polygon>
                            <line x1="19" y1="5" x2="19" y2="19"></line>
                        </svg>
                    </button>
                </div>
                
                <div class="audio-player-progress">
                    <span class="audio-player-time" id="currentTime">0:00</span>
                    <div class="audio-player-progress-bar" id="progressBar">
                        <div class="audio-player-progress-fill" id="progressFill"></div>
                        <div class="audio-player-progress-handle" id="progressHandle"></div>
                    </div>
                    <span class="audio-player-time" id="duration">0:00</span>
                </div>
                
                <div class="audio-player-volume">
                    <button class="audio-player-btn audio-player-btn-volume" id="volumeBtn" title="Volume">
                        <svg class="volume-high" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                        <svg class="volume-muted" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display: none;">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <line x1="23" y1="9" x2="17" y2="15"></line>
                            <line x1="17" y1="9" x2="23" y2="15"></line>
                        </svg>
                    </button>
                    <div class="audio-player-volume-slider" id="volumeSlider">
                        <div class="audio-player-volume-fill" id="volumeFill"></div>
                        <div class="audio-player-volume-handle" id="volumeHandle"></div>
                    </div>
                </div>
            </div>
        `;

        // Get references to elements
        this.elements = {
            player: this.container.querySelector('#audioPlayer'),
            hymnNumber: this.container.querySelector('#playerHymnNumber'),
            hymnTitle: this.container.querySelector('#playerHymnTitle'),
            hymnCategory: this.container.querySelector('#playerHymnCategory'),
            playPauseBtn: this.container.querySelector('#playPauseBtn'),
            prevBtn: this.container.querySelector('#prevBtn'),
            nextBtn: this.container.querySelector('#nextBtn'),
            playIcon: this.container.querySelector('.play-icon'),
            pauseIcon: this.container.querySelector('.pause-icon'),
            currentTime: this.container.querySelector('#currentTime'),
            duration: this.container.querySelector('#duration'),
            progressBar: this.container.querySelector('#progressBar'),
            progressFill: this.container.querySelector('#progressFill'),
            progressHandle: this.container.querySelector('#progressHandle'),
            volumeBtn: this.container.querySelector('#volumeBtn'),
            volumeSlider: this.container.querySelector('#volumeSlider'),
            volumeFill: this.container.querySelector('#volumeFill'),
            volumeHandle: this.container.querySelector('#volumeHandle'),
            volumeHigh: this.container.querySelector('.volume-high'),
            volumeMuted: this.container.querySelector('.volume-muted')
        };
    }

    attachEventListeners() {
        // Play/Pause button
        this.elements.playPauseBtn.addEventListener('click', this.togglePlay);
        
        // Previous/Next buttons
        this.elements.prevBtn.addEventListener('click', this.previous);
        this.elements.nextBtn.addEventListener('click', this.next);
        
        // Progress bar
        this.elements.progressBar.addEventListener('click', (e) => {
            const rect = this.elements.progressBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            this.seek(percent);
        });
        
        // Volume controls
        this.elements.volumeBtn.addEventListener('click', () => {
            if (this.audio.volume > 0) {
                this.previousVolume = this.audio.volume;
                this.setVolume(0);
            } else {
                this.setVolume(this.previousVolume || 0.5);
            }
        });
        
        this.elements.volumeSlider.addEventListener('click', (e) => {
            const rect = this.elements.volumeSlider.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            this.setVolume(percent);
        });
        
        // Audio events
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('ended', () => this.onEnded());
        this.audio.addEventListener('play', () => this.onPlay());
        this.audio.addEventListener('pause', () => this.onPause());
        this.audio.addEventListener('error', (e) => this.onError(e));
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts if player is active and not typing in input
            if (!this.currentHymn || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch(e.key) {
                case ' ':
                    e.preventDefault();
                    this.togglePlay();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previous();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.next();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.setVolume(Math.min(1, this.audio.volume + 0.1));
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.setVolume(Math.max(0, this.audio.volume - 0.1));
                    break;
            }
        });
    }

    loadHymn(hymn, playlist = null, index = -1) {
        if (!hymn.audio_url) {
            console.warn('Hymn has no audio URL:', hymn);
            return;
        }

        this.currentHymn = hymn;
        this.audio.src = hymn.audio_url;
        
        // Update playlist if provided
        if (playlist) {
            this.playlist = playlist;
            this.currentIndex = index;
        }
        
        // Normalize hymn data (handle both field name formats)
        const hymnNumber = hymn.number || hymn.songNumber;
        const hymnCategory = hymn.category || hymn.bookSectionTitle;
        
        // Update UI
        this.elements.hymnNumber.textContent = `#${hymnNumber || '?'}`;
        this.elements.hymnTitle.textContent = hymn.title || 'Untitled';
        this.elements.hymnCategory.textContent = hymnCategory || '';
        
        // Enable controls
        this.elements.playPauseBtn.disabled = false;
        this.updateNavigationButtons();
        
        // Show player if hidden
        this.elements.player.classList.add('active');
    }

    play() {
        if (this.currentHymn && this.audio.src) {
            this.audio.play().catch(err => {
                console.error('Error playing audio:', err);
                this.showError('Errore durante la riproduzione');
            });
        }
    }

    pause() {
        this.audio.pause();
    }

    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    seek(percent) {
        if (this.audio.duration) {
            this.audio.currentTime = this.audio.duration * percent;
        }
    }

    setVolume(volume) {
        this.audio.volume = Math.max(0, Math.min(1, volume));
        this.updateVolumeUI();
    }

    next() {
        if (this.playlist.length > 0 && this.currentIndex < this.playlist.length - 1) {
            this.loadHymn(this.playlist[this.currentIndex + 1], this.playlist, this.currentIndex + 1);
            this.play();
        }
    }

    previous() {
        if (this.playlist.length > 0 && this.currentIndex > 0) {
            this.loadHymn(this.playlist[this.currentIndex - 1], this.playlist, this.currentIndex - 1);
            this.play();
        }
    }

    updateProgress() {
        if (this.audio.duration) {
            const percent = (this.audio.currentTime / this.audio.duration) * 100;
            this.elements.progressFill.style.width = `${percent}%`;
            this.elements.progressHandle.style.left = `${percent}%`;
            this.elements.currentTime.textContent = this.formatTime(this.audio.currentTime);
        }
    }

    updateDuration() {
        this.elements.duration.textContent = this.formatTime(this.audio.duration);
    }

    updateVolumeUI() {
        const percent = this.audio.volume * 100;
        this.elements.volumeFill.style.width = `${percent}%`;
        this.elements.volumeHandle.style.left = `${percent}%`;
        
        // Update volume icon
        if (this.audio.volume === 0) {
            this.elements.volumeHigh.style.display = 'none';
            this.elements.volumeMuted.style.display = 'block';
        } else {
            this.elements.volumeHigh.style.display = 'block';
            this.elements.volumeMuted.style.display = 'none';
        }
    }

    updateNavigationButtons() {
        if (this.playlist.length > 0) {
            this.elements.prevBtn.disabled = this.currentIndex <= 0;
            this.elements.nextBtn.disabled = this.currentIndex >= this.playlist.length - 1;
        } else {
            this.elements.prevBtn.disabled = true;
            this.elements.nextBtn.disabled = true;
        }
    }

    onPlay() {
        this.isPlaying = true;
        this.elements.playIcon.style.display = 'none';
        this.elements.pauseIcon.style.display = 'block';
    }

    onPause() {
        this.isPlaying = false;
        this.elements.playIcon.style.display = 'block';
        this.elements.pauseIcon.style.display = 'none';
    }

    onEnded() {
        // Auto-play next if available
        if (this.playlist.length > 0 && this.currentIndex < this.playlist.length - 1) {
            this.next();
        } else {
            this.pause();
        }
    }

    onError(e) {
        console.error('Audio error:', e);
        this.showError('Errore durante il caricamento dell\'audio');
    }

    showError(message) {
        // You can implement a toast notification here
        console.error(message);
    }

    formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    destroy() {
        this.audio.pause();
        this.audio.src = '';
        this.currentHymn = null;
        this.playlist = [];
        this.currentIndex = -1;
    }
}

export default AudioPlayer;