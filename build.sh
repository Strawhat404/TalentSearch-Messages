#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

# Debug: Show Django version and static files settings
python -c "import django; print(f'Django version: {django.get_version()}')"
python manage.py check --deploy

# Collect static files with verbose output
python manage.py collectstatic --no-input --clear -v 2

# Run migrations
python manage.py migrate

# Create superuser if needed
python manage.py createsuperuser_if_not_exists

# Setup roles
python manage.py setup_roles

# Debug: List collected static files
echo "Checking collected static files:"
ls -la staticfiles/admin/
