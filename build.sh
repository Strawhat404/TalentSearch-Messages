#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories with proper permissions
mkdir -p /opt/render/project/src/staticfiles
mkdir -p /opt/render/project/src/media
chmod -R 755 /opt/render/project/src/staticfiles
chmod -R 755 /opt/render/project/src/media

# Debug: Show Django version and static files settings
python -c "import django; print(f'Django version: {django.get_version()}')"
python manage.py check --deploy

# Collect static files with verbose output
DJANGO_SETTINGS_MODULE=talentsearch.settings.prod python manage.py collectstatic --no-input --clear -v 2

# Run migrations
python manage.py migrate

# Create superuser if needed
python manage.py createsuperuser_if_not_exists

# Setup roles
python manage.py setup_roles

# Debug: List collected static files and their sizes
echo "Checking collected static files:"
ls -la /opt/render/project/src/staticfiles/admin/
echo "Total size of static files:"
du -sh /opt/render/project/src/staticfiles/
