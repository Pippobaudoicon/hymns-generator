#!/bin/bash
# PM2 Deployment script for Italian Hymns API

set -e

echo "🚀 Starting PM2 deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="italian-hymns-api"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_DIR/.venv"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to project directory
cd "$PROJECT_DIR"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    log_error "PM2 is not installed. Install it with: npm install -g pm2"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment and install dependencies
log_info "Installing dependencies..."
source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Initialize database
log_info "Initializing database..."
python cli.py db init || log_warn "Database already initialized"

# Stop existing PM2 process if running
if pm2 list | grep -q "$APP_NAME"; then
    log_info "Stopping existing PM2 process..."
    pm2 stop "$APP_NAME" || true
    pm2 delete "$APP_NAME" || true
fi

# Start with PM2
log_info "Starting application with PM2..."
pm2 start ecosystem.config.js

# Save PM2 configuration
log_info "Saving PM2 configuration..."
pm2 save

# Setup PM2 startup script
log_info "Setting up PM2 startup script..."
pm2 startup | tail -n 1 | bash || log_warn "PM2 startup already configured"

# Check status
sleep 2
if pm2 list | grep -q "$APP_NAME.*online"; then
    log_info "✅ Deployment successful! Application is running."
    pm2 status
    echo ""
    log_info "Useful PM2 commands:"
    echo "  pm2 logs $APP_NAME       - View logs"
    echo "  pm2 restart $APP_NAME    - Restart app"
    echo "  pm2 reload $APP_NAME     - Zero-downtime reload"
    echo "  pm2 stop $APP_NAME       - Stop app"
    echo "  pm2 monit                - Monitor app"
else
    log_error "❌ Deployment failed! Application is not running."
    pm2 logs "$APP_NAME" --lines 50
    exit 1
fi

log_info "🎉 PM2 deployment completed!"