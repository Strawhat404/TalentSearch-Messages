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

# Debug: Show database connection info (without sensitive data)
echo "Checking database connection..."
python manage.py shell -c "
from django.conf import settings
from django.db import connection
db_engine = settings.DATABASES['default']['ENGINE']
print(f'Database engine: {db_engine}')
print(f'Database name: {settings.DATABASES[\"default\"][\"NAME\"]}')
print(f'Database user: {settings.DATABASES[\"default\"][\"USER\"]}')
print(f'Database host: {settings.DATABASES[\"default\"][\"HOST\"]}')
"

# Show migration status before running migrations
echo "Migration status before running migrations:"
python manage.py showmigrations --list

# Debug: Check if we can connect to the database
echo "Testing database connection..."
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"

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

# Debug: Check database tables and their structure
echo "Checking database tables and structure:"
if [[ $DATABASE_URL == postgresql://* ]]; then
    python manage.py dbshell << EOF
    \dt
    \d authapp_user
    \d django_migrations
    SELECT app, name, applied FROM django_migrations ORDER BY id DESC LIMIT 10;
EOF
else
    python manage.py dbshell << EOF
    .tables
    .schema authapp_user
    .schema django_migrations
    SELECT app, name, applied FROM django_migrations ORDER BY id DESC LIMIT 10;
EOF
fi

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

# Final database check
echo "Final database check:"
if [[ $DATABASE_URL == postgresql://* ]]; then
    python manage.py dbshell << EOF
    \dt
    SELECT COUNT(*) FROM authapp_user;
    SELECT COUNT(*) FROM django_migrations;
EOF
else
    python manage.py dbshell << EOF
    .tables
    SELECT COUNT(*) FROM authapp_user;
    SELECT COUNT(*) FROM django_migrations;
EOF
fi