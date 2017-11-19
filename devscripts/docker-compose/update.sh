#!/usr/bin/env bash
eval "$(docker-machine env default)"
git pull
docker-compose up -d --force-recreate --build
docker-compose run --rm interfaceserver python manage.py migrate --noinput
docker-compose run --rm interfaceserver python manage.py collectstatic --noinput
