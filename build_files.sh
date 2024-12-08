#!/usr/bin/env bash
apt install libsqlite3-dev

echo "installing requirements"
python3 -m pip install -r requirements.txt


echo "making migrations"
python3 manage.py makemigrations gaming --noinput

echo "migrating"
python3 manage.py migrate --noinput