#!/usr/bin/env bash
# exit on error
set -o errexit

# Create and activate a virtual environment
echo "Creating virtual environment..."
python -m venv .venv
source .venv/bin/activate

# Upgrade pip (to avoid pip upgrade notice)
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies (including daphne if it's in requirements.txt)
echo "Installing dependencies (including daphne) from requirements.txt..."
pip install -r requirements.txt

# (Optional) Explicitly install daphne if it's not in requirements.txt
# echo "Explicitly installing daphne (if not in requirements.txt)..."
# pip install daphne

# Debug: verify that daphne is installed in the venv
echo "Verifying daphne installation (in venv)..."
ls -l .venv/bin/daphne

# Create necessary directories (for static files and media) with proper permissions
echo "Creating static and media directories..."
mkdir -p /opt/render/project/src/staticfiles
mkdir -p /opt/render/project/src/media
chmod -R 755 /opt/render/project/src/staticfiles
chmod -R 755 /opt/render/project/src/media

# Debug: Show Django version and static files settings
echo "Checking Django setup..."
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

python manage.py migrate news 0002_initial --fake || python manage.py migrate news 0001_initial --fake
python manage.py migrate --fake-initial

# Verify migrations after running them
echo "Migration status after running migrations:"
python manage.py showmigrations --list

# Create superuser if none exists
echo "Creating superuser if needed..."
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-"admin@example.com"}
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

# Create a wrapper start script (start.sh) that activates the venv and then runs daphne
echo "Creating wrapper start script (start.sh) to activate venv and run daphne..."
cat > /opt/render/project/src/start.sh << 'EOF'
#!/usr/bin/env bash
set -e
echo "Activating virtual environment..."
source /opt/render/project/src/.venv/bin/activate
echo "Starting daphne (from venv) ..."
EOF

# Make start.sh executable
chmod +x /opt/render/project/src/start.sh

# Debug: verify start.sh exists and is executable
echo "Verifying start.sh (wrapper script) ..."
ls -l /opt/render/project/src/start.sh

gunicorn talentsearch.wsgi:application --bind 0.0.0.0:$PORT
