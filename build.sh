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

# Show migration status before running migrations
echo "Migration status before running migrations:"
python manage.py showmigrations --list

# Reset database if needed (uncomment if you want to start fresh)
# echo "Dropping all tables..."
# python manage.py dbshell << EOF
# DROP SCHEMA public CASCADE;
# CREATE SCHEMA public;
# GRANT ALL ON SCHEMA public TO postgres;
# GRANT ALL ON SCHEMA public TO public;
# EOF

# Run migrations with specific order and verbose output
echo "Running migrations..."
echo "1. Running authapp migrations first..."
python manage.py migrate authapp --verbosity 2
echo "2. Running contenttypes migrations..."
python manage.py migrate contenttypes --verbosity 2
echo "3. Running auth migrations..."
python manage.py migrate auth --verbosity 2
echo "4. Running admin migrations..."
python manage.py migrate admin --verbosity 2
echo "5. Running all other migrations..."
python manage.py migrate --verbosity 2

# Show migration status after running migrations
echo "Migration status after running migrations:"
python manage.py showmigrations --list

# Debug: Check if superuser exists
echo "Checking for existing superusers:"
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superusers:', User.objects.filter(is_superuser=True).count())"

# Create superuser if needed
echo "Creating superuser if needed..."
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-"abel"}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-"admin@gmail.com"}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-"abel1234"}
python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true

# Setup roles
python manage.py setup_roles

# Debug: List collected static files and their sizes
echo "Checking collected static files:"
ls -la /opt/render/project/src/staticfiles/admin/
echo "Total size of static files:"
du -sh /opt/render/project/src/staticfiles/

# Debug: Show database tables
echo "Checking database tables:"
python manage.py dbshell << EOF
\dt
SELECT * FROM django_migrations ORDER BY id DESC LIMIT 10;
EOF
