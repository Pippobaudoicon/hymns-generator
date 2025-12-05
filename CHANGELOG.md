# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional project structure following big tech standards
- Comprehensive configuration files (.env.example, .editorconfig, .dockerignore)
- Docker and Docker Compose support for containerization
- Makefile for common development tasks
- Pre-commit hooks configuration
- GitHub Actions CI/CD pipeline
- Deployment scripts (deploy.sh, backup.sh)
- MkDocs documentation setup
- Enhanced test configuration with conftest.py
- CONTRIBUTING.md with development guidelines
- MIT License
- Comprehensive README with badges and detailed instructions

### Changed
- Renamed main application file from `lds_tools.py` to `app.py`
- Updated all references to use new `app.py` naming
- Improved project documentation structure
- Enhanced code organization and modularity

### Fixed
- Standardized import paths across the project
- Improved error handling and logging

## [1.0.0] - 2024-12-05

### Added
- Initial release of Italian Hymns API
- RESTful API for hymn management
- Smart hymn selection algorithm
- Ward-based history tracking
- Support for special occasions (Christmas, Easter)
- SQLAlchemy database integration
- FastAPI web framework
- Command-line interface (CLI)
- Web scraper for hymn data
- Comprehensive test suite
- API documentation with Swagger/OpenAPI
- Static web interface for hymn selection

### Features
- Get hymns for church services with customizable rules
- Single hymn retrieval by number, category, or tag
- Avoid repetition with smart selection
- Track hymn usage per ward
- Support for first Sunday (fast & testimony)
- Support for festive Sundays (Christmas, Easter)
- Health check endpoint
- Statistics and analytics endpoints

### Technical
- FastAPI for high-performance API
- SQLAlchemy for database ORM
- Pydantic for data validation
- Uvicorn/Gunicorn for production serving
- Pytest for testing
- Clean architecture with separation of concerns
- SOLID principles implementation

---

## Release Notes

### Version 1.0.0 - Initial Release

This is the first stable release of the Italian Hymns API. The application provides a complete solution for managing hymn selections for Italian-speaking congregations of the Church of Jesus Christ.

**Key Features:**
- Smart hymn selection to avoid repetition
- Ward-specific history tracking
- Support for special occasions
- RESTful API with comprehensive documentation
- Command-line tools for data management
- Production-ready deployment options

**Getting Started:**
See the [README.md](README.md) for installation and usage instructions.

**Contributing:**
We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

[Unreleased]: https://github.com/yourusername/italian-hymns-api/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/italian-hymns-api/releases/tag/v1.0.0