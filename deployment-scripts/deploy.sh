#!/bin/bash

# LMAIK User Study - EC2 Deployment Script
# Complete setup for Flask application with Nginx

set -e  # Exit on any error

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
    exit 1
}

# Configuration
APP_NAME="lmaik-userstudy"
APP_USER="lmaik"
APP_DIR="/opt/$APP_NAME"
VENV_DIR="/opt/$APP_NAME/venv"
SERVICE_NAME="lmaik-userstudy"
NGINX_SITE="lmaik-userstudy"

log "Starting deployment of $APP_NAME..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Update system packages
log "Updating system packages..."
sudo apt-get update -y

# Install essential system dependencies
log "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    nginx \
    git \
    curl \
    wget \
    unzip \
    libffi-dev \
    libssl-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    libhdf5-dev \
    libnetcdf-dev \
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libgdal-dev \
    gdal-bin

# Create application user
log "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d $APP_DIR $APP_USER
    log "Created user: $APP_USER"
else
    log "User $APP_USER already exists"
fi

# Create application directory
log "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Copy application files
log "Copying application files..."
if [ -f "app.py" ] && [ -f "requirements.txt" ]; then
    sudo cp -r . $APP_DIR/
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
    log "Application files copied successfully"
else
    error "Please run this script from the application directory (must contain app.py and requirements.txt)"
fi

# Create virtual environment
log "Creating Python virtual environment..."
sudo -u $APP_USER python3 -m venv $VENV_DIR

# Install Python dependencies
log "Installing Python dependencies..."
sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip setuptools wheel
sudo -u $APP_USER $VENV_DIR/bin/pip install -r $APP_DIR/requirements.txt

# Create uploads directory
log "Creating uploads directory..."
sudo -u $APP_USER mkdir -p $APP_DIR/uploads
sudo chmod 755 $APP_DIR/uploads

# Create log directory
log "Creating log directory..."
sudo mkdir -p /var/log/$APP_NAME
sudo chown $APP_USER:$APP_USER /var/log/$APP_NAME

# Create Flask startup script
log "Creating Flask startup script..."
sudo tee $APP_DIR/start_flask.py > /dev/null <<EOF
#!/usr/bin/env python3
"""
Flask startup script for production
"""
import os
import sys

# Add the application directory to Python path
sys.path.insert(0, '/opt/lmaik-userstudy')

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=False, threaded=True)
EOF

# Make the startup script executable
sudo chmod +x $APP_DIR/start_flask.py

# Create systemd service file
log "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=LMAIK User Study Flask Application
After=network.target

[Service]
Type=simple
User=lmaik
Group=lmaik
WorkingDirectory=/opt/lmaik-userstudy
Environment=PATH=/opt/lmaik-userstudy/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=0
ExecStart=/opt/lmaik-userstudy/venv/bin/python start_flask.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=append:/var/log/lmaik-userstudy/access.log
StandardError=append:/var/log/lmaik-userstudy/error.log

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
log "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null <<EOF
server {
    listen 80;
    server_name userstudy.afikbae.com;

    # Allow very large uploads (0 disables size checking in Nginx)
    client_max_body_size 0;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias /opt/lmaik-userstudy/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /opt/lmaik-userstudy/uploads/;
        internal;
    }
}
EOF

# Enable Nginx site
log "Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
log "Testing Nginx configuration..."
sudo nginx -t

# Enable and start services
log "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl enable nginx
sudo systemctl restart nginx

# Configure firewall
log "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# Copy management scripts to application directory
log "Installing management scripts..."
sudo cp deployment-scripts/restart.sh $APP_DIR/
sudo cp deployment-scripts/status.sh $APP_DIR/
sudo cp deployment-scripts/logs.sh $APP_DIR/

# Make scripts executable
sudo chmod +x $APP_DIR/*.sh
sudo chown lmaik:lmaik $APP_DIR/*.sh

# Test the application
log "Testing application..."
sleep 5
if curl -f -s http://localhost > /dev/null; then
    log "Application is running successfully!"
else
    warn "Application might not be fully started yet. Please check logs:"
    warn "sudo journalctl -u $SERVICE_NAME -f"
fi

# Display final information
log "Deployment completed successfully!"
echo ""
echo -e "${BLUE}=== Deployment Summary ===${NC}"
echo -e "Application: $APP_NAME"
echo -e "Installation directory: $APP_DIR"
echo -e "Virtual environment: $VENV_DIR"
echo -e "Service name: $SERVICE_NAME"
echo -e "Nginx site: $NGINX_SITE"
echo ""
echo -e "${BLUE}=== Management Commands ===${NC}"
echo -e "Check service status: $APP_DIR/status.sh"
echo -e "View application logs: $APP_DIR/logs.sh"
echo -e "Restart application: $APP_DIR/restart.sh"
echo ""
echo -e "${BLUE}=== Access Information ===${NC}"
echo -e "Local access: http://localhost"
echo -e "Public access: http://$(curl -s ifconfig.me)"
echo ""
echo -e "${GREEN}The application is now running and will start automatically on boot!${NC}"
echo -e "${GREEN}All services are configured for auto-restart on failure.${NC}" 