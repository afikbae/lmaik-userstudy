#!/bin/bash

# Status script for LMAIK User Study application

# Configuration
APP_NAME="lmaik-userstudy"
SERVICE_NAME="lmaik-userstudy"
APP_URL="http://localhost"

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

# Check service status
check_service_status() {
    local service=$1
    local service_name=$2
    
    echo -e "${BLUE}=== $service_name Status ===${NC}"
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓ $service_name is running${NC}"
        systemctl status $service --no-pager -l | head -10
    else
        echo -e "${RED}✗ $service_name is not running${NC}"
        systemctl status $service --no-pager -l | head -10
    fi
    echo ""
}

# Check application response
check_application_response() {
    echo -e "${BLUE}=== Application Response ===${NC}"
    if curl -f -s $APP_URL > /dev/null; then
        echo -e "${GREEN}✓ Application is responding at $APP_URL${NC}"
        
        # Get response time
        local response_time=$(curl -w "%{time_total}" -s -o /dev/null $APP_URL)
        echo -e "Response time: ${response_time}s"
        
        # Get HTTP status
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL)
        echo -e "HTTP status: $http_status"
    else
        echo -e "${RED}✗ Application is not responding at $APP_URL${NC}"
    fi
    echo ""
}

# Check system resources
check_system_resources() {
    echo -e "${BLUE}=== System Resources ===${NC}"
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "CPU usage: ${cpu_usage}%"
    
    # Memory usage
    local memory_info=$(free -h | grep Mem)
    local total_mem=$(echo $memory_info | awk '{print $2}')
    local used_mem=$(echo $memory_info | awk '{print $3}')
    local free_mem=$(echo $memory_info | awk '{print $4}')
    echo -e "Memory: ${used_mem}/${total_mem} (${free_mem} free)"
    
    # Disk usage
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    local disk_available=$(df -h / | tail -1 | awk '{print $4}')
    echo -e "Disk usage: ${disk_usage} (${disk_available} available)"
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo -e "Load average: ${load_avg}"
    echo ""
}

# Check network connectivity
check_network() {
    echo -e "${BLUE}=== Network Information ===${NC}"
    
    # Get public IP
    local public_ip=$(curl -s ifconfig.me 2>/dev/null || echo "Unable to get public IP")
    echo -e "Public IP: $public_ip"
    
    # Get local IP
    local local_ip=$(hostname -I | awk '{print $1}')
    echo -e "Local IP: $local_ip"
    
    # Check port 80
    if netstat -tlnp 2>/dev/null | grep :80 > /dev/null; then
        echo -e "${GREEN}✓ Port 80 is listening${NC}"
    else
        echo -e "${RED}✗ Port 80 is not listening${NC}"
    fi
    
    # Check port 8000 (Gunicorn)
    if netstat -tlnp 2>/dev/null | grep :8000 > /dev/null; then
        echo -e "${GREEN}✓ Port 8000 (Gunicorn) is listening${NC}"
    else
        echo -e "${RED}✗ Port 8000 (Gunicorn) is not listening${NC}"
    fi
    echo ""
}

# Check recent logs
check_recent_logs() {
    echo -e "${BLUE}=== Recent Application Logs ===${NC}"
    local log_file="/var/log/$APP_NAME/error.log"
    
    if [ -f "$log_file" ]; then
        echo -e "Last 10 error log entries:"
        sudo tail -10 "$log_file" 2>/dev/null || echo "Unable to read log file"
    else
        echo "No error log file found"
    fi
    echo ""
}

# Check process information
check_processes() {
    echo -e "${BLUE}=== Process Information ===${NC}"
    
    # Gunicorn processes
    local gunicorn_count=$(pgrep -c gunicorn 2>/dev/null || echo "0")
    echo -e "Gunicorn processes: $gunicorn_count"
    
    # Nginx processes
    local nginx_count=$(pgrep -c nginx 2>/dev/null || echo "0")
    echo -e "Nginx processes: $nginx_count"
    
    # Python processes
    local python_count=$(pgrep -c python 2>/dev/null || echo "0")
    echo -e "Python processes: $python_count"
    echo ""
}

# Main status function
main() {
    echo "=== Status Report for $APP_NAME ==="
    echo "Time: $(date)"
    echo ""
    
    # Check all services
    check_service_status $SERVICE_NAME "Application Service"
    check_service_status nginx "Nginx"
    
    # Check application response
    check_application_response
    
    # Check system resources
    check_system_resources
    
    # Check network
    check_network
    
    # Check processes
    check_processes
    
    # Check recent logs
    check_recent_logs
    
    echo -e "${BLUE}=== Quick Commands ===${NC}"
    echo -e "View live logs: sudo journalctl -u $SERVICE_NAME -f"
    echo -e "Restart application: sudo systemctl restart $SERVICE_NAME"
    echo -e "Restart nginx: sudo systemctl restart nginx"
    echo -e "Check all services: sudo systemctl status $SERVICE_NAME nginx"
    echo ""
    
    # Overall status
    if systemctl is-active --quiet $SERVICE_NAME && systemctl is-active --quiet nginx && curl -f -s $APP_URL > /dev/null; then
        echo -e "${GREEN}✓ All systems operational${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some systems are not operational${NC}"
        exit 1
    fi
}

# Run main function
main "$@" 