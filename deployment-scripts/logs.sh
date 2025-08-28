#!/bin/bash

# Logs script for LMAIK User Study application

# Configuration
APP_NAME="lmaik-userstudy"
SERVICE_NAME="lmaik-userstudy"
LOG_DIR="/var/log/$APP_NAME"

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

# Show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  -a, --app          Show application logs (Gunicorn)"
    echo "  -n, --nginx        Show Nginx logs"
    echo "  -s, --system       Show systemd service logs"
    echo "  -e, --error        Show error logs only"
    echo "  -f, --follow       Follow logs in real-time"
    echo "  -l, --lines N      Show last N lines (default: 50)"
    echo "  -c, --clear        Clear all logs"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -a -f           # Follow application logs"
    echo "  $0 -n -l 100       # Show last 100 nginx log lines"
    echo "  $0 -s -e           # Show systemd error logs"
    echo "  $0 -c              # Clear all logs"
}

# Show application logs
show_app_logs() {
    local log_file="$LOG_DIR/error.log"
    local access_file="$LOG_DIR/access.log"
    
    echo -e "${BLUE}=== Application Logs ===${NC}"
    
    if [ -f "$log_file" ]; then
        echo -e "${GREEN}Error Log:${NC}"
        if [ "$FOLLOW" = true ]; then
            sudo tail -f "$log_file"
        else
            sudo tail -n "$LINES" "$log_file"
        fi
    else
        echo "No error log file found"
    fi
    
    if [ -f "$access_file" ]; then
        echo -e "${GREEN}Access Log:${NC}"
        if [ "$FOLLOW" = true ]; then
            sudo tail -f "$access_file"
        else
            sudo tail -n "$LINES" "$access_file"
        fi
    else
        echo "No access log file found"
    fi
}

# Show Nginx logs
show_nginx_logs() {
    echo -e "${BLUE}=== Nginx Logs ===${NC}"
    
    local error_log="/var/log/nginx/error.log"
    local access_log="/var/log/nginx/access.log"
    
    if [ -f "$error_log" ]; then
        echo -e "${GREEN}Nginx Error Log:${NC}"
        if [ "$FOLLOW" = true ]; then
            sudo tail -f "$error_log"
        else
            sudo tail -n "$LINES" "$error_log"
        fi
    else
        echo "No Nginx error log found"
    fi
    
    if [ -f "$access_log" ]; then
        echo -e "${GREEN}Nginx Access Log:${NC}"
        if [ "$FOLLOW" = true ]; then
            sudo tail -f "$access_log"
        else
            sudo tail -n "$LINES" "$access_log"
        fi
    else
        echo "No Nginx access log found"
    fi
}

# Show systemd service logs
show_system_logs() {
    echo -e "${BLUE}=== Systemd Service Logs ===${NC}"
    
    if [ "$FOLLOW" = true ]; then
        sudo journalctl -u $SERVICE_NAME -f
    else
        if [ "$ERROR_ONLY" = true ]; then
            sudo journalctl -u $SERVICE_NAME --no-pager -l | grep -i error | tail -n "$LINES"
        else
            sudo journalctl -u $SERVICE_NAME --no-pager -l | tail -n "$LINES"
        fi
    fi
}

# Clear logs
clear_logs() {
    echo -e "${BLUE}=== Clearing Logs ===${NC}"
    
    # Clear application logs
    if [ -d "$LOG_DIR" ]; then
        sudo rm -f "$LOG_DIR"/*.log
        log "Application logs cleared"
    fi
    
    # Clear Nginx logs
    sudo truncate -s 0 /var/log/nginx/error.log 2>/dev/null || true
    sudo truncate -s 0 /var/log/nginx/access.log 2>/dev/null || true
    log "Nginx logs cleared"
    
    # Clear systemd logs for the service
    sudo journalctl --vacuum-time=1s -u $SERVICE_NAME >/dev/null 2>&1 || true
    log "Systemd logs cleared"
    
    echo -e "${GREEN}All logs cleared successfully${NC}"
}

# Show log file sizes
show_log_sizes() {
    echo -e "${BLUE}=== Log File Sizes ===${NC}"
    
    # Application logs
    if [ -d "$LOG_DIR" ]; then
        echo "Application logs:"
        for log_file in "$LOG_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                local size=$(du -h "$log_file" | cut -f1)
                local name=$(basename "$log_file")
                echo "  $name: $size"
            fi
        done
    fi
    
    # Nginx logs
    echo "Nginx logs:"
    for log_file in /var/log/nginx/*.log; do
        if [ -f "$log_file" ]; then
            local size=$(du -h "$log_file" | cut -f1)
            local name=$(basename "$log_file")
            echo "  $name: $size"
        fi
    done
    
    # Systemd logs
    echo "Systemd logs:"
    local journal_size=$(sudo journalctl --disk-usage -u $SERVICE_NAME 2>/dev/null | grep -o '[0-9.]*[KMG]' || echo "Unknown")
    echo "  $SERVICE_NAME: $journal_size"
}

# Main function
main() {
    # Default values
    LINES=50
    FOLLOW=false
    ERROR_ONLY=false
    SHOW_APP=false
    SHOW_NGINX=false
    SHOW_SYSTEM=false
    CLEAR_LOGS=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--app)
                SHOW_APP=true
                shift
                ;;
            -n|--nginx)
                SHOW_NGINX=true
                shift
                ;;
            -s|--system)
                SHOW_SYSTEM=true
                shift
                ;;
            -e|--error)
                ERROR_ONLY=true
                shift
                ;;
            -f|--follow)
                FOLLOW=true
                shift
                ;;
            -l|--lines)
                LINES="$2"
                shift 2
                ;;
            -c|--clear)
                CLEAR_LOGS=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # If no specific log type is specified, show all
    if [ "$SHOW_APP" = false ] && [ "$SHOW_NGINX" = false ] && [ "$SHOW_SYSTEM" = false ] && [ "$CLEAR_LOGS" = false ]; then
        SHOW_APP=true
        SHOW_NGINX=true
        SHOW_SYSTEM=true
    fi
    
    # Clear logs if requested
    if [ "$CLEAR_LOGS" = true ]; then
        clear_logs
        exit 0
    fi
    
    # Show log sizes
    show_log_sizes
    echo ""
    
    # Show requested logs
    if [ "$SHOW_APP" = true ]; then
        show_app_logs
        echo ""
    fi
    
    if [ "$SHOW_NGINX" = true ]; then
        show_nginx_logs
        echo ""
    fi
    
    if [ "$SHOW_SYSTEM" = true ]; then
        show_system_logs
        echo ""
    fi
    
    # Show quick commands
    echo -e "${BLUE}=== Quick Commands ===${NC}"
    echo -e "Follow all logs: $0 -a -n -s -f"
    echo -e "Show errors only: $0 -e"
    echo -e "Show last 100 lines: $0 -l 100"
    echo -e "Clear all logs: $0 -c"
}

# Run main function
main "$@" 