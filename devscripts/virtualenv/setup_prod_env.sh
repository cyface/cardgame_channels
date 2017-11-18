#!/usr/bin/env bash
# You must have virtualenv installed, and the virtualenv command in your path for this to work.
# Assuming you have python installed, you can install virtualenv using the command below.
# curl -O https://raw.github.com/pypa/virtualenv/master/virtualenv.py
# This should be run from the project directory, not inside the socialprofile dir

virtualenv .virtualenv
. ./.virtualenv/bin/activate
pip install --use-wheel -r requirements_prod.txt
