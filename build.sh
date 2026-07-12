#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Change into Django project directory
cd cineverse

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
