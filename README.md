# Italian Hymns API

[![CI/CD Pipeline](https://github.com/Pippobaudoicon/hymns-generator/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/Pippobaudoicon/hymns-generator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional-grade RESTful API for managing and retrieving Italian hymns for the Church of Jesus Christ, featuring smart selection algorithms to avoid repetition and support for special occasions.

## ✨ Features

- **Smart Hymn Selection**: Intelligent algorithms to avoid recently used hymns
- **Sunday Date Tracking**: Automatically tracks hymns for the upcoming Sunday
- **Ward Management**: Track hymn usage per ward to ensure variety
- **Special Occasions**: Support for Christmas, Easter, and other festivities
- **JWT Authentication**: Secure login with role-based access control
- **Admin Panel**: Web-based management for users, areas, stakes, and wards
- **Role Hierarchy**: Superadmin → Area Manager → Stake Manager → Ward User
- **RESTful API**: Clean, well-documented endpoints
- **Database Tracking**: SQLAlchemy-based history tracking with selection dates
- **CLI Tools**: Comprehensive command-line interface
- **Comprehensive Testing**: Full test coverage with pytest
- **CI/CD Ready**: GitHub Actions workflow included

## 🚀 Quick Start

### Using Make (Recommended)

```bash
# Install dependencies
make install

# Initialize database
make db-init

# If upgrading from an older version, run migration
python database/migrations/add_updated_at_column.py

# Run development server
make run
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python cli.py db init

# If upgrading from an older version, run migrations
python database/migrations/add_updated_at_column.py
python database/migrations/add_auth_tables.py

# Create superadmin user
python scripts/create_superadmin.py

# Run server
python cli.py serve --reload
```

### Using PM2 (Recommended for Production)

```bash
# Quick deployment
./scripts/pm2-deploy.sh

# Or manually
make pm2-start

# View logs
make pm2-logs

# Restart
make pm2-restart

# Stop
make pm2-stop
```

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **Web Interface**: http://localhost:8000/
- **Login Page**: http://localhost:8000/login
- **Admin Panel**: http://localhost:8000/admin

### Main Endpoints

#### Get Hymns for Service (Smart Selection)
```http
GET /api/v1/get_hymns_smart?ward_name=MyWard&prima_domenica=false&domenica_festiva=false
```

Returns a list of hymns for a church service with smart selection to avoid repetition. **Automatically tracks the selection for the upcoming Sunday.**

**Query Parameters:**
- `ward_name` (string, required): Ward name for history tracking
- `prima_domenica` (bool): First Sunday (fast & testimony) - returns 3 hymns instead of 4
- `domenica_festiva` (bool): Festive Sunday (requires `tipo_festivita`)
- `tipo_festivita` (string): Type of festivity (`natale` or `pasqua`)
- `save_selection` (bool, default: true): Save this selection to database
- `selection_date` (string, optional): Selection date in YYYY-MM-DD format (defaults to next Sunday)

**Note:** When `selection_date` is not provided, the system automatically calculates and uses the date of the **next upcoming Sunday**. This ensures that hymn selections are always associated with the correct Sunday service date for future reference and historical tracking.

#### Get Hymns (Basic)
```http
GET /api/v1/get_hymns?prima_domenica=false&domenica_festiva=false
```

Returns a list of hymns without smart selection or history tracking.

**Query Parameters:**
- `prima_domenica` (bool): First Sunday (fast & testimony) - returns 3 hymns instead of 4
- `domenica_festiva` (bool): Festive Sunday (requires `tipo_festivita`)
- `tipo_festivita` (string): Type of festivity (`natale` or `pasqua`)

#### Get Single Hymn
```http
GET /api/v1/get_hymn?category=sacramento&tag=natale
```

Returns a single hymn filtered by number, category, or tag.

#### Additional Endpoints
- `GET /api/v1/categories` - List all categories
- `GET /api/v1/tags` - List all tags
- `GET /api/v1/stats` - Collection statistics
- `GET /api/v1/health` - Health check
- `GET /api/v1/wards` - List all wards
- `GET /api/v1/wards/{ward_name}/history` - Ward selection history

### 🔐 Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=myuser&password=mypassword
```

Returns a JWT access token:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

#### User Management (Admin only)
- `GET /auth/users` - List all users
- `POST /auth/users` - Create new user
- `GET /auth/users/{id}` - Get user by ID
- `PUT /auth/users/{id}` - Update user
- `DELETE /auth/users/{id}` - Delete user
- `PUT /auth/users/{id}/wards` - Assign wards to user

### 🏛️ Organization Endpoints

#### Areas (Superadmin only)
- `GET /areas` - List all areas
- `POST /areas` - Create new area
- `GET /areas/{id}` - Get area by ID
- `PUT /areas/{id}` - Update area
- `DELETE /areas/{id}` - Delete area

#### Stakes (Area Managers+)
- `GET /stakes` - List all stakes
- `POST /stakes` - Create new stake
- `GET /stakes/{id}` - Get stake by ID
- `PUT /stakes/{id}` - Update stake
- `DELETE /stakes/{id}` - Delete stake

#### Wards (Stake Managers+)
- `GET /wards` - List all wards
- `POST /wards` - Create new ward
- `PUT /wards/{id}` - Update ward
- `DELETE /wards/{id}` - Delete ward

## 🏗️ Project Structure

```
hymns-generator/
├── api/                    # API layer (FastAPI routes)
│   ├── routes/
│   │   ├── health.py      # Health check endpoints
│   │   ├── hymns.py       # Hymn-related endpoints
│   │   └── wards.py       # Ward management endpoints
│   └── routes.py          # Route aggregation
├── hymns/                 # Domain layer (business logic)
│   ├── models.py          # Pydantic models
│   ├── service.py         # Hymn service
│   └── exceptions.py      # Custom exceptions
├── database/              # Data layer
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database configuration
│   └── history_service.py # History tracking service
├── config/                # Configuration
│   └── settings.py        # Application settings
├── auth/                  # Authentication module
│   ├── models.py          # User, Area, Stake models
│   ├── schemas.py         # Pydantic schemas
│   ├── utils.py           # JWT and password utilities
│   ├── dependencies.py    # Auth dependencies
│   ├── routes.py          # Auth routes
│   └── organization_routes.py # Area/Stake routes
├── utils/                 # Utilities
│   ├── scraper.py         # Data scraping utilities
│   └── date_utils.py      # Date utility functions (Sunday calculation)
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest configuration
│   ├── test_api.py        # API tests
│   └── test_*.py          # Additional tests
├── scripts/               # Utility scripts
│   ├── deploy.sh          # Deployment script
│   └── backup.sh          # Backup script
├── docs/                  # Documentation
│   └── index.md           # Documentation home
├── data/                  # Data files
│   ├── italian_hymns_full.json
│   └── italian_hymns.csv
├── static/                # Static files
│   ├── index.html         # Web interface
│   ├── login.html         # Login page
│   ├── admin.html         # Admin panel
│   ├── css/
│   │   ├── styles.css     # Main styles
│   │   ├── auth.css       # Authentication styles
│   │   └── admin.css      # Admin panel styles
│   └── js/
│       ├── app.js         # Main application
│       ├── api.js         # API module
│       ├── ui.js          # UI module
│       ├── auth.js        # Authentication service
│       └── admin.js       # Admin panel logic
├── .github/               # GitHub configuration
│   └── workflows/
│       └── ci.yml         # CI/CD pipeline
├── app.py                 # Main FastAPI application
├── cli.py                 # Command-line interface
├── Makefile               # Task automation
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml         # Project configuration
├── .env.example           # Environment variables template
├── .editorconfig          # Editor configuration
├── .pre-commit-config.yaml # Pre-commit hooks
└── README.md              # This file
```

## 🛠️ Development

### Available Make Commands

```bash
make help           # Show all available commands
make install        # Install production dependencies
make dev-install    # Install development dependencies
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Run linters
make format         # Format code
make clean          # Clean up generated files
make run            # Run development server
make run-prod       # Run production server

# PM2 Commands
make pm2-start      # Start app with PM2
make pm2-stop       # Stop PM2 app
make pm2-restart    # Restart PM2 app
make pm2-reload     # Zero-downtime reload
make pm2-logs       # Show PM2 logs
make pm2-status     # Show PM2 status
make pm2-monit      # Monitor PM2 app

# Database Commands
make db-init        # Initialize database
make db-reset       # Reset database
make db-stats       # Show database statistics

# Data Commands
make scrape         # Scrape fresh hymn data
make stats          # Show hymn statistics
```

### CLI Commands

```bash
# Server management
python cli.py serve --reload --host 0.0.0.0 --port 8000

# Database management
python cli.py db init          # Initialize database
python cli.py db reset         # Reset database
python cli.py db stats         # Show database statistics

# Data management
python cli.py scrape           # Scrape fresh hymn data
python cli.py stats --verbose  # Show hymn statistics
python cli.py demo             # Create demo data

# Testing
python cli.py test             # Run tests
python cli.py test --coverage  # Run with coverage
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

Run all checks:
```bash
make lint format test
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before committing:

```bash
pip install pre-commit
pre-commit install
```

## 🚢 Deployment

### PM2 Deployment (Recommended)

1. **Using the PM2 deployment script:**
   ```bash
   ./scripts/pm2-deploy.sh
   ```

2. **Manual PM2 deployment:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Initialize database
   python cli.py db init
   
   # Start with PM2
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup
   ```

3. **PM2 Management:**
   ```bash
   pm2 status                    # Check status
   pm2 logs italian-hymns-api    # View logs
   pm2 restart italian-hymns-api # Restart
   pm2 reload italian-hymns-api  # Zero-downtime reload
   pm2 monit                     # Monitor resources
   ```

### Systemd Deployment (Alternative)

1. **Using the systemd deployment script:**
   ```bash
   sudo ./scripts/deploy.sh
   ```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key variables:
- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DATABASE_URL`: Database connection string
- `DATA_PATH`: Path to hymns data file
- `SECRET_KEY`: JWT signing secret (required for auth)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 1440 = 24h)

## 📊 Testing

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

## 📖 Documentation

Full documentation is available in the `docs/` directory. Build and serve locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Visit http://localhost:8001 to view the documentation.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters (`make lint test`)
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Church of Jesus Christ for the hymn data
- FastAPI for the excellent web framework
- All contributors who have helped improve this project

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ for the Italian-speaking members of the Church of Jesus Christ
