# Italian Hymns API Documentation

Welcome to the Italian Hymns API documentation. This API provides a comprehensive solution for managing and retrieving Italian hymns for the Church of Jesus Christ of Latter day Saints.

## Overview

The Italian Hymns API is a RESTful service that:

- Generates hymn selections for church services
- Tracks hymn usage history to avoid repetition
- Supports special occasions (Christmas, Easter, etc.)
- Provides smart selection based on ward history
- Offers comprehensive hymn search and filtering

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd hymns

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install

# Initialize database
make db-init

# Run development server
make run
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Features

### Smart Hymn Selection

The API uses intelligent algorithms to:
- Avoid recently used hymns
- Respect category requirements (e.g., sacrament hymns)
- Handle special occasions appropriately
- Maintain variety across weeks

### Ward Management

Track hymn usage per ward to ensure:
- No repetition within recent weeks
- Fair distribution across categories
- Appropriate selections for each occasion

### Comprehensive API

- RESTful endpoints for all operations
- OpenAPI/Swagger documentation
- Comprehensive error handling
- Rate limiting support

## Architecture

The project follows clean architecture principles:

```
├── api/              # API layer (FastAPI routes)
├── hymns/            # Domain layer (business logic)
├── database/         # Data layer (SQLAlchemy models)
├── config/           # Configuration management
├── utils/            # Utility functions
├── tests/            # Test suite
├── scripts/          # Deployment and utility scripts
└── docs/             # Documentation
```

## Next Steps

- [API Reference](api-reference.md) - Detailed API documentation
- [Configuration](configuration.md) - Configuration options
- [Development](development.md) - Development guide
- [Deployment](deployment.md) - Deployment instructions