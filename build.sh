#!/usr/bin/env bash
echo "BUILD START"
python3.11 -m venv venv
source venv/bin/activate

echo "installing requirements"
python3 -m pip install -r requirements.txt


echo "making migrations"
python3 manage.py makemigrations gaming --noinput

echo "migrating"
python3 manage.py migrate --noinput