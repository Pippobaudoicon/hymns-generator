# Hymn Dashboard Refactoring Plan

## Overview
Refactor the hymns application to support multiple tools with a clean, modular architecture. The dashboard will feature two main tools:
1. **Hymn Selector** (existing) - Generate hymn selections for Sunday services
2. **Hymn Player** (new) - Browse and play all hymns with audio accompaniment

## Architecture

### File Structure
```
hymns/static/
├── hymns.html                    # Renamed to hymn-selector.html
├── hymn-player.html              # NEW - Hymn player interface
├── css/
│   ├── styles.css                # Global styles (existing)
│   ├── auth.css                  # Auth styles (existing)
│   ├── dashboard.css             # Dashboard styles (existing)
│   ├── hymn-selector.css         # NEW - Selector-specific styles
│   └── hymn-player.css           # NEW - Player-specific styles
├── js/
│   ├── auth.js                   # Auth service (existing)
│   ├── api.js                    # API calls (existing)
│   ├── pwa.js                    # PWA functionality (existing)
│   ├── offline-storage.js        # Offline storage (existing)
│   ├── offline-sync.js           # Offline sync (existing)
│   ├── dashboard.js              # Dashboard module (existing)
│   ├── ui.js                     # UI utilities (existing)
│   ├── app.js                    # Hymn selector app (existing)
│   ├── hymn-player.js            # NEW - Hymn player app
│   └── components/               # NEW - Shared components
│       ├── hymn-card.js          # Reusable hymn card component
│       ├── audio-player.js       # Audio player component
│       ├── search-filter.js      # Search and filter component
│       └── user-menu.js          # User menu component
```

### Component Architecture

#### Shared Components (`/static/js/components/`)

1. **hymn-card.js** - Reusable hymn display card
   - Display hymn number, title, category
   - Show composers and authors
   - Action buttons (play, select, info)
   - Responsive design

2. **audio-player.js** - Audio playback component
   - Play/pause controls
   - Progress bar with seek
   - Volume control
   - Current time / duration display
   - Playlist support (next/previous)

3. **search-filter.js** - Search and filtering
   - Text search (number, title, composer, author)
   - Category filter dropdown
   - Tag filter chips
   - Clear filters button

4. **user-menu.js** - User menu component
   - Extract from duplicated code in HTML files
   - Reusable across all pages

## Implementation Plan

### Phase 1: Create Shared Components ✓
**Goal**: Extract reusable components to avoid code duplication

**Tasks**:
1. Create `/static/js/components/` directory
2. Implement `hymn-card.js` component
3. Implement `audio-player.js` component
4. Implement `search-filter.js` component
5. Implement `user-menu.js` component

**Files to create**:
- `hymns/static/js/components/hymn-card.js`
- `hymns/static/js/components/audio-player.js`
- `hymns/static/js/components/search-filter.js`
- `hymns/static/js/components/user-menu.js`

### Phase 2: Add API Endpoint for All Hymns ✓
**Goal**: Create endpoint to fetch all hymns with pagination and filtering

**Tasks**:
1. Add `/api/hymns/all` endpoint in `hymns/api/routes/hymns.py`
   - Support pagination (page, page_size)
   - Support search (query parameter)
   - Support category filter
   - Support tag filter
   - Return total count for pagination UI

**Files to modify**:
- `hymns/api/routes/hymns.py`

**Endpoint specification**:
```python
@router.get("/all", response_model=PaginatedHymnList)
async def get_all_hymns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    service: HymnService = Depends(get_hymn_service),
):
    """Get all hymns with pagination and filtering."""
```

### Phase 3: Refactor Hymn Selector ✓
**Goal**: Clean up existing hymn selector and use shared components

**Tasks**:
1. Rename `hymns.html` to `hymn-selector.html`
2. Extract selector-specific styles to `hymn-selector.css`
3. Update `app.js` to use shared components where applicable
4. Update dashboard link to point to new filename

**Files to modify**:
- `hymns/static/hymns.html` → `hymns/static/hymn-selector.html`
- Create `hymns/static/css/hymn-selector.css`
- Update `hymns/static/js/app.js`
- Update `hymns/static/js/dashboard.js`

### Phase 4: Create Hymn Player ✓
**Goal**: Build new hymn player tool

**Tasks**:
1. Create `hymn-player.html` page
   - Use shared user menu component
   - Back to dashboard button
   - Search and filter section
   - Hymn grid/list view
   - Audio player section (sticky bottom)
   
2. Create `hymn-player.css` stylesheet
   - Grid layout for hymn cards
   - Sticky audio player at bottom
   - Responsive design
   - Filter sidebar/panel
   
3. Create `hymn-player.js` application
   - Fetch hymns with pagination
   - Implement search and filtering
   - Handle audio playback
   - Manage playlist queue
   - Keyboard shortcuts (space = play/pause, arrow keys = next/prev)

**Files to create**:
- `hymns/static/hymn-player.html`
- `hymns/static/css/hymn-player.css`
- `hymns/static/js/hymn-player.js`

