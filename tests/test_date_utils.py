"""Tests for date utility functions."""

from datetime import datetime, timedelta

import pytest

from utils.date_utils import format_sunday_date, get_next_sunday


class TestGetNextSunday:
    """Tests for get_next_sunday function."""
    
    def test_from_monday_returns_next_sunday(self):
        """Test that from Monday, it returns the upcoming Sunday."""
        # Monday, December 9, 2024
        monday = datetime(2024, 12, 9, 10, 30, 0)
        result = get_next_sunday(monday)
        
        # Should return Sunday, December 15, 2024 at midnight
        expected = datetime(2024, 12, 15, 0, 0, 0)
        assert result == expected
        assert result.weekday() == 6  # Sunday
    
    def test_from_sunday_returns_same_day(self):
        """Test that from Sunday, it returns the same Sunday."""
        # Sunday, December 15, 2024
        sunday = datetime(2024, 12, 15, 10, 30, 0)
        result = get_next_sunday(sunday)
        
        # Should return the same Sunday at midnight
        expected = datetime(2024, 12, 15, 0, 0, 0)
        assert result == expected
        assert result.weekday() == 6  # Sunday
    
    def test_from_saturday_returns_next_day(self):
        """Test that from Saturday, it returns the next day (Sunday)."""
        # Saturday, December 14, 2024
        saturday = datetime(2024, 12, 14, 10, 30, 0)
        result = get_next_sunday(saturday)
        
        # Should return Sunday, December 15, 2024 at midnight
        expected = datetime(2024, 12, 15, 0, 0, 0)
        assert result == expected
        assert result.weekday() == 6  # Sunday
    
    def test_from_tuesday_returns_next_sunday(self):
        """Test that from Tuesday, it returns the upcoming Sunday."""
        # Tuesday, December 10, 2024
        tuesday = datetime(2024, 12, 10, 15, 45, 30)
        result = get_next_sunday(tuesday)
        
        # Should return Sunday, December 15, 2024 at midnight
        expected = datetime(2024, 12, 15, 0, 0, 0)
        assert result == expected
        assert result.weekday() == 6  # Sunday
    
    def test_returns_midnight(self):
        """Test that the result is always at midnight."""
        # Any day with time
        some_day = datetime(2024, 12, 11, 14, 23, 45, 123456)
        result = get_next_sunday(some_day)
        
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0
    
    def test_default_uses_current_date(self):
        """Test that calling without arguments uses current date."""
        result = get_next_sunday()
        
        # Should return a Sunday
        assert result.weekday() == 6
        
        # Should be in the future or today
        now = datetime.now()
        assert result >= now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Should be within the next 7 days
        assert result <= now + timedelta(days=7)
    
    def test_across_month_boundary(self):
        """Test that it works correctly across month boundaries."""
        # Thursday, December 26, 2024
        thursday = datetime(2024, 12, 26, 10, 0, 0)
        result = get_next_sunday(thursday)
        
        # Should return Sunday, December 29, 2024
        expected = datetime(2024, 12, 29, 0, 0, 0)
        assert result == expected
        assert result.weekday() == 6  # Sunday
    
    def test_across_year_boundary(self):
        """Test that it works correctly across year boundaries."""
        # Friday, December 27, 2024
        friday = datetime(2024, 12, 27, 10, 0, 0)
        result = get_next_sunday(friday)
        
        # Should return Sunday, December 29, 2024 (not crossing year yet)
        expected = datetime(2024, 12, 29, 0, 0, 0)
        assert result == expected
        
        # Now test from December 30 (Monday)
        monday = datetime(2024, 12, 30, 10, 0, 0)
        result = get_next_sunday(monday)
        
        # Should return Sunday, January 5, 2025
        expected = datetime(2025, 1, 5, 0, 0, 0)
        assert result == expected
        assert result.weekday() == 6  # Sunday


class TestFormatSundayDate:
    """Tests for format_sunday_date function."""
    
    def test_formats_date_correctly(self):
        """Test that date is formatted correctly."""
        date = datetime(2024, 12, 15, 0, 0, 0)
        result = format_sunday_date(date)
        
        assert result == "Sunday, December 15, 2024"
    
    def test_formats_different_months(self):
        """Test formatting for different months."""
        date = datetime(2024, 1, 7, 0, 0, 0)
        result = format_sunday_date(date)
        
        assert result == "Sunday, January 07, 2024"