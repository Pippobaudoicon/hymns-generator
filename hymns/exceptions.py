"""Custom exceptions for the Italian Hymns API."""

from fastapi import HTTPException, status


class HymnAPIException(HTTPException):
    """Base exception for hymn API errors."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class DataNotFoundError(HymnAPIException):
    """Raised when hymn data cannot be found."""
    
    def __init__(self, detail: str = "Hymn data not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class InvalidFilterError(HymnAPIException):
    """Raised when invalid filter criteria are provided."""
    
    def __init__(self, detail: str = "Invalid filter criteria"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class InsufficientHymnsError(HymnAPIException):
    """Raised when not enough hymns are available for selection."""
    
    def __init__(self, detail: str = "Insufficient hymns available for selection"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class DataLoadError(HymnAPIException):
    """Raised when hymn data cannot be loaded."""
    
    def __init__(self, detail: str = "Failed to load hymn data"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
