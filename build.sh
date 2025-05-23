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

# Make sure you're in the correct directory
cd /opt/render/project/src

# Activate the virtual environment
source .venv/bin/activate

# Force database connection and migrations with error handling
echo "Running migrations with error handling..."
if ! python manage.py migrate auth --noinput; then
    echo "Error: Auth migrations failed"
    exit 1
fi

if ! python manage.py migrate contenttypes --noinput; then
    echo "Error: Contenttypes migrations failed"
    exit 1
fi

if ! python manage.py migrate authapp --noinput; then
    echo "Error: Authapp migrations failed"
    exit 1
fi

if ! python manage.py migrate --noinput; then
    echo "Error: General migrations failed"
    exit 1
fi

# Verify migrations after running them
echo "Migration status after running migrations:"
python manage.py showmigrations --list

# Create superuser if none exists
echo "Creating superuser if needed..."
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-"admin@example.com}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-"Test1234!"}
DJANGO_SUPERUSER_NAME=${DJANGO_SUPERUSER_NAME:-"Admin User"}

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        name='$DJANGO_SUPERUSER_NAME'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
