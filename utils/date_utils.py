"""Date utility functions for hymn selection."""

from datetime import datetime, timedelta
from typing import Optional


def get_next_sunday(from_date: Optional[datetime] = None) -> datetime:
    """
    Calculate the date of the next Sunday from a given date.

    Args:
        from_date: The date to calculate from (defaults to today)

    Returns:
        datetime: The date of the next Sunday at midnight

    Examples:
        >>> # If today is Monday, returns the upcoming Sunday
        >>> # If today is Sunday, returns today
        >>> next_sunday = get_next_sunday()
    """
    if from_date is None:
        from_date = datetime.now()

    # Get the current day of week (0=Monday, 6=Sunday)
    current_weekday = from_date.weekday()

    # Calculate days until Sunday (6 = Sunday)
    # If today is Sunday (6), days_until_sunday = 0
    # If today is Monday (0), days_until_sunday = 6
    if current_weekday == 6:
        # Today is Sunday
        days_until_sunday = 0
    else:
        # Days until next Sunday
        days_until_sunday = (6 - current_weekday) % 7

    # Calculate next Sunday
    next_sunday = from_date + timedelta(days=days_until_sunday)

    # Return at midnight (start of day)
    return next_sunday.replace(hour=0, minute=0, second=0, microsecond=0)


def format_sunday_date(date: datetime) -> str:
    """
    Format a Sunday date for display.

    Args:
        date: The date to format

    Returns:
        str: Formatted date string (e.g., "Sunday, December 15, 2024")
    """
    return date.strftime("%A, %B %d, %Y")
