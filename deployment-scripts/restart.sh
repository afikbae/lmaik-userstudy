#!/bin/bash

# Restart script for LMAIK User Study application

# Configuration
APP_NAME="lmaik-userstudy"
SERVICE_NAME="lmaik-userstudy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        error "This script requires sudo privileges"
        echo "Please run: sudo $0"
        exit 1
    fi
}

# Restart application service
restart_application() {
    log "Restarting $SERVICE_NAME service..."
    if systemctl restart $SERVICE_NAME; then
        log "Service $SERVICE_NAME restarted successfully"
        return 0
    else
        error "Failed to restart $SERVICE_NAME service"
        return 1
    fi
}

# Restart nginx
restart_nginx() {
    log "Restarting nginx service..."
    if systemctl restart nginx; then
        log "Nginx restarted successfully"
        return 0
    else
        error "Failed to restart nginx"
        return 1
    fi
}

# Check service status
check_status() {
    log "Checking service status..."
    echo ""
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    systemctl status nginx --no-pager -l
}

# Wait for application to be ready
wait_for_ready() {
    log "Waiting for application to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost > /dev/null; then
            log "Application is ready!"
            return 0
        else
            echo -n "."
            sleep 2
            ((attempt++))
        fi
    done
    
    warn "Application may not be fully ready yet"
    return 1
}

# Main restart function
main() {
    echo "=== Restarting $APP_NAME ==="
    echo "Time: $(date)"
    echo ""
    
    # Check permissions
    check_permissions
    
    # Restart services
    if restart_application && restart_nginx; then
        log "All services restarted successfully"
    else
        error "Some services failed to restart"
        exit 1
    fi
    
    # Wait for application to be ready
    wait_for_ready
    
    # Show status
    check_status
    
    echo ""
    log "Restart completed successfully!"
    echo -e "${BLUE}Application should be available at: http://$(curl -s ifconfig.me)${NC}"
}

# Run main function
main "$@" 