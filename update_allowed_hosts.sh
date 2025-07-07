#!/bin/bash

# Script to update ALLOWED_HOSTS environment variable on VPS
# This script helps you set the ALLOWED_HOSTS environment variable for your Django application

echo "=== Django ALLOWED_HOSTS Configuration Helper ==="
echo ""

# Check if we're in the project directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from your Django project root directory"
    exit 1
fi

echo "Current ALLOWED_HOSTS configuration:"
echo "-----------------------------------"

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📁 Found .env file"
    if grep -q "ALLOWED_HOSTS" .env; then
        echo "Current ALLOWED_HOSTS in .env:"
        grep "ALLOWED_HOSTS" .env
    else
        echo "No ALLOWED_HOSTS found in .env file"
    fi
else
    echo "📁 No .env file found"
fi

echo ""
echo "Recommended ALLOWED_HOSTS for your setup:"
echo "talentsearch-messages-1.onrender.com,localhost,127.0.0.1,.onrender.com,www.saphor.net,saphor.net,.saphor.net"
echo ""

# Ask user if they want to update .env file
read -p "Do you want to create/update .env file with the recommended ALLOWED_HOSTS? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create or update .env file
    if [ ! -f ".env" ]; then
        echo "Creating new .env file..."
        touch .env
    fi
    
    # Remove existing ALLOWED_HOSTS line if it exists
    if grep -q "ALLOWED_HOSTS" .env; then
        sed -i '/ALLOWED_HOSTS/d' .env
        echo "Removed existing ALLOWED_HOSTS from .env"
    fi
    
    # Add new ALLOWED_HOSTS
    echo "ALLOWED_HOSTS=talentsearch-messages-1.onrender.com,localhost,127.0.0.1,.onrender.com,www.saphor.net,saphor.net,.saphor.net" >> .env
    echo "✅ Added ALLOWED_HOSTS to .env file"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Restart your Django application"
    echo "2. If using systemd, run: sudo systemctl restart your-app-name"
    echo "3. If using gunicorn directly, restart the process"
    echo "4. Test your admin login again"
else
    echo "No changes made. You can manually set ALLOWED_HOSTS in your environment or .env file."
fi

echo ""
echo "=== Configuration Complete ===" 