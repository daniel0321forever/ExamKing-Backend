#!/usr/bin/env bash
echo "installing requirements..."
python3 -m pip install -r requirements.txt


echo "making migrations..."
python3 manage.py makemigrations gaming --noinput

echo "migrating..."
python3 manage.py migrate --noinput

echo "deploying..."
daphne -b 0.0.0.0 -p 8000 testing_game.asgi:application