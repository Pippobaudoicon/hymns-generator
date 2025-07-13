# Italian Hymns RESTful API

This project provides a RESTful API for generating and retrieving Italian hymns for the Church of Jesus Christ, with special logic for different occasions (e.g., sacrament, festive Sundays, etc.).

## Features

- **Hymn Selection**: Generate lists of hymns for church services with customizable rules
- **Single Hymn Retrieval**: Get specific hymns by number, category, or tag
- **Fresh Results**: Always returns randomized results (no caching)
- **Error Handling**: Comprehensive error handling and validation
- **Well-Organized**: Clean, SOLID-compliant code structure
- **Command Line Interface**: CLI for data management and server operations
- **Extensible**: Easy to extend with new features and categories

## API Endpoints

### `GET /api/v1/get_hymns`
Returns a list of hymns according to the rules:
- 3 hymns for the first Sunday (fast & testimony), 4 otherwise
- The second hymn is always from the "Sacramento" category
- Excludes "Occasioni speciali" and festive hymns unless requested

**Query Parameters:**
- `prima_domenica` (bool): If true, returns 3 hymns (first Sunday). Default: false
- `domenica_festiva` (bool): If true, includes festive hymns. Requires `tipo_festivita`
- `tipo_festivita` (string): Required if `domenica_festiva` is true. Either `natale` or `pasqua`

**Examples:**
- `/api/v1/get_hymns`
- `/api/v1/get_hymns?prima_domenica=true`
- `/api/v1/get_hymns?domenica_festiva=true&tipo_festivita=natale`

### `GET /api/v1/get_hymn`
Returns a single hymn filtered by number, category, or tag (all optional, AND logic).
If multiple hymns match, one is returned at random.

**Query Parameters:**
- `number` (int): Hymn number
- `category` (string): Hymn category (e.g., "Sacramento")
- `tag` (string): Hymn tag (e.g., "natale", "pasqua")

**Examples:**
- `/api/v1/get_hymn?category=sacramento`
- `/api/v1/get_hymn?tag=natale`
- `/api/v1/get_hymn?number=1`
- `/api/v1/get_hymn?category=sacramento&tag=natale`

### Additional Endpoints
- `GET /api/v1/categories` - Get all available categories
- `GET /api/v1/tags` - Get all available tags
- `GET /api/v1/stats` - Get collection statistics
- `GET /api/v1/health` - Health check endpoint

## Project Structure

```
hymns/
├── api/                    # API layer
│   ├── __init__.py
│   └── routes.py          # FastAPI route definitions
├── hymns/                 # Core domain logic
│   ├── __init__.py
│   ├── models.py          # Pydantic data models
│   ├── service.py         # Business logic
│   └── exceptions.py      # Custom exceptions
├── config/                # Configuration
│   ├── __init__.py
│   └── settings.py        # Application settings
├── utils/                 # Utilities
│   ├── __init__.py
│   └── scraper.py         # Data scraping utilities
├── data/                  # Data files
│   ├── italian_hymns_full.json
│   └── italian_hymns.csv
├── lds_tools.py          # Main FastAPI application
├── cli.py                # Command line interface
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation and Setup

1. **Clone the repository and navigate to the project directory**

2. **Create and activate a Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

The project includes a CLI for various operations:

```bash
# Show available commands
python cli.py --help

# Scrape fresh hymn data from the web
python cli.py scrape

# Show hymn collection statistics
python cli.py stats

# Show detailed statistics
python cli.py stats --verbose

# Start the development server
python cli.py serve --reload

# Start server on custom host/port
python cli.py serve --host 0.0.0.0 --port 8080
```

### Development Server

Start the development server with auto-reload:
```bash
python cli.py serve --reload
```

Or using uvicorn directly:
```bash
uvicorn lds_tools:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

For production, use Gunicorn:
```bash
gunicorn -k uvicorn.workers.UvicornWorker lds_tools:app --bind 0.0.0.0:8000
```

For production using PM2:
```bash
pm2 start .venv/bin/gunicorn \
  --name lds_tools \
  --interpreter none \
  -- \
  -k uvicorn.workers.UvicornWorker lds_tools:app --bind 0.0.0.0:8000
```

## Configuration

The application can be configured using environment variables:

- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DATA_PATH`: Path to hymns data file (default: data/italian_hymns_full.json)

## Data Management

### Updating Hymn Data

To fetch fresh hymn data from the Church website:
```bash
python cli.py scrape
```

This will update both `data/italian_hymns_full.json` and `data/italian_hymns.csv`.

### Data Format

The hymn data includes:
- **number**: Hymn number
- **title**: Hymn title
- **category**: Hymn category (e.g., "Sacramento", "Restaurazione")
- **tags**: List of tags (e.g., ["natale"], ["pasqua"])

## API Documentation

When the server is running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Development

### Code Organization

The codebase follows SOLID principles and is organized into clear layers:

- **API Layer** (`api/`): FastAPI routes and HTTP handling
- **Domain Layer** (`hymns/`): Core business logic and models
- **Configuration** (`config/`): Application settings
- **Utilities** (`utils/`): Helper functions and tools

### Error Handling

The API includes comprehensive error handling:
- Custom exceptions for different error types
- Proper HTTP status codes
- Detailed error messages for debugging

### Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests (when test files are created)
pytest
```

## Deployment Notes

- Use a process manager (e.g., PM2, systemd) to keep the app running
- Use Nginx as a reverse proxy for HTTPS and performance
- Configure CORS settings for production
- Set up proper logging and monitoring

## Contributing

1. Follow the existing code structure and patterns
2. Add proper error handling and logging
3. Update documentation for new features
4. Test your changes thoroughly

## Notes

- All endpoints return fresh, randomized results (no cache)
- The code follows OOP and SOLID principles for easy extension
- Logging is configured for both development and production
- The CLI provides easy access to common operations
