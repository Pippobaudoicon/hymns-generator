.PHONY: help install dev-install test lint format clean run pm2-start pm2-stop pm2-restart pm2-logs docker-build docker-up docker-down db-init db-reset

# Default target
help:
	@echo "Italian Hymns API - Available commands:"
	@echo ""
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make lint           - Run linters (flake8, mypy)"
	@echo "  make format         - Format code with black and isort"
	@echo "  make clean          - Clean up generated files"
	@echo "  make run            - Run development server"
	@echo "  make run-prod       - Run production server with gunicorn"
	@echo ""
	@echo "PM2 Commands:"
	@echo "  make pm2-start      - Start app with PM2"
	@echo "  make pm2-stop       - Stop PM2 app"
	@echo "  make pm2-restart    - Restart PM2 app"
	@echo "  make pm2-reload     - Reload PM2 app (zero-downtime)"
	@echo "  make pm2-logs       - Show PM2 logs"
	@echo "  make pm2-status     - Show PM2 status"
	@echo "  make pm2-monit      - Monitor PM2 app"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-init        - Initialize database"
	@echo "  make db-reset       - Reset database"
	@echo ""
	@echo "Data Commands:"
	@echo "  make scrape         - Scrape fresh hymn data"
	@echo "  make stats          - Show hymn statistics"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=api --cov=hymns --cov=database --cov-report=html --cov-report=term-missing

test-watch:
	pytest-watch tests/ -v

# Code quality
lint:
	flake8 api/ hymns/ database/ config/ utils/ --max-line-length=120
	mypy api/ hymns/ database/ config/ utils/ --ignore-missing-imports

format:
	black api/ hymns/ database/ config/ utils/ tests/ cli.py lds_tools.py
	isort api/ hymns/ database/ config/ utils/ tests/ cli.py lds_tools.py

check-format:
	black --check api/ hymns/ database/ config/ utils/ tests/ cli.py lds_tools.py
	isort --check-only api/ hymns/ database/ config/ utils/ tests/ cli.py lds_tools.py

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Running
run:
	python cli.py serve --reload

run-prod:
	gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000 --workers 4

# PM2 Process Management
pm2-start:
	pm2 start ecosystem.config.js

pm2-stop:
	pm2 stop italian-hymns-api

pm2-restart:
	pm2 restart italian-hymns-api

pm2-reload:
	pm2 reload italian-hymns-api

pm2-delete:
	pm2 delete italian-hymns-api

pm2-logs:
	pm2 logs italian-hymns-api

pm2-status:
	pm2 status

pm2-monit:
	pm2 monit

# Docker (optional)
docker-build:
	docker build -t italian-hymns-api:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database
db-init:
	python cli.py db init

db-reset:
	python cli.py db reset

db-stats:
	python cli.py db stats

# Data management
scrape:
	python cli.py scrape

stats:
	python cli.py stats --verbose

demo:
	python cli.py demo

# CI/CD
ci: lint test

# Development workflow
dev: clean dev-install db-init run

# Production deployment
deploy: clean install db-init
	@echo "Ready for production deployment"