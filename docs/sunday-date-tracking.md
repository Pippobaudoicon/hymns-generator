# Sunday Date Tracking Feature

## Overview

The hymn selection system now automatically tracks the **date of the upcoming Sunday** for each hymn selection. This ensures that every time hymns are fetched, they are associated with the specific Sunday service they are intended for.

## Why This Feature?

### Historical Tracking
- Know exactly which Sunday each set of hymns was intended for
- Build a complete historical record of hymn selections by date

### Future Reference
- Query hymns by specific Sunday dates
- Analyze patterns over time (e.g., which hymns were used during Christmas season)

### Audit Trail
- See when hymns were fetched and for which Sunday they were meant
- Track changes and replacements with proper date context

## How It Works

### Automatic Sunday Calculation

When you request hymns without specifying a date, the system automatically:

1. Calculates the **next upcoming Sunday** from today's date
2. Associates the hymn selection with that Sunday date
3. Stores this date in the `selection_date` column of the database

### Date Calculation Logic

The [`get_next_sunday()`](../utils/date_utils.py:8) function:
- If today is Sunday → returns today at midnight
- If today is Monday-Saturday → returns the upcoming Sunday at midnight
- Always returns the date at 00:00:00 (start of day)

### Examples

```python
from utils.date_utils import get_next_sunday
from datetime import datetime

# If today is Monday, December 9, 2024
today = datetime(2024, 12, 9, 10, 30, 0)
next_sunday = get_next_sunday(today)
# Returns: Sunday, December 15, 2024 at 00:00:00

# If today is Sunday, December 15, 2024
today = datetime(2024, 12, 15, 14, 0, 0)
next_sunday = get_next_sunday(today)
# Returns: Sunday, December 15, 2024 at 00:00:00 (same day)
```

## API Usage

### Using Smart Selection (Recommended)

```http
GET /api/v1/get_hymns_smart?ward_name=MyWard
```

**Behavior:**
- Automatically calculates next Sunday
- Saves selection with that Sunday's date
- Returns hymns avoiding recent repetition

### Specifying a Custom Date

```http
GET /api/v1/get_hymns_smart?ward_name=MyWard&selection_date=2024-12-22
```

**Behavior:**
- Uses the specified date (December 22, 2024)
- Useful for planning ahead or historical data entry

## Database Schema

The [`HymnSelection`](../database/models.py:23) model now has separate columns for tracking dates:

```python
class HymnSelection(Base):
    """Represents a set of hymns selected for a particular Sunday."""
    __tablename__ = "hymn_selections"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    selection_date = Column(DateTime, nullable=False, index=True)  # ← Sunday service date
    prima_domenica = Column(Boolean, default=False)
    domenica_festiva = Column(Boolean, default=False)
    tipo_festivita = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)          # ← When record was created
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # ← When record was last modified
```

### Column Purposes

- **`selection_date`**: The date of the Sunday service (future date)
- **`created_at`**: When the hymn selection was first created
- **`updated_at`**: When the hymn selection was last modified (e.g., when a hymn was swapped)

## Code Changes

### 1. Date Utility Module
Created [`utils/date_utils.py`](../utils/date_utils.py) with:
- `get_next_sunday()` - Calculate next Sunday date
- `format_sunday_date()` - Format Sunday for display

### 2. History Service Updates
Updated [`database/history_service.py`](../database/history_service.py):
- [`get_smart_hymns()`](../database/history_service.py:69) - Uses next Sunday by default
- [`save_selection()`](../database/history_service.py:145) - Stores Sunday date

### 3. API Route Updates
Updated [`api/routes/hymns.py`](../api/routes/hymns.py):
- [`get_hymns_smart()`](../api/routes/hymns.py:66) - Calculates next Sunday when date not provided

## Benefits

### For Ward Leaders
- Clear record of which hymns were used on which Sundays
- Easy to review past selections by date
- Better planning for future services

### For System Administrators
- Accurate historical data
- Better analytics and reporting
- Proper audit trail

### For Developers
- Clean, testable date logic
- Consistent date handling across the system
- Well-documented utility functions

## Testing

Comprehensive tests in [`tests/test_date_utils.py`](../tests/test_date_utils.py) cover:
- Calculating next Sunday from any day of the week
- Handling month and year boundaries
- Ensuring midnight (00:00:00) timestamps
- Date formatting

Run tests:
```bash
make test
# or
pytest tests/test_date_utils.py -v
```

## Migration Notes

### Database Migration Required

If you have an existing database, you need to add the `updated_at` column:

```bash
# Run the migration script
python database/migrations/add_updated_at_column.py

# Or specify a custom database path
python database/migrations/add_updated_at_column.py path/to/your/hymns.db
```

The migration script will:
1. Check if the `updated_at` column already exists
2. Add the column if it doesn't exist
3. Initialize existing records with their `created_at` values
4. Verify the migration was successful

### New Installations

For new installations, the database will be created with the correct schema automatically when you run:

```bash
make db-init
# or
python cli.py db init
```

### Existing Data
- The `selection_date` column already existed in the schema
- Old records may have the creation timestamp instead of the Sunday date
- The new `updated_at` column tracks when records are modified

### Future Enhancements
Potential improvements:
- Bulk update tool to correct historical `selection_date` values to actual Sundays
- Report showing hymn usage by Sunday
- Calendar view of hymn selections
- Automatic reminders for upcoming Sundays
- Track who made changes (add `updated_by` column)