#!/usr/bin/env bash

echo "installing requirements"
python3 -m pip3 install -r requirements.txt


echo "making migrations"
python3 manage.py makemigrations gaming --noinput

echo "migrating"
python3 manage.py migrate --noinput