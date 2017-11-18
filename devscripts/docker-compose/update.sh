#!/usr/bin/env bash
git pull
docker-compose build
docker-compose up -d
docker-compose run --rm interfaceserver python manage.py migrate --noinput
docker-compose run --rm interfaceserver python manage.py collectstatic --noinput
