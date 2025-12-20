#!/bin/bash
# Deployment script for Italian Hymns API

set -e

echo "🚀 Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="hymns-generator"
DEPLOY_USER="${DEPLOY_USER:-appuser}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/$APP_NAME}"
VENV_PATH="$DEPLOY_PATH/.venv"

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root or with sudo"
    exit 1
fi

# Create deployment directory
log_info "Creating deployment directory..."
mkdir -p "$DEPLOY_PATH"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_PATH"

# Copy application files
log_info "Copying application files..."
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.venv' --exclude='data/*.db' \
    ./ "$DEPLOY_PATH/"

# Create virtual environment
log_info "Setting up virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    sudo -u "$DEPLOY_USER" python3 -m venv "$VENV_PATH"
fi

# Install dependencies
log_info "Installing dependencies..."
sudo -u "$DEPLOY_USER" "$VENV_PATH/bin/pip" install --upgrade pip
sudo -u "$DEPLOY_USER" "$VENV_PATH/bin/pip" install -r "$DEPLOY_PATH/requirements.txt"

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p "$DEPLOY_PATH/data"
mkdir -p "$DEPLOY_PATH/logs"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_PATH/data"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_PATH/logs"

# Initialize database
log_info "Initializing database..."
sudo -u "$DEPLOY_USER" "$VENV_PATH/bin/python" "$DEPLOY_PATH/cli.py" db init || log_warn "Database already initialized"

# Setup systemd service
log_info "Setting up systemd service..."
cat > /etc/systemd/system/$APP_NAME.service <<EOF
[Unit]
Description=Italian Hymns API
After=network.target

[Service]
Type=notify
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$DEPLOY_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000 --workers 4
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and restart service
log_info "Reloading systemd and restarting service..."
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME

# Check service status
sleep 2
if systemctl is-active --quiet $APP_NAME; then
    log_info "✅ Deployment successful! Service is running."
    systemctl status $APP_NAME --no-pager
else
    log_error "❌ Deployment failed! Service is not running."
    systemctl status $APP_NAME --no-pager
    exit 1
fi

log_info "🎉 Deployment completed!"