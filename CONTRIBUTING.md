# Contributing to Italian Hymns API

Thank you for your interest in contributing to the Italian Hymns API! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive environment.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment tool (venv)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/Pippobaudoicon/hymns-generator
   cd hymns-generator
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make dev-install
   ```

4. **Initialize the database**
   ```bash
   make db-init
   ```

5. **Run tests to verify setup**
   ```bash
   make test
   ```

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   make lint          # Check code style
   make format        # Format code
   make test          # Run tests
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 120 characters
- Use type hints where appropriate

### Code Organization

- Keep functions small and focused
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Follow SOLID principles

### Example

```python
from typing import List, Optional

def get_hymns_by_category(
    category: str,
    limit: Optional[int] = None
) -> List[Hymn]:
    """
    Retrieve hymns filtered by category.
    
    Args:
        category: The category to filter by
        limit: Maximum number of hymns to return
        
    Returns:
        List of Hymn objects matching the category
        
    Raises:
        ValueError: If category is invalid
    """
    # Implementation here
    pass
```

## Testing

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_api.py -v

# Run tests matching pattern
pytest -k "test_hymn" -v
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints

### Project Documentation

- Update README.md for user-facing changes
- Update docs/ for detailed documentation
- Include examples where appropriate

## Pull Request Process

1. **Ensure all checks pass**
   - All tests pass
   - Code is formatted correctly
   - No linting errors
   - Documentation is updated

2. **Create a clear PR description**
   - Describe what changes were made
   - Explain why the changes were necessary
   - Reference any related issues

3. **Request review**
   - Wait for maintainer review
   - Address any feedback
   - Keep the PR focused and manageable

4. **Merge**
   - Maintainers will merge once approved
   - Delete your feature branch after merge

## Reporting Issues

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and logs

### Feature Requests

Include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion
- Contact the maintainers

Thank you for contributing! 🎉