### Phase 5: Update Dashboard ✓
**Goal**: Add hymn player card to dashboard

**Tasks**:
1. Update `dashboard.js` to include new tool
2. Add appropriate icon and description
3. Ensure proper routing

**Files to modify**:
- `hymns/static/js/dashboard.js`

**New tool configuration**:
```javascript
{
    id: 'hymn-player',
    title: 'Lettore Inni',
    description: 'Sfoglia e ascolta tutti gli inni con accompagnamento audio. Cerca per numero, titolo, categoria o compositore.',
    icon: 'music', // or '🎵'
    url: '/hymn-player',
    badge: 'new',
    disabled: false,
}
```

### Phase 6: Add Backend Route ✓
**Goal**: Serve the new hymn player page

**Tasks**:
1. Add route in `app.py` to serve `hymn-player.html`

**Files to modify**:
- `hymns/app.py`

### Phase 7: Testing & Polish ✓
**Goal**: Ensure everything works smoothly

**Tasks**:
1. Test hymn selector with refactored code
2. Test hymn player functionality
   - Search and filtering
   - Audio playback
   - Pagination
   - Responsive design
3. Test offline functionality
4. Test authentication and authorization
5. Cross-browser testing
6. Mobile testing

## Features

### Hymn Player Features

#### Core Features
- **Browse All Hymns**: Paginated grid/list view of all hymns
- **Search**: Search by number, title, composer, or author
- **Filter**: Filter by category and tags
- **Audio Playback**: Play hymn accompaniment audio
- **Hymn Details**: View full hymn information (composers, authors, category, tags)

#### Audio Player Features
- Play/Pause control
- Progress bar with seek functionality
- Volume control
- Current time and duration display
- Next/Previous track navigation
- Keyboard shortcuts:
  - Space: Play/Pause
  - Arrow Left: Previous track
  - Arrow Right: Next track
  - Arrow Up: Volume up
  - Arrow Down: Volume down

#### UI Features
- Grid view (default) and list view toggle
- Responsive design (mobile, tablet, desktop)
- Sticky audio player at bottom
- Smooth animations and transitions
- Loading states and error handling
- Empty states for no results

## Data Model

### PaginatedHymnList (New)
```python
class PaginatedHymnList(BaseModel):
    hymns: List[Hymn]
    total: int
    page: int
    page_size: int
    total_pages: int
```

## API Endpoints

### New Endpoints
- `GET /api/hymns/all` - Get all hymns with pagination and filtering

### Existing Endpoints (unchanged)
- `GET /api/hymns/get_hymns` - Get hymns for service
- `GET /api/hymns/get_hymns_smart` - Get smart hymns for ward
- `GET /api/hymns/get_hymn` - Get single hymn
- `GET /api/hymns/get_replacement_hymn` - Get replacement hymn
- `GET /api/hymns/get_available_hymns` - Get available hymns
- `POST /api/hymns/swap_hymn` - Swap hymn in selection

## Styling Guidelines

### Color Scheme (from existing styles.css)
- Primary: `#003f87` (LDS blue)
- Secondary: `#6c757d`
- Success: `#28a745`
- Danger: `#dc3545`
- Warning: `#ffc107`

### Component Styling
- Use CSS Grid for layouts
- Use Flexbox for component internals
- Mobile-first responsive design
- Smooth transitions (0.3s ease)
- Box shadows for depth
- Border radius: 8px for cards, 4px for buttons

## Progressive Enhancement

### Offline Support
- Cache hymn data in IndexedDB
- Cache audio files for offline playback
- Show offline indicator
- Sync when back online

### PWA Features
- Add to home screen
- Offline functionality
- Background sync
- Push notifications (future)

## Migration Path

1. **No Breaking Changes**: Existing hymn selector continues to work
2. **Gradual Rollout**: New hymn player is added alongside
3. **User Feedback**: Gather feedback before making major changes
4. **Future Enhancements**: Based on usage patterns and feedback

## Future Enhancements

### Phase 8+ (Future)
- **Favorites**: Save favorite hymns
- **Playlists**: Create custom playlists
- **Lyrics Display**: Show hymn lyrics (if available)
- **Sheet Music**: Display sheet music (if available)
- **History**: Track recently played hymns
- **Sharing**: Share hymns via link
- **Download**: Download hymns for offline use
- **Transpose**: Transpose sheet music to different keys
- **Tempo Control**: Adjust playback speed

## Success Metrics

- Both tools accessible from dashboard
- No regression in hymn selector functionality
- Hymn player loads within 2 seconds
- Audio playback starts within 1 second
- Search results appear within 500ms
- Mobile-responsive on all screen sizes
- Works offline with cached data
- 95%+ uptime

## Notes

- Maintain backward compatibility
- Keep code DRY (Don't Repeat Yourself)
- Use ES6 modules for better organization
- Follow existing code style and conventions
- Add JSDoc comments for all functions
- Handle errors gracefully with user-friendly messages
- Optimize for performance (lazy loading, pagination)
- Ensure accessibility (ARIA labels, keyboard navigation)