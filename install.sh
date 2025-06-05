#!/bin/bash

# Frontend Installation Script
# Production deployment for 172.28.69.200

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting Frontend installation..."
echo "=============================================================="

# Update system
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Node.js 18.x
print_status "Installing Node.js 18.x..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install Nginx
print_status "Installing Nginx..."
apt-get install -y nginx

# Verify Node.js installation
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
print_status "Node.js version: $NODE_VERSION"
print_status "NPM version: $NPM_VERSION"

# Create application directories
print_status "Creating application directories..."
mkdir -p /var/www/crop-frontend
mkdir -p /var/log/crop-frontend

# Install dependencies and build application
print_status "Installing dependencies..."
npm install

print_status "Building production application..."
npm run build

# Copy built files to web directory
print_status "Deploying application..."
cp -r dist/* /var/www/crop-frontend/
chown -R www-data:www-data /var/www/crop-frontend
chmod -R 755 /var/www/crop-frontend

# Configure Nginx
print_status "Configuring Nginx..."
cp nginx-production.conf /etc/nginx/sites-available/crop-frontend

# Enable site and disable default
ln -sf /etc/nginx/sites-available/crop-frontend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_status "Testing Nginx configuration..."
nginx -t

# Configure firewall
print_status "Configuring UFW firewall..."
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS (for future SSL)
ufw --force enable

# Configure logrotate
print_status "Configuring log rotation..."
cat > /etc/logrotate.d/crop-frontend << EOF
/var/log/nginx/crop-frontend.*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 \$(cat /var/run/nginx.pid)
        fi
    endscript
}
EOF

# Create update script
print_status "Creating update script..."
cat > /usr/local/bin/update-crop-frontend << 'EOF'
#!/bin/bash

# Frontend Update Script
set -e

REPO_DIR="/opt/crop-frontend-source"
WEB_DIR="/var/www/crop-frontend"

echo "Updating Crop Recommendation Frontend..."

# Backup current version
if [ -d "$WEB_DIR" ]; then
    cp -r "$WEB_DIR" "$WEB_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Build new version
cd "$REPO_DIR"
npm install
npm run build

# Deploy new version
rm -rf "$WEB_DIR"/*
cp -r dist/* "$WEB_DIR/"
chown -R www-data:www-data "$WEB_DIR"
chmod -R 755 "$WEB_DIR"

# Test deployment
if curl -s http://localhost/health > /dev/null; then
    echo "Frontend updated successfully!"
else
    echo "Warning: Health check failed after update"
fi
EOF

chmod +x /usr/local/bin/update-crop-frontend

# Create deployment directory for future updates
mkdir -p /opt/crop-frontend-source
cp -r . /opt/crop-frontend-source/
chown -R www-data:www-data /opt/crop-frontend-source

# Start and enable Nginx
print_status "Starting Nginx..."
systemctl enable nginx
systemctl restart nginx

# Wait for service to start
sleep 2

# Test the deployment
print_status "Testing frontend deployment..."
if curl -s http://localhost/health > /dev/null; then
    print_success "Frontend is accessible!"
else
    print_warning "Health check endpoint not responding"
fi

if curl -s http://localhost | grep -q "agri-ai-recommend"; then
    print_success "Frontend application loaded successfully!"
else
    print_warning "Frontend application may not be loading correctly"
fi

print_success "Frontend installation completed successfully!"
echo "=============================================================="
echo -e "${GREEN}Frontend URL:${NC}        http://172.28.69.200"
echo -e "${GREEN}Health Check:${NC}        http://172.28.69.200/health"
echo -e "${GREEN}API Backend:${NC}         http://172.28.69.96"
echo -e "${GREEN}Web Directory:${NC}       /var/www/crop-frontend"
echo -e "${GREEN}Source Directory:${NC}    /opt/crop-frontend-source"
echo ""
echo -e "${BLUE}Management:${NC}"
echo "  sudo systemctl start nginx"
echo "  sudo systemctl stop nginx"
echo "  sudo systemctl restart nginx"
echo "  sudo systemctl reload nginx"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  tail -f /var/log/nginx/crop-frontend.access.log"
echo "  tail -f /var/log/nginx/crop-frontend.error.log"
echo ""
echo -e "${BLUE}Updates:${NC}"
echo "  sudo /usr/local/bin/update-crop-frontend"
echo ""
echo -e "${YELLOW}Features:${NC}"
echo "  - React 18 + TypeScript"
echo "  - Real-time API integration"
echo "  - Manual prediction forms"
echo "  - CSV batch upload"
echo "  - Responsive design"
echo "  - Health monitoring"
echo "=============================================================="