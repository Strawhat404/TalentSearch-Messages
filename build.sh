#!/bin/bash
# Exit on error
set -e

echo "Starting build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements/prod.txt
pip install gunicorn

# Show Python version
echo "Python version:"
python --version

# Show installed packages
echo "Installed packages:"
pip list

# Show Django version
echo "Django version:"
python -c "import django; print(django.get_version())"

# Show current directory
echo "Current directory:"
pwd

# List files in current directory
echo "Files in current directory:"
ls -la

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if not exists
echo "Setting up superuser..."
python manage.py createsuperuser_if_not_exists

# Setup roles
echo "Setting up roles..."
python manage.py setup_roles

# Show environment variables (excluding sensitive ones)
echo "Environment variables:"
env | grep -v "SECRET\|PASSWORD\|KEY" | sort

# Test Django setup
echo "Testing Django setup..."
python manage.py check

echo "Build completed successfully!"
