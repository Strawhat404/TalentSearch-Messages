#!/usr/bin/env bash
# exit on error
set -o errexit

# Set the project directory
cd /opt/render/project/src

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create static directories
mkdir -p staticfiles
mkdir -p static
chmod -R 755 staticfiles
chmod -R 755 static

# Run migrations
python manage.py makemigrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Ensure daphne is installed and working
pip install daphne
echo "Daphne version:"
.venv/bin/daphne --version

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
