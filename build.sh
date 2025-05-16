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

# Show migration status
echo "Current migration status:"
python manage.py showmigrations

# Run migrations with specific order
echo "Running migrations..."
# First, ensure authapp migrations are applied (since it contains the custom user model)
python manage.py migrate authapp
# Then run all other migrations
python manage.py migrate

# Debug: Check if superuser exists
echo "Checking for existing superusers:"
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superusers:', User.objects.filter(is_superuser=True).count())"

# Create superuser if needed
echo "Creating superuser if needed..."
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-"admin"}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-"admin@example.com"}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-"admin"}
python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true

# Setup roles
python manage.py setup_roles

# Debug: List collected static files and their sizes
echo "Checking collected static files:"
ls -la /opt/render/project/src/staticfiles/admin/
echo "Total size of static files:"
du -sh /opt/render/project/src/staticfiles/
