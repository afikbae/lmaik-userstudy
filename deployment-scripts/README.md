# Riskoloji Analiz - Deployment Scripts

This directory contains deployment and management scripts for the Riskoloji Analiz Flask application.

## Scripts Overview

### 1. `deploy.sh` - Main Deployment Script
**Purpose**: Complete setup of the application on a fresh EC2 instance.

**Usage**:
```bash
# Run from the application directory
sudo ./deployment-scripts/deploy.sh
```

**What it does**:
- Installs system dependencies (Python, Nginx, scientific libraries)
- Creates application user and directories
- Sets up Python virtual environment
- Installs Python dependencies from `requirements.txt`
- Configures Flask application to run directly
- Sets up Nginx reverse proxy
- Creates systemd service for auto-start
- Configures firewall
- Installs management scripts
- Tests the deployment

### 2. `status.sh` - Status Report
**Purpose**: Detailed status report of all services and system resources.

**Usage**:
```bash
# Run status check
sudo /opt/riskoloji-analiz/status.sh

# Or from deployment directory
sudo ./deployment-scripts/status.sh
```

**What it shows**:
- Service status (Application, Nginx)
- Application response time and HTTP status
- System resources (CPU, Memory, Disk, Load)
- Network information (IP addresses, ports)
- Process counts
- Recent logs
- Quick management commands

### 3. `restart.sh` - Service Restart
**Purpose**: Restart application and related services.

**Usage**:
```bash
# Restart services
sudo /opt/riskoloji-analiz/restart.sh

# Or from deployment directory
sudo ./deployment-scripts/restart.sh
```

**What it does**:
- Restarts application service
- Restarts Nginx
- Waits for services to be ready
- Shows service status
- Displays access information

### 4. `logs.sh` - Log Management
**Purpose**: View and manage application logs.

**Usage**:
```bash
# View logs
sudo /opt/riskoloji-analiz/logs.sh

# Or from deployment directory
sudo ./deployment-scripts/logs.sh
```

**What it shows**:
- Application logs (access and error)
- Nginx logs
- Systemd service logs
- Real-time log monitoring
- Log rotation information

## Architecture

The application uses a simple but robust architecture:

```
Internet → Nginx (Port 80) → Flask App (Port 8000)
```

### Components:
- **Nginx**: Reverse proxy and static file server
- **Flask**: Python web application running directly
- **Systemd**: Service management and auto-restart
- **Python Virtual Environment**: Isolated dependencies

### Key Features:
- **Direct Flask Execution**: No WSGI server needed, Flask runs directly
- **Auto-restart**: Services automatically restart on failure
- **Log Management**: Comprehensive logging to files
- **Static File Serving**: Nginx serves static files efficiently
- **Process Management**: Systemd manages the Flask process

## Deployment Process

### Prerequisites
- Ubuntu/Debian system
- Sudo privileges
- Internet connection for package installation

### Quick Deployment
1. Clone or copy the application to the server
2. Navigate to the application directory
3. Run the deployment script:
   ```bash
   sudo ./deployment-scripts/deploy.sh
   ```

### What Gets Installed
- **System Packages**: Python 3, Nginx, scientific libraries
- **Python Dependencies**: All packages from `requirements.txt`
- **Application**: Copied to `/opt/riskoloji-analiz/`
- **User**: `riskoloji` user created for security
- **Services**: Systemd services for auto-start
- **Firewall**: UFW configured for web access

## Management Commands

### 1. Status Monitoring
```bash
# Check overall status
sudo /opt/riskoloji-analiz/status.sh

# View logs
sudo /opt/riskoloji-analiz/logs.sh
```

### 2. Service Management
```bash
# Restart application
sudo /opt/riskoloji-analiz/restart.sh

# Manual service control
sudo systemctl restart riskoloji-analiz
sudo systemctl restart nginx
```

### 3. Manual Updates
To update the application manually:

1. **Backup current version**:
   ```bash
   sudo cp -r /opt/riskoloji-analiz /opt/riskoloji-analiz.backup.$(date +%Y%m%d)
   ```

2. **Copy new files**:
   ```bash
   sudo cp -r /path/to/new/version/* /opt/riskoloji-analiz/
   sudo chown -R riskoloji:riskoloji /opt/riskoloji-analiz/
   ```

3. **Update dependencies** (if requirements.txt changed):
   ```bash
   sudo -u riskoloji /opt/riskoloji-analiz/venv/bin/pip install -r /opt/riskoloji-analiz/requirements.txt
   ```

4. **Restart services**:
   ```bash
   sudo /opt/riskoloji-analiz/restart.sh
   ```

## Troubleshooting

### Common Issues

#### 1. Application Not Starting
```bash
# Check service status
sudo systemctl status riskoloji-analiz

# View logs
sudo journalctl -u riskoloji-analiz -f
```

#### 2. Nginx Issues
```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx
```

#### 3. Permission Issues
```bash
# Fix ownership
sudo chown -R riskoloji:riskoloji /opt/riskoloji-analiz/

# Fix permissions
sudo chmod 755 /opt/riskoloji-analiz/uploads/
```

#### 4. Port Conflicts
```bash
# Check what's using port 8000
sudo netstat -tlnp | grep :8000

# Check what's using port 80
sudo netstat -tlnp | grep :80
```

### Log Locations
- **Application Logs**: `/var/log/riskoloji-analiz/`
- **Nginx Logs**: `/var/log/nginx/`
- **Systemd Logs**: `sudo journalctl -u riskoloji-analiz`

## Security Considerations

### Firewall
- Only ports 80 (HTTP) and 22 (SSH) are open
- Nginx handles all external connections
- Flask app only listens on localhost (127.0.0.1)

### User Permissions
- Application runs as dedicated `riskoloji` user
- Minimal file permissions
- No root access for application

### File Uploads
- Maximum file size: 16MB
- Uploads stored in isolated directory
- Files served through Nginx with internal directive

## Performance Optimization

### Flask Configuration
- Debug mode disabled in production
- Threaded mode enabled for concurrent requests
- Proper logging configuration

### Nginx Configuration
- Static file caching (30 days)
- Gzip compression
- Proxy buffering for large requests
- Connection timeouts configured

### System Resources
- Monitor with `status.sh` script
- Check disk space regularly
- Monitor memory usage

## Backup and Recovery

### Application Backup
```bash
# Create backup
sudo cp -r /opt/riskoloji-analiz /opt/riskoloji-analiz.backup.$(date +%Y%m%d)

# Restore from backup
sudo systemctl stop riskoloji-analiz
sudo rm -rf /opt/riskoloji-analiz
sudo cp -r /opt/riskoloji-analiz.backup.YYYYMMDD /opt/riskoloji-analiz
sudo chown -R riskoloji:riskoloji /opt/riskoloji-analiz
sudo systemctl start riskoloji-analiz
```

### Data Backup
- Upload directory: `/opt/riskoloji-analiz/uploads/`
- Logs: `/var/log/riskoloji-analiz/`
- Configuration: `/etc/systemd/system/riskoloji-analiz.service`

## Support

For issues or questions:
1. Check the logs first: `sudo /opt/riskoloji-analiz/logs.sh`
2. Verify service status: `sudo /opt/riskoloji-analiz/status.sh`
3. Review this documentation
4. Check system resources and permissions 