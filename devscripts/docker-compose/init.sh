#!/usr/bin/env bash
docker-compose run interfaceserver python manage.py migrate --noinput
docker-compose run interfaceserver python manage.py collectstatic --noinput
docker-compose run interfaceserver python manage.py createsuperuser