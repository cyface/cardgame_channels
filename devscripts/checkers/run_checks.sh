#!/usr/bin/env bash
. .env/bin/activate
python manage.py jenkins --coverage-rcfile=devscripts/checkers/coveragerc cardgame_channels
python manage.py pylint --pylint-rcfile=devscripts/checkers/pylintrc cardgame_channels