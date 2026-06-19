#!/usr/bin/env bash

set -e  # stoppe si une commande échoue

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_admin