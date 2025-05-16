#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

# Collect static files
python manage.py collectstatic --no-input --clear

# Run migrations
python manage.py migrate

# Create superuser if needed
python manage.py createsuperuser_if_not_exists

# Setup roles
python manage.py setup_roles
