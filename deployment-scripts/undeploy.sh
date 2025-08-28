#!/bin/bash

# LMAIK User Study - Undeployment Script
# WARNING: This script will completely remove the application and its data.

set -e # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="lmaik-userstudy"
APP_USER="lmaik"
APP_DIR="/opt/$APP_NAME"
SERVICE_NAME="lmaik-userstudy"
NGINX_SITE="lmaik-userstudy"
LOG_DIR="/var/log/$APP_NAME"

echo -e "${RED}WARNING: This script will permanently delete the '$APP_NAME' application, user, and all associated data.${NC}"
echo -e "${YELLOW}This includes:${NC}"
echo -e "- The application service ($SERVICE_NAME)"
echo -e "- The Nginx site configuration"
echo -e "- The application directory ($APP_DIR)"
echo -e "- The log directory ($LOG_DIR)"
echo -e "- The application user ($APP_USER)"
echo ""
echo -e "${YELLOW}Starting undeployment in 5 seconds... Press Ctrl+C to cancel.${NC}"
sleep 5

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root or with sudo."
fi

log "Starting undeployment of $APP_NAME..."

# Stop and disable systemd service
log "Stopping and disabling systemd service..."
systemctl stop $SERVICE_NAME || echo "Service not running."
systemctl disable $SERVICE_NAME || echo "Service not enabled."
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload

# Remove Nginx configuration
log "Removing Nginx configuration..."
rm -f /etc/nginx/sites-enabled/$NGINX_SITE
rm -f /etc/nginx/sites-available/$NGINX_SITE
if [ ! -e /etc/nginx/sites-enabled/default ]; then
    log "Re-enabling default Nginx site..."
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
fi
nginx -t
systemctl restart nginx

# Remove application user and directory
log "Removing application user and directory..."
userdel -r $APP_USER || echo "User $APP_USER not found."

# Remove log directory
log "Removing log directory..."
rm -rf $LOG_DIR

# Update firewall
log "Updating firewall rules..."
ufw delete allow 'Nginx Full' || echo "Firewall rule for Nginx not found."

log "Undeployment completed successfully!"