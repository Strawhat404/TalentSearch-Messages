#!/bin/bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser_if_not_exists
