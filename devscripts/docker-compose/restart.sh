#!/usr/bin/env bash
eval "$(docker-machine env default)"
docker-compose stop
sleep 1s
docker-compose up -d