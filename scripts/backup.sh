#!/bin/bash
# Backup script for Italian Hymns API data

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATA_DIR="${DATA_DIR:-./data}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="hymns_backup_$TIMESTAMP"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log_info "Starting backup..."

# Create backup archive
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    -C "$DATA_DIR" \
    --exclude='*.log' \
    .

log_info "Backup created: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Keep only last 7 backups
log_info "Cleaning old backups (keeping last 7)..."
cd "$BACKUP_DIR"
ls -t hymns_backup_*.tar.gz | tail -n +8 | xargs -r rm --

log_info "✅ Backup completed successfully!"