#!/bin/bash
# Exit on error
set -e

# Install dependencies
pip install -r requirements/prod.txt
pip install gunicorn

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
python manage.py createsuperuser_if_not_exists
python manage.py setup_roles